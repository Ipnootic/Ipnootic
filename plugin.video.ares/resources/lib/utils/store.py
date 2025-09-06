import os, json
from xbmcaddon import Addon

ADDON = Addon()
DATA_DIR = xbmc.translatePath(ADDON.getAddonInfo('profile')) if hasattr(__import__('xbmc'), 'translatePath') else ADDON.getAddonInfo('profile')
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    pass
HIST = os.path.join(DATA_DIR, "history.json")

def _load():
    try:
        with open(HIST, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return {"episodes": []}

def _save(data):
    try:
        with open(HIST, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception: pass

def add_episode_play(title, season, episode, next_title=None):
    data = _load()
    data["episodes"] = [e for e in data["episodes"] if not (e.get("title")==title and e.get("season")==season and e.get("episode")==episode)]
    data["episodes"].insert(0, {"title": title, "season": int(season), "episode": int(episode), "next_title": next_title})
    data["episodes"] = data["episodes"][:200]
    _save(data)

def nextup_list(limit=20):
    data = _load()
    return data["episodes"][:limit]
