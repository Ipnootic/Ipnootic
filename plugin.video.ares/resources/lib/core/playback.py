import xbmcplugin, xbmcgui
from ..resolvers.debrid import resolve_magnet_or_url
from ..subs.opensubs import auto_subtitle_for
from ..utils.store import add_episode_play
from ..utils.settings import get_bool

def resolve_and_play(src, handle):
    # Save to local history if episode
    if src.get('type') == 'episode' or src.get('kind') == 'episode':
        add_episode_play(src.get('title'), src.get('season') or 1, src.get('episode') or 1)

    url = resolve_magnet_or_url(src)
    if not url:
        xbmcgui.Dialog().notification("Ares", "Falha a resolver fonte", xbmcgui.NOTIFICATION_ERROR, 3000)
        return
    li = xbmcplugin.ListItem(path=url)
    # Attempt subtitle auto-load
    try:
        if get_bool('os_enabled') and get_bool('os_auto_load'):
            sub_path = auto_subtitle_for(src)
            if sub_path:
                li.setSubtitles([sub_path])
    except Exception:
        pass
    xbmcplugin.setResolvedUrl(handle, True, li)
