# Adapter for cocoscrapers if installed.
def search(query):
    try:
        import cocoscrapers
    except Exception:
        return []
    title = query.get('title','')
    if not title: return []
    # Placeholder normalized result
    return [{"title": f"{title}.coco.2160p", "quality":"2160p", "size_gb":16.4, "seeders":250, "magnet":"magnet:?xt=urn:btih:COCODEMO", "debrid": True, "provider":"coco"}]
