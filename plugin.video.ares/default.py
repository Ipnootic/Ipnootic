# -*- coding: utf-8 -*-
import sys, urllib.parse as urlparse, json
import xbmcplugin, xbmcaddon, xbmcgui
from resources.lib.core.menus import load_menu
from resources.lib.core.aggregator import aggregate_sources
from resources.lib.core.ranker import rank_sources
from resources.lib.core.playback import resolve_and_play
from resources.lib.trakt import client as trakt
from resources.lib.utils.store import nextup_list
from resources.lib.utils.store import nextup_list
from resources.lib.utils.settings import get_str, get_bool

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])

def build_url(q):
    return sys.argv[0] + '?' + urlparse.urlencode(q)

def list_nextup_trakt():
    items = trakt.next_up(limit=int(ADDON.getSettingInt('nextup_limit') or 20))
    if not items:
        xbmcplugin.addDirectoryItem(HANDLE, build_url({}), xbmcplugin.ListItem(label="Sem itens em Next Up (Trakt)"), isFolder=False)
        xbmcplugin.endOfDirectory(HANDLE); return
    for e in items:
        s = int(e.get('season',1)); ep = int(e.get('episode',1))
        label = f"{e.get('title')} S{str(s).zfill(2)}E{str(ep).zfill(2)}"
        qs = {"action":"aggregate","kind":"episode","title":e.get('title'),"season":str(s),"episode":str(ep)}
        xbmcplugin.addDirectoryItem(HANDLE, build_url(qs), xbmcplugin.ListItem(label=label), isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)

def list_nextup():
    items = nextup_list(limit=int(ADDON.getSettingInt('nextup_limit') or 20))
    if not items:
        li = xbmcplugin.ListItem(label="Sem itens em Next Up")
        xbmcplugin.addDirectoryItem(HANDLE, build_url({}), li, isFolder=False)
        xbmcplugin.endOfDirectory(HANDLE); return
    for e in items:
        s = int(e.get('season',1)); ep = int(e.get('episode',1)) + 1
        label = f"{e.get('title')} S{str(s).zfill(2)}E{str(ep).zfill(2)}"
        qs = {"action":"aggregate","kind":"episode","title":e.get('title'),"season":str(s),"episode":str(ep)}
        li = xbmcplugin.ListItem(label=label)
        xbmcplugin.addDirectoryItem(HANDLE, build_url(qs), li, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)

def list_root():
    for item in load_menu():
        li = xbmcplugin.ListItem(label=item['label'])
        li.setArt({'icon': 'DefaultFolder.png'})
        xbmcplugin.addDirectoryItem(HANDLE, build_url(item['route']), li, isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)

def list_section(kind):
    hide = ADDON.getSettingBool('hide_watched')
    watched_eps = set(); watched_movies_ids = set()
    if ADDON.getSettingBool('trakt_enabled') and ADDON.getSettingString('trakt_access_token'):
        try:
            watched_eps = set(trakt.watched_episodes())
            watched_movies_ids = set(trakt.watched_movies())
        except Exception:
            pass
    samples = []
    if kind == 'movie':
        samples = [("Inception (2010)", {"action":"aggregate","kind":"movie","title":"Inception","year":"2010","tmdb_id":"27205"})]
    elif kind == 'show':
        samples = [("Breaking Bad S01E01", {"action":"aggregate","kind":"episode","title":"Breaking Bad","season":"1","episode":"1"})]
    elif kind == 'anime':
        samples = [("Attack on Titan S01E01", {"action":"aggregate","kind":"episode","title":"Attack on Titan","season":"1","episode":"1"})]
    for label, qs in samples:
        if hide and qs.get('kind')=='movie' and ('movie', int(qs.get('tmdb_id','0') or 0)) in watched_movies_ids:
            continue
        if hide and qs.get('kind')=='episode' and (qs.get('title'), int(qs.get('season','1')), int(qs.get('episode','1'))) in watched_eps:
            continue
        xbmcplugin.addDirectoryItem(HANDLE, build_url(qs), xbmcplugin.ListItem(label=label), isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)

    # Minimal demo entries — replace with TMDb/Trakt discovery
    samples = []
    if kind == 'movie':
        samples = [("Inception (2010)", {"action":"aggregate","kind":"movie","title":"Inception","year":"2010"})]
    elif kind == 'show':
        samples = [("Breaking Bad S01E01", {"action":"aggregate","kind":"episode","title":"Breaking Bad","season":"1","episode":"1"})]
    elif kind == 'anime':
        samples = [("Attack on Titan S01E01", {"action":"aggregate","kind":"episode","title":"Attack on Titan","season":"1","episode":"1"})]
    for label, qs in samples:
        li = xbmcplugin.ListItem(label=label); li.setArt({'icon':'DefaultVideo.png'})
        xbmcplugin.addDirectoryItem(HANDLE, build_url(qs), li, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)

def do_search():
    kb = xbmcgui.Dialog().input("Pesquisar título", type=xbmcgui.INPUT_ALPHANUM)
    if not kb: return
    qs = {"action":"aggregate","kind":"movie","title":kb}
    xbmc.executebuiltin(f'Container.Update({build_url(qs)})')

def aggregate_route(params):
    query = dict(params)
    # inject preferences from settings
    prefer_map = ["2160p","1080p","720p","Any"]
    query['prefer_quality'] = prefer_map[int(ADDON.getSettingInt('prefer_quality'))]
    query['exclude'] = get_str('filters_exclude','')
    sources = aggregate_sources(query)
    ranked = rank_sources(sources, query)
    auto = get_bool('auto_play_best')
    for src in ranked:
        label = f"[{src.get('provider','?')}] {src.get('quality','?')} • {src.get('size_gb','?')}GB • {src.get('title','')}"
        li = xbmcplugin.ListItem(label=label)
        li.setInfo('video', {'title': src.get('title','')})
        art = _art_for(src.get('title'), query.get('kind','movie'))
        if art: li.setArt(art)
        url = build_url({"action":"play","src": json.dumps(src)})
        xbmcplugin.addDirectoryItem(HANDLE, url, li, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)
    if auto and ranked:
        xbmc.executebuiltin(f'RunPlugin({build_url({"action":"play","src": json.dumps(ranked[0])})})')

def open_settings():
    ADDON.openSettings(); xbmcplugin.endOfDirectory(HANDLE)

def play(params):
    src = json.loads(params['src'])
    resolve_and_play(src, HANDLE)

def router(paramstring):
    params = dict(urlparse.parse_qsl(paramstring))
    action = params.get("action")
    if action is None:
        list_root()
elif action == "nextup":
    if ADDON.getSettingBool('trakt_enabled') and ADDON.getSettingString('trakt_access_token'):
        list_nextup_trakt()
    else:
        list_nextup()
    elif action == "anime_menu":
        list_anime()
    elif action == "section":
        list_section(params.get("type"))
    elif action == "search":
        do_search()
    elif action == "aggregate":
        aggregate_route(params)
    elif action == "open_settings":
        open_settings()
    elif action == "trakt_auth":
        trakt_auth()
    elif action == "anime_list":
        src = params.get('src')
        items = anilist.trending() if src=='trending' else anilist.current_season()
        for e in items:
            label = f"{e.get('title')}"
            qs = {"action":"aggregate","kind":"episode","title":e.get('title'),"season":"1","episode":"1"}
            xbmcplugin.addDirectoryItem(HANDLE, build_url(qs), xbmcplugin.ListItem(label=label), isFolder=False)
        xbmcplugin.endOfDirectory(HANDLE)
    elif action == "play":
        play(params)
    else:
        list_root()

if __name__ == '__main__':
    router(sys.argv[2][1:])

def trakt_auth():
    try:
        dc = trakt.device_code()
        dlg = xbmcgui.Dialog()
        dlg.ok("Trakt", f"Código: [B]{dc.get('user_code')}[/B]\nAcede a {dc.get('verification_url')} e introduz o código.")
        trakt.poll_for_token(dc.get('device_code'), interval=dc.get('interval',5), expires_in=dc.get('expires_in',600))
        xbmcgui.Dialog().notification("Trakt", "Autorizado com sucesso", xbmcgui.NOTIFICATION_INFO, 3000)
    except Exception as e:
        xbmcgui.Dialog().notification("Trakt", "Falha na autorização", xbmcgui.NOTIFICATION_ERROR, 4000)


def list_anime():
    # Simple two folders: Trending / Current season
    items = [("Trending (AniList)", {"action":"anime_list","src":"trending"}),
             ("Temporada atual (AniList)", {"action":"anime_list","src":"season"})]
    for label, qs in items:
        li = xbmcplugin.ListItem(label=label)
        xbmcplugin.addDirectoryItem(HANDLE, build_url(qs), li, isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)

def _art_for(title, kind='movie'):
    try:
        if not ADDON.getSettingBool('use_artwork'):
            return {}
        res = tmdb_meta.find_show(title) if kind!='movie' else None
        if kind=='movie':
            # quick movie search
            pass
        # Reuse show poster as generic
        if res and res.get('poster_path'):
            base = "https://image.tmdb.org/t/p/"
            return {'poster': base + "w342" + res['poster_path'], 'fanart': base + "w780" + (res.get('backdrop_path') or res['poster_path'])}
    except Exception:
        pass
    return {}
