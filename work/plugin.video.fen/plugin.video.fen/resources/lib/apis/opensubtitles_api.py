# -*- coding: utf-8 -*-
import re
import shutil
from zipfile import ZipFile
from datetime import timedelta
from caches.main_cache import main_cache
from modules.kodi_utils import requests, json, notification, sleep, delete_file, rename_file, quote
# from modules.kodi_utils import logger

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

class OpenSubtitlesAPI:
	def __init__(self):
		self.headers = {'User-Agent': user_agent}
		self.token = None
		self.login()
		
	def login(self):
		"""Login to OpenSubtitles API"""
		from modules.kodi_utils import logger
		try:
			login_data = {
				'username': 'FenUser',
				'password': 'FenPass123',
				'useragent': user_agent
			}
			response = requests.post('https://rest.opensubtitles.org/login', 
									json=login_data, 
									headers=self.headers)
			if response.status_code == 200:
				data = response.json()
				self.token = data.get('token')
				if self.token:
					self.headers['Authorization'] = f'Bearer {self.token}'
					logger('FEN', 'DEBUG: Login OpenSubtitles bem-sucedido')
				else:
					logger('FEN', 'DEBUG: Login OpenSubtitles falhou - sem token')
			else:
				logger('FEN', 'DEBUG: Login OpenSubtitles falhou - status %d' % response.status_code)
		except Exception as e:
			logger('FEN', 'DEBUG: Erro no login OpenSubtitles: %s' % str(e))

	def search(self, query, imdb_id, language, season=None, episode=None):
		from modules.kodi_utils import logger
		logger('FEN', 'DEBUG: OpenSubtitles API search iniciado')
		imdb_clean = re.sub(r'[^0-9]', '', imdb_id or '')
		cache_key = imdb_clean or (imdb_id or (query or 'no_id'))
		cache_name = 'opensubtitles_%s_%s' % (cache_key, language)
		if season: cache_name += '_%s_%s' % (season, episode)
		cache = main_cache.get(cache_name)
		if cache:
			logger('FEN', 'DEBUG: Cache hit - %d legendas' % len(cache))
			return cache

		path_parts = []
		if imdb_clean:
			path_parts.append(f'imdbid-{imdb_clean}')
		if query:
			path_parts.append(f'query-{quote(query)}')
		if season is not None and episode is not None:
			path_parts.append(f'season-{season}')
			path_parts.append(f'episode-{episode}')
		path_parts.append(f'sublanguageid-{language}')
		url = 'https://rest.opensubtitles.org/search/' + '/'.join(path_parts)
		logger('FEN', 'DEBUG: URL chamada: %s' % url[:200])
		response = self._get(url, retry=True)
		if not response:
			logger('FEN', 'DEBUG: Resposta é None')
			return []
		try:
			response = json.loads(response.text)
			logger('FEN', 'DEBUG: API retornou %d legendas' % len(response))
			main_cache.set(cache_name, response, expiration=timedelta(hours=24))
			return response
		except Exception as e:
			logger('FEN', 'DEBUG: Erro JSON: %s' % str(e))
			return []


	def download(self, url, filepath, temp_zip, temp_path, final_path):
		from modules.kodi_utils import logger
		logger('FEN', 'DEBUG: Iniciando download de legenda')
		try:
			result = self._get(url, stream=True, retry=True)
			if not result:
				logger('FEN', 'DEBUG: Erro - resposta None no download')
				return None
			with open(temp_zip, 'wb') as f: shutil.copyfileobj(result.raw, f)
			with ZipFile(temp_zip, 'r') as zip_file: zip_file.extractall(filepath)
			delete_file(temp_zip)
			rename_file(temp_path, final_path)
			logger('FEN', 'DEBUG: Download concluído: %s' % final_path)
			return final_path
		except Exception as e:
			logger('FEN', 'DEBUG: Erro no download: %s' % str(e))
			return None

	def _get(self, url, stream=False, retry=False):
		response = requests.get(url, headers=self.headers, stream=stream)
		if '200' in str(response): return response
		elif '429' in str(response) and retry:
			notification(32740, 3500)
			sleep(10000)
			return self._get(url, stream)
		else: return
