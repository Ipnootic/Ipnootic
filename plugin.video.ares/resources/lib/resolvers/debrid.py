import json, urllib.parse, urllib.request, time
from ..utils.settings import get_str

API = "https://api.real-debrid.com/rest/1.0"

def _rd_req(path, method="GET", data=None, token=None, headers=None):
    token = token or get_str('rd_token','')
    if not token: return None
    url = f"{API}/{path}"
    hdrs = {"Authorization": f"Bearer {token}"}
    if headers: hdrs.update(headers)
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read().decode()
        try: return json.loads(raw)
        except: return raw

def _pick_video_files(files):
    vids = []
    for f in files or []:
        name = f.get("path") or f.get("filename") or ""
        if any(name.lower().endswith(ext) for ext in (".mkv",".mp4",".avi",".mov",".mpg",".m4v",".webm")):
            vids.append(f)
    # choose largest
    vids.sort(key=lambda x: x.get("bytes",0), reverse=True)
    return vids

def resolve_magnet_or_url(src):
    # Direct HTTP link
    if src.get('url'):
        # For hosters via RD you could unrestrict here too if desired
        return src['url']

    magnet = src.get('magnet')
    if not magnet:
        return None

    # 1) Add magnet to RD
    add = _rd_req("torrents/addMagnet", method="POST", data={"magnet": magnet})
    if not add or not isinstance(add, dict) or not add.get("id"):
        return None
    tid = add["id"]

    # 2) Get torrent info, wait for metadata
    info = _rd_req(f"torrents/info/{tid}")
    t0 = time.time()
    while info and not info.get("files") and time.time() - t0 < 20:
        time.sleep(2)
        info = _rd_req(f"torrents/info/{tid}")
    if not info: return None

    # 3) Select video files (largest by default)
    files = _pick_video_files(info.get("files", []))
    if not files: return None
    file_ids = ",".join(str(f["id"]) for f in files[:1])  # select best 1 by default
    _ = _rd_req(f"torrents/selectFiles/{tid}", method="POST", data={"files": file_ids})

    # 4) Refresh info to get generated links
    info = _rd_req(f"torrents/info/{tid}")
    links = info.get("links") or []
    if not links: return None

    # 5) Unrestrict chosen link to streamable URL
    best = links[0]
    unr = _rd_req("unrestrict/link", method="POST", data={"link": best})
    if isinstance(unr, dict) and unr.get("download"):
        return unr["download"]

    return None
