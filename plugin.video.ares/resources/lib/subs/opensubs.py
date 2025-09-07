import os, json, urllib.request, urllib.parse, tempfile
from ..utils.settings import get_str

API = "https://api.opensubtitles.com/api/v1"

def _req(path, params=None, headers=None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    hdrs = {"Api-Key": get_str('os_api_key','')}
    if headers: hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def _download(file_id):
    url = API + "/download"
    data = json.dumps({"file_id": file_id}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Api-Key": get_str('os_api_key',''), "Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        meta = json.loads(r.read().decode())
    if not meta or not meta.get("link"): 
        return None
    # Fetch the actual subtitle file
    req2 = urllib.request.Request(meta["link"])
    with urllib.request.urlopen(req2, timeout=20) as r2:
        data = r2.read()
    fd, subpath = tempfile.mkstemp(suffix=".srt")
    os.write(fd, data); os.close(fd)
    return subpath

def auto_subtitle_for(src):
    api_key = get_str('os_api_key','')
    if not api_key: return None
    langs = [s.strip() for s in get_str('os_langs','pt,pt-BR').split(',') if s.strip()]
    title = src.get('title') or ""
    year = src.get('year') or ""
    season = src.get('season'); episode = src.get('episode')
    params = {"query": title, "languages": ",".join(langs)}
    if year: params["year"] = year
    if season and episode:
        params["season_number"] = season; params["episode_number"] = episode
    try:
        data = _req("/subtitles", params=params)
        items = data.get('data') or []
        # crude scoring: exact season/ep match > lang pref
        def score(it):
            a = it.get('attributes',{})
            sc = 0
            if a.get('language') in langs: sc += 3
            if season and a.get('season_number') == int(season): sc += 2
            if episode and a.get('episode_number') == int(episode): sc += 2
            if a.get('hearing_impaired'): sc -= 1
            return sc
        items.sort(key=score, reverse=True)
        if not items: return None
        file_id = items[0].get('attributes',{}).get('files',[{}])[0].get('file_id')
        if not file_id: return None
        return _download(file_id)
    except Exception:
        return None
