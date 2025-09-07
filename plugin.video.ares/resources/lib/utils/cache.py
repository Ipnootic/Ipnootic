import os, json, sqlite3, time
import xbmc, xbmcaddon

ADDON = xbmcaddon.Addon()
DBPATH = os.path.join(xbmc.translatePath(ADDON.getAddonInfo('profile')), "cache.sqlite")

def _conn():
    os.makedirs(os.path.dirname(DBPATH), exist_ok=True)
    con = sqlite3.connect(DBPATH)
    con.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT, exp INTEGER)")
    return con

def set(key, value, ttl=3600):
    exp = int(time.time()+ttl) if ttl>0 else 0
    with _conn() as con:
        con.execute("REPLACE INTO kv (k,v,exp) VALUES (?,?,?)", (key, json.dumps(value), exp))

def get(key):
    now = int(time.time())
    with _conn() as con:
        cur = con.execute("SELECT v,exp FROM kv WHERE k=?", (key,))
        row = cur.fetchone()
        if not row: return None
        v, exp = row
        if exp and exp < now:
            con.execute("DELETE FROM kv WHERE k=?", (key,))
            return None
        try: return json.loads(v)
        except: return None
