# -*- coding: utf-8 -*-
import time
from windows.base_window import BaseDialog
from modules.kodi_utils import Thread, sleep, get_setting, set_setting, notification, local_string as ls
from modules.kodi_utils import make_listitem, json
# from modules.kodi_utils import logger

class SubtitleSelector(BaseDialog):
	def __init__(self, *args, **kwargs):
		BaseDialog.__init__(self, *args)
		self.subtitles_list = kwargs.get('subtitles_list', [])
		self.selected_subtitle = None
		self.auto_hide_time = int(get_setting('fen.subtitles.overlay_time', '15'))
		self.is_auto_closing = False
		self.timer_active = get_setting('fen.subtitles.show_timer', 'false') == 'true'
		self.set_overlay_properties()
		
	def onInit(self):
		try:
			from modules.kodi_utils import logger
			logger('FEN', 'DEBUG: Overlay onInit iniciado')
			self.setProperty('highlight_var', self.highlight_var(force=True))
			self.populate_subtitles()
			self.setFocusId(5001)  # Focus on subtitle list
			if self.auto_hide_time > 0:
				Thread(target=self.auto_hide_monitor).start()
			if self.timer_active and self.auto_hide_time > 0:
				Thread(target=self.update_timer).start()
			logger('FEN', 'DEBUG: Overlay onInit concluído')
		except Exception as e:
			from modules.kodi_utils import logger
			logger('FEN', 'DEBUG: Erro no onInit: %s' % str(e))
			notification("Erro no onInit: %s" % str(e), 3000)
			
	def run(self):
		from modules.kodi_utils import logger
		logger('FEN', 'DEBUG: Overlay run iniciado')
		self.doModal()
		self.clearProperties()
		logger('FEN', 'DEBUG: Overlay run concluído - resultado: %s' % str(self.selected_subtitle))
		return self.selected_subtitle
		
	def onClick(self, controlID):
		from modules.kodi_utils import logger
		logger('FEN', 'DEBUG: Overlay onClick - controlID: %d' % controlID)
		if controlID == 5001:  # Subtitle list
			self.select_current_subtitle()
		elif controlID == 9999:  # Close button
			self.close_dialog()
			
	def onAction(self, action):
		if action in self.selection_actions:
			self.select_current_subtitle()
		elif action in self.closing_actions:
			self.close_dialog()
		# Reset timer on any action
		if hasattr(self, 'start_time'):
			self.start_time = time.time()
			
	def set_overlay_properties(self):
		"""Set the overlay position and size based on user settings"""
		overlay_x = get_setting('fen.subtitles.overlay_x', '760')
		overlay_y = get_setting('fen.subtitles.overlay_y', '390') 
		overlay_width = get_setting('fen.subtitles.overlay_width', '400')
		overlay_height = get_setting('fen.subtitles.overlay_height', '300')
		
		# Ensure we have valid values and constrain to screen
		try:
			overlay_x = max(0, min(int(overlay_x), 1520))  # Keep within screen bounds
			overlay_y = max(0, min(int(overlay_y), 780))
			overlay_width = max(200, min(int(overlay_width), 800))
			overlay_height = max(150, min(int(overlay_height), 600))
		except:
			overlay_x, overlay_y = 760, 390
			overlay_width, overlay_height = 400, 300
			
		# Calculate derived properties for dynamic sizing
		overlay_width_plus = overlay_width + 4
		overlay_height_plus = overlay_height + 4
		header_width = overlay_width - 80
		list_width = overlay_width - 16
		list_height = overlay_height - 85
		item_width = list_width - 80
		quality_x = list_width - 70
		close_button_x = overlay_width - 35
		scrollbar_x = list_width + 2
		footer_y = overlay_height - 30
		
		# Set all properties
		self.setProperty('overlay_x', str(overlay_x))
		self.setProperty('overlay_y', str(overlay_y)) 
		self.setProperty('overlay_width', str(overlay_width))
		self.setProperty('overlay_height', str(overlay_height))
		self.setProperty('overlay_width_plus', str(overlay_width_plus))
		self.setProperty('overlay_height_plus', str(overlay_height_plus))
		self.setProperty('header_width', str(header_width))
		self.setProperty('list_width', str(list_width))
		self.setProperty('list_height', str(list_height))
		self.setProperty('item_width', str(item_width))
		self.setProperty('quality_x', str(quality_x))
		self.setProperty('close_button_x', str(close_button_x))
		self.setProperty('scrollbar_x', str(scrollbar_x))
		self.setProperty('footer_y', str(footer_y))
		self.setProperty('show_timer', 'true' if self.timer_active else 'false')
		
	def populate_subtitles(self):
		"""Populate the subtitle list"""
		try:
			from modules.kodi_utils import logger
			logger('FEN', 'DEBUG: Populando lista com %d legendas' % len(self.subtitles_list))
			notification("Populando lista com %d legendas" % len(self.subtitles_list), 2000)
			
			if not self.subtitles_list:
				# Show "No subtitles found" option
				listitem = make_listitem()
				listitem.setProperty('subtitle_name', "Nenhuma legenda encontrada")
				self.get_control(5001).addItem(listitem)
				return
				
			# Add "No subtitles" option at the top
			listitem = make_listitem()
			listitem.setProperty('subtitle_name', 'Desligar Legendas')
			listitem.setProperty('subtitle_data', json.dumps({'action': 'disable'}))
			self.get_control(5001).addItem(listitem)
			
			# Add available subtitles
			for i, subtitle in enumerate(self.subtitles_list):
				listitem = make_listitem()
				
				# Format subtitle name (simplified)
				lang = subtitle.get('SubLanguageID', 'Unknown').upper()
				release_name = subtitle.get('MovieReleaseName', 'Unknown Release')
				if len(release_name) > 40:
					release_name = release_name[:37] + '...'
					
				subtitle_name = "%s - %s" % (lang, release_name)
				
				listitem.setProperty('subtitle_name', subtitle_name)
				listitem.setProperty('subtitle_data', json.dumps(subtitle))
				
				self.get_control(5001).addItem(listitem)
				
			notification("Lista populada com sucesso", 2000)
			
		except Exception as e:
			notification("Erro ao popular lista: %s" % str(e), 3000)
			
	def extract_quality(self, release_name):
		"""Extract quality info from release name"""
		release_lower = release_name.lower()
		quality_keywords = {
			'bluray': 'BluRay', 'brrip': 'BRRip', 'bdrip': 'BDRip',
			'webrip': 'WebRip', 'webdl': 'Web-DL', 'web-dl': 'Web-DL',
			'hdtv': 'HDTV', 'dvdrip': 'DVDRip', 'hdrip': 'HDRip',
			'cam': 'CAM', 'ts': 'TS', 'tc': 'TC'
		}
		
		for keyword, display in quality_keywords.items():
			if keyword in release_lower:
				return display
				
		# Check for resolution
		if '2160p' in release_lower or '4k' in release_lower:
			return '4K'
		elif '1080p' in release_lower:
			return '1080p'
		elif '720p' in release_lower:
			return '720p'
		elif '480p' in release_lower:
			return '480p'
			
		return 'SD'
		
	def select_current_subtitle(self):
		"""Select the currently focused subtitle"""
		try:
			from modules.kodi_utils import logger
			logger('FEN', 'DEBUG: Selecionando legenda atual')
			control = self.get_control(5001)
			selected_item = control.getSelectedItem()
			subtitle_data = selected_item.getProperty('subtitle_data')
			
			if subtitle_data:
				self.selected_subtitle = json.loads(subtitle_data)
				logger('FEN', 'DEBUG: Legenda selecionada: %s' % selected_item.getProperty('subtitle_name'))
				notification(f"Legenda selecionada: {selected_item.getProperty('subtitle_name')}", 2000)
			else:
				self.selected_subtitle = None
				logger('FEN', 'DEBUG: Nenhuma legenda selecionada')
				
		except Exception as e:
			from modules.kodi_utils import logger
			logger('FEN', 'DEBUG: Erro ao selecionar legenda: %s' % str(e))
			self.selected_subtitle = None
			
		self.close_dialog()
		
	def close_dialog(self):
		"""Close the dialog"""
		self.is_auto_closing = True
		self.close()
		
	def auto_hide_monitor(self):
		"""Auto-hide the dialog after specified time"""
		self.start_time = time.time()
		
		while not self.is_auto_closing:
			current_time = time.time()
			elapsed = current_time - self.start_time
			
			if elapsed >= self.auto_hide_time:
				self.is_auto_closing = True
				notification("Janela de legendas fechada automaticamente", 2000)
				self.close()
				break
				
			sleep(500)  # Check every 500ms
			
	def update_timer(self):
		"""Update the progress timer if enabled"""
		if not self.timer_active or self.auto_hide_time <= 0:
			return
			
		self.start_time = time.time()
		
		while not self.is_auto_closing:
			current_time = time.time()
			elapsed = current_time - self.start_time
			progress = min((elapsed / self.auto_hide_time) * 100, 100)
			
			try:
				self.get_control(8000).setPercent(progress)
			except:
				break
				
			if elapsed >= self.auto_hide_time:
				break
				
			sleep(100)  # Update every 100ms for smooth animation
