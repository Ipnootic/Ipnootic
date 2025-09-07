# Thin wrappers to avoid Kodi API import errors when linting
try:
    import xbmc, xbmcgui, xbmcaddon, xbmcplugin
except Exception:
    xbmc = xbmcgui = xbmcaddon = xbmcplugin = None
