import json, os
from ..utils.settings import get_str
from xbmcaddon import Addon
ADDON = Addon()
def load_menu():
    preset_idx = int(ADDON.getSettingInt('menu_preset'))
    preset = ['Minimal','Extended','Custom'][preset_idx]
    path = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'menus.json')
    data = json.load(open(path, 'r', encoding='utf-8'))
    if preset == 'Custom' and not data.get('Custom'):
        return data['Minimal']
    return data.get(preset, data['Minimal'])
