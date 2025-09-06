from ..utils.settings import get_str, ADDON

def _num(v, default=0.0):
    try: return float(v)
    except: return default

def rank_sources(sources, query):
    prefer = query.get('prefer_quality') or '1080p'
    exclude = [w.strip().lower() for w in (query.get('exclude') or '').split(',') if w.strip()]
    prefer_codecs = [w.strip().lower() for w in get_str('prefer_codecs','x265,hevc,av1').split(',') if w.strip()]
    min_seed = _num(ADDON.getSettingString('filters_min_seeders') or 0, 0)
    min_size = _num(ADDON.getSettingString('filters_min_size_gb') or 0.0, 0.0)
    max_size = _num(ADDON.getSettingString('filters_max_size_gb') or 0.0, 0.0)
    exclude_cam = ADDON.getSettingBool('exclude_cam_ts')

    def bad(s):
        name = (s.get('title','') + ' ' + s.get('release','')).lower()
        if any(w in name for w in exclude): return True
        if exclude_cam and (' cam ' in ' '+name+' ' or 'ts ' in name or 'telecine' in name): return True
        if int(s.get('seeders',0)) < min_seed: return True
        sg = _num(s.get('size_gb',0.0), 0.0)
        if sg and sg < min_size: return True
        if max_size and sg and sg > max_size: return True
        return False

    order = ['480p','720p','1080p','2160p']
    def score(s):
        sc = 0
        if s.get('debrid'): sc += 120
        q = s.get('quality') or 'unknown'
        if q in order: sc += order.index(q)*12
        if q == prefer: sc += 6
        sg = _num(s.get('size_gb',0), 0)
        sc += min(sg, 30)
        sc += int(s.get('seeders',0)) * 0.12
        tag = (s.get('title','') + ' ' + s.get('release','')).lower()
        if any(c in tag for c in prefer_codecs): sc += 3
        if 'bluray' in tag or 'webrip' in tag or 'web-dl' in tag: sc += 2
        if 'remux' in tag: sc += 4
        if 'cam' in tag or ' ts ' in tag: sc -= 60
        return sc

    ranked = [s for s in sources if not bad(s)]
    return sorted(ranked, key=score, reverse=True)
