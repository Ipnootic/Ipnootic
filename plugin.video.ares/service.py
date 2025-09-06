import xbmc, xbmcgui, json
from resources.lib.utils.settings import get_bool
from resources.lib.utils.store import add_episode_play
from resources.lib.metadata.tmdb import compute_next
from resources.lib.trakt import client as trakt

class Player(xbmc.Player):
    def __init__(self): super().__init__(); self.last_info = None
    def onAVStarted(self):
        title = xbmc.getInfoLabel('VideoPlayer.TVshowtitle')
        season = xbmc.getInfoLabel('VideoPlayer.Season')
        episode = xbmc.getInfoLabel('VideoPlayer.Episode')
        if title and season and episode:
            try:
                add_episode_play(title, int(season), int(episode))
                trakt.scrobble_start(title, int(season), int(episode), progress=0)
            except Exception:
                pass
        self.last_info = (title, season, episode)

    def onPlayBackEnded(self):
        try:
            if not (self.last_info and self.last_info[0]): return
            title, season, episode = self.last_info
            season = int(season or 1); episode = int(episode or 1)
            # scrobble complete
            try: trakt.scrobble_stop(title, season, episode, progress=100)
            except Exception: pass
            # compute next using TMDb season bounds
            ns, ne = compute_next(title, season, episode)
            if get_bool('autoplay_next'):
                xbmc.executebuiltin(f'RunPlugin(plugin://plugin.video.ares/?action=aggregate&kind=episode&title={title}&season={ns}&episode={ne})')
                return
            if get_bool('post_play_prompt'):
                dlg = xbmcgui.Dialog()
                ret = dlg.yesno("Ares", f"Reproduzir o próximo episódio?\n{title} S{str(ns).zfill(2)}E{str(ne).zfill(2)}", yeslabel="Seguir", nolabel="Parar")
                if ret:
                    xbmc.executebuiltin(f'RunPlugin(plugin://plugin.video.ares/?action=aggregate&kind=episode&title={title}&season={ns}&episode={ne})')
        except Exception:
            pass

class Service(xbmc.Monitor):
    def __init__(self): super().__init__(); self.player = Player()
    def run(self):
        while not self.abortRequested():
            if self.waitForAbort(1): break

if __name__ == "__main__":
    Service().run()
