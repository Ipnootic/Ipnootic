import json, urllib.request

API = "https://graphql.anilist.co"

def _post(query, variables=None):
    payload = json.dumps({"query": query, "variables": variables or {}}).encode('utf-8')
    req = urllib.request.Request(API, data=payload, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

def trending(limit=20):
    q = '''
    query($per:Int){ Page(perPage:$per){ media(type:ANIME, sort:TRENDING_DESC){ id title{romaji} season seasonYear } } }
    '''
    data = _post(q, {"per": limit})
    out = []
    for m in (data.get("data",{}).get("Page",{}).get("media") or []):
        out.append({"title": m["title"]["romaji"], "season": 1, "episode": 1})
    return out

def current_season(limit=20):
    q = '''
    query($per:Int){ Page(perPage:$per){ media(type:ANIME, season:SUMMER, sort:POPULARITY_DESC){ id title{romaji} } } }
    '''
    data = _post(q, {"per": limit})
    out = []
    for m in (data.get("data",{}).get("Page",{}).get("media") or []):
        out.append({"title": m["title"]["romaji"], "season": 1, "episode": 1})
    return out
