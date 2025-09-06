import json, time, urllib.request, urllib.parse
from ..utils.settings import get_str
from xbmcaddon import Addon
import xbmc

ADDON = Addon()
BASE = "https://api.trakt.tv"
OAUTH = "https://api.trakt.tv/oauth"

def _headers(authed=False):
    h = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": ADDON.getSettingString('trakt_client_id')
    }
    if authed and ADDON.getSettingString('trakt_access_token'):
        h["Authorization"] = "Bearer " + ADDON.getSettingString('trakt_access_token')
    return h

def _req(url, data=None, headers=None, method=None):
    if headers is None: headers = _headers()
    if data is not None and not isinstance(data, (bytes, bytearray)):
        data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method=method or ("POST" if data else "GET"))
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read().decode('utf-8')
        try: return json.loads(raw)
        except: return raw

def device_code():
    cid = ADDON.getSettingString('trakt_client_id')
    if not cid:
        raise Exception("Trakt Client ID vazio")
    url = OAUTH + "/device/code"
    data = {"client_id": cid}
    return _req(url, data=data, headers=_headers())

def poll_for_token(device_code, interval=5, expires_in=600):
    start = time.time()
    while time.time() - start < expires_in:
        try:
            tok = _req(OAUTH + "/device/token", data={
                "code": device_code,
                "client_id": ADDON.getSettingString('trakt_client_id'),
                "client_secret": ADDON.getSettingString('trakt_client_secret')
            }, headers=_headers())
            if tok and tok.get("access_token"):
                ADDON.setSettingString('trakt_access_token', tok["access_token"])
                ADDON.setSettingString('trakt_refresh_token', tok.get("refresh_token",""))
                return tok
        except Exception as e:
            pass
        time.sleep(max(2,int(interval)))
    raise Exception("Timeout a obter token Trakt")

def refresh_token():
    rt = ADDON.getSettingString('trakt_refresh_token')
    if not rt: return False
    tok = _req(OAUTH + "/token", data={
        "refresh_token": rt,
        "client_id": ADDON.getSettingString('trakt_client_id'),
        "client_secret": ADDON.getSettingString('trakt_client_secret'),
        "grant_type": "refresh_token",
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob"
    }, headers=_headers())
    if tok and tok.get("access_token"):
        ADDON.setSettingString('trakt_access_token', tok["access_token"])
        ADDON.setSettingString('trakt_refresh_token', tok.get("refresh_token",""))
        return True
    return False

# ---- Next Up & watched ----
def next_up(limit=20):
    # Use progress watching list
    try:
        data = _req(BASE + "/sync/playback/episodes", headers=_headers(authed=True))
        out = []
        for ep in data or []:
            show = ep.get("show",{}).get("title","")
            s = ep.get("episode",{}).get("season",1)
            e = ep.get("episode",{}).get("number",1) + 1
            out.append({"title": show, "season": s, "episode": e})
        return out[:limit]
    except Exception:
        return []

def watched_movies():
    try:
        data = _req(BASE + "/sync/watched/movies", headers=_headers(authed=True))
        ids = set()
        for m in data or []:
            if m.get("movie",{}).get("ids",{}).get("tmdb"):
                ids.add(("movie", int(m["movie"]["ids"]["tmdb"])))
        return ids
    except Exception:
        return set()

def watched_episodes():
    try:
        data = _req(BASE + "/sync/watched/shows", headers=_headers(authed=True))
        seen = set()
        for s in data or []:
            show = s.get("show",{}).get("title","")
            for ss in s.get("seasons",[]):
                season = ss.get("number",0)
                for ep in ss.get("episodes",[]):
                    seen.add((show, season, ep.get("number",0)))
        return seen
    except Exception:
        return set()

def mark_watched_movie(tmdb_id):
    payload = {"movies":[{"ids":{"tmdb": tmdb_id}}]}
    try:
        _req(BASE + "/sync/history", data=payload, headers=_headers(authed=True))
        return True
    except Exception:
        return False

def mark_watched_episode(title, season, episode):
    payload = {"shows":[{"title": title, "seasons":[{"number": int(season), "episodes":[{"number": int(episode)}]}]}]}
    try:
        _req(BASE + "/sync/history", data=payload, headers=_headers(authed=True))
        return True
    except Exception:
        return False

def scrobble_start(title, season=None, episode=None, progress=0, tmdb_show_id=None, tmdb_movie_id=None):
    body = {"progress": float(progress)}
    if tmdb_movie_id:
        body["movie"] = {"ids":{"tmdb": int(tmdb_movie_id)}}
    elif season is not None and episode is not None:
        body["show"] = {"title": title}
        body["episode"] = {"season": int(season), "number": int(episode)}
    return _req(BASE + "/scrobble/start", data=body, headers=_headers(authed=True))


def scrobble_stop(title, season=None, episode=None, progress=100, tmdb_show_id=None, tmdb_movie_id=None):
    body = {"progress": float(progress)}
    if tmdb_movie_id:
        body["movie"] = {"ids":{"tmdb": int(tmdb_movie_id)}}
    elif season is not None and episode is not None:
        body["show"] = {"title": title}
        body["episode"] = {"season": int(season), "number": int(episode)}
    return _req(BASE + "/scrobble/stop", data=body, headers=_headers(authed=True))

