import xbmcaddon
ADDON = xbmcaddon.Addon()
def get_str(id, default=""): return ADDON.getSettingString(id) or default
def get_bool(id): return ADDON.getSettingBool(id)
def get_int(id, default=0): 
    try: return int(ADDON.getSettingInt(id))
    except: return default
