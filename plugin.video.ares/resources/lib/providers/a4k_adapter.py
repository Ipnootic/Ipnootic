# Adapter for a4kscrapers if installed in Kodi's Python env.
def search(query):
    try:
        import a4kscrapers
    except Exception:
        return []
    # NOTE: API signatures vary by version. This is a placeholder call pattern.
    # You must adapt to the exact a4kscrapers API you have installed.
    # Expected normalized return:
    # [{"title": ..., "quality":"1080p","size_gb":7.1,"seeders":500,"magnet": "...","debrid":True}, ...]
    # Fallback demo:
    title = query.get('title','')
    if not title: return []
    return [{"title": f"{title}.a4k.1080p", "quality":"1080p", "size_gb":7.2, "seeders":420, "magnet":"magnet:?xt=urn:btih:A4KDEMO", "debrid": True, "provider":"a4k"}]
