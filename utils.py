import sys
import atexit
import requests
from urllib import parse
from threading import Thread
import json
import re
import uuid
import bottle



class Server:
	def __init__(self, config, settings):
		self.config = config
		self.settings = settings
		self.window = None

		self.common_path = '.'
		self.running = False
		self.address = None

		self.port = self.settings.get('port')
		if self.port:
			self.address = self.config.URLS.localhost_address_template.format(self.port)

			if self.redial():
				sys.exit()

		# self.js_callback = {}
		# self.js_api_endpoint = None
		self.uid = str(uuid.uuid1())
		

		bottle.response.set_header('Cache-Control', 'no-cache, no-store, must-revalidate')
		bottle.response.set_header('Pragma', 'no-cache')
		bottle.response.set_header('Expires', 0)
		
		self.start_server()
		
		self.settings.set(port=self.port)
		
		atexit.register(self.settings.remove, 'port')

	def set_window(self, window):
		self.window = window

	def start_server(self):
		from webview.http import ThreadedAdapter, _get_random_port
		
		from main_html import main_html

		app = bottle.Bottle()

		# @app.post(f'/js_api/{self.uid}')
		# def js_api():
		# 	bottle.response.headers['Access-Control-Allow-Origin'] = '*'
		# 	bottle.response.headers[
		# 		'Access-Control-Allow-Methods'
		# 	] = 'PUT, GET, POST, DELETE, OPTIONS'
		# 	bottle.response.headers[
		# 		'Access-Control-Allow-Headers'
		# 	] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

		# 	body = json.loads(bottle.request.body.read().decode('utf-8'))
		# 	if body['uid'] in self.js_callback:
		# 		return json.dumps(self.js_callback[body['uid']](body))


		@app.route('/')
		@app.route('/<file:path>')
		def index(file=None):
			if not file:
				file = 'main.html'
				
			item = main_html.get(file)
			if not item:
				return bottle.HTTPError(404)
			
			return bottle.HTTPResponse(item["content"], **{"Content-Type": item["content_type"], "Content-Length": len(item["content"])})
		

		@app.route('/redial', method='POST')
		def redial():
			json_data = bottle.request.json
			if json_data == None or not self.window:
				return
			
			self.window.on_top = True
	
			user_id = json_data.get('user_id')
			redial_address = json_data.get('redial_address')
			if redial_address:
				redial_address = re.sub(r"^http", 'ss14', redial_address)
				if redial_address.endswith('/'):
					redial_address = redial_address[:-1]
					
				self.window._js_api.ss14api.connect_server(redial_address, user_id)
			
			self.window.on_top = False

			return bottle.HTTPResponse(status=200)
		
		# @app.route('/proxy_auth/<url:path>', method='POST')
		# def proxy_auth(url=None):
			
		# 	print(bottle.request.method)
		# 	print(self.config.URLS.auth + f'/{url}')
		# 	print(dict(bottle.request.headers) | {'Host': self.config.URLS.host})
		# 	print(bottle.request.body)


		# 	proxy_responce = re2quest(
		# 		bottle.request.method,
		# 		self.config.URLS.auth + f'/{url}',
		# 		headers=dict(bottle.request.headers) | {'Host': self.config.URLS.host},
		# 		json=bottle.request.json
		# 		)
			
		# 	print(proxy_responce.status_code)
		# 	print(proxy_responce.headers)
		# 	print(proxy_responce.content)

		# 	return bottle.HTTPResponse(body=proxy_responce.content, headers=dict(proxy_responce.headers), status=proxy_responce.status_code)


		self.port = _get_random_port()

		self.thread = Thread(target=lambda: bottle.run(app=app, server=ThreadedAdapter, port=self.port, quiet=not self.config.debug), daemon=True)
		self.thread.start()

		self.running = True
		self.address = self.config.URLS.localhost_address_template.format(self.port)
		# self.js_api_endpoint = f'{self.address}js_api/{self.uid}'

		return self.address, None, self

	def redial(self):
		try:
			data = {}

			if len(sys.argv) == 5:
				reason = bytes.fromhex(sys.argv[3][1:]).decode("utf-8")
				redial_data = bytes.fromhex(sys.argv[4][1:]).decode("utf-8")

				parsed_redial_data = parse.urlparse(redial_data)

				data["user_id"] = parsed_redial_data.fragment
				data["redial_address"] = parsed_redial_data._replace(fragment="").geturl()

			response = requests.post(self.address + 'redial', json=data, timeout=0.5)
			if response.status_code == 200:
				return True
			
		except:
			pass

		return False

	@property
	def is_running(self):
		return self.running



import os

def quick_file_reader(path, *args, **kwargs):
	if 'encoding' not in kwargs:
		kwargs["encoding"] = 'utf-8'

	if os.path.exists(path):
		with open(path, 'r', *args, **kwargs) as f:
			return f.read()

import sass

def update_css(css_dir, scss_dir):
	css_file_path = os.path.join(css_dir, os.path.normpath('main.css'))
	scss_file_path = os.path.join(scss_dir, os.path.normpath('main.scss'))
	
	if not os.path.exists(scss_file_path):
		return
	
	if not os.path.exists(css_file_path) or (os.path.getmtime(scss_file_path) > os.path.getmtime(css_file_path)):
		with open(css_file_path, 'w', encoding='utf-8') as css_file:
			compiled = sass.compile(filename=scss_file_path, output_style='compressed').strip('\ufeff')
			css_file.write(compiled)


def url_update_params(url, **kwargs):
	url_parts = list(parse.urlparse(url))
	params = dict(parse.parse_qsl(url_parts[4]))

	params.update(kwargs)

	url_parts[4] = parse.urlencode(params)

	return parse.urlunparse(url_parts)


def load_languages(languages_dir):
	languages = {}
	for language_file_name in os.listdir(languages_dir):
		if not language_file_name.endswith('.json'):
			continue
		
		language_file_path = os.path.join(languages_dir, language_file_name)
		with open(language_file_path, 'r', encoding='utf8') as file:
			language = json.load(file)
			if 'name' not in language or 'fields' not in language:
				continue
			
			language_code = os.path.splitext(language_file_name)[0]
			languages[language_code] = language
			
	return languages



disconnect_pattern = r'\[INFO\] net: \".*\": Disconnected \(\"(.*)\"\)'
def catch_disconnect_line(line):
	disconnect_line = re.match(disconnect_pattern, line)
	if disconnect_line:
		try:
			disconnect_line_content = disconnect_line.group(1).encode('utf-8').decode('unicode-escape')
			if disconnect_line_content == 'Connection timed out':
				return True
			
			disconnect_line_content_json = json.loads(disconnect_line_content)
			if disconnect_line_content_json.get('reason', '').startswith('Server shutting down') and disconnect_line_content_json.get('redial'):
				return True
			
			raise

		except:
			return False


def split_list(lst, num_splits=None, max_size=None):
	if num_splits != None and num_splits > 0:
		if num_splits > len(lst):
			num_splits = len(lst)

		split_size = len(lst) // num_splits
		split_remainder = len(lst) % num_splits

		result = []
		start = 0
		for i in range(num_splits):
			end = start + split_size
			if i < split_remainder:
				end += 1
			result.append(lst[start:end])
			start = end

		return result

	elif max_size != None and max_size > 0:
		sublist = []
		result = []
		for item in lst:
			sublist.append(item)
			if len(sublist) >= max_size:
				result.append(sublist)
				sublist = []

		if sublist:
			result.append(sublist)

		return result

	else:
		return lst


def int_from_4_bytes(_bytes):
	return int.from_bytes(_bytes, byteorder='little')



import pickle
from copy import deepcopy

class Settings():
	def __init__(self, config):
		self.config = config
		self.defaults = {
				"accounts": [],
				"added_servers": [],
				"compat_mode": False,
				"favorite_servers": [],
				"hide_not_favorite": False,
				"language": "en",
				"local_server_build": "syndicate",
				"multiverse_hub": True,
				"notes_sequence": [],
				"priority_for_account_connection": True,
				"reconnect_to_favorite": True,
				"stc": False,
				"stc_activation_key": [
					"Spacebar"
				],
				"stc_chat_key": [
					"T"
				],
				"stc_device": None,
				"stc_instant_send": False,
				"stc_prefixes": [
					["%", [
						"Shift"
						]
					],
					[";", [
						"Ctrl"
						]
					],
					[",", [
						"Alt"
						]
					]
				],
				"traffic_economy": True
			}
		
		self.settings = deepcopy(self.defaults)
		
		self._load()

	def _load(self):
		try:
			with open(self.config.settings_path, "rb") as file:
				self.settings = self.settings | pickle.load(file)
				
		except:
			try:
				with open(self.config.backup_settings_name, "rb") as file:
					self.settings = self.settings | pickle.load(file)
			except:
				self.remove()

		return self.settings
			

	def _dump(self):
		if os.path.exists(self.config.settings_path):
			os.replace(self.config.settings_path, self.config.backup_settings_name)

		with open(self.config.settings_path, "wb") as file:
			pickle.dump(self.settings, file)


	def get(self, *args):
		if not len(args):
			return self.settings

		if len(args) == 1:
			return self.settings.get(args[0])
		
		output = {}
		for arg in args:
			output[arg] = self.settings.get(arg)

		return output
	

	def set(self, **kwargs):
		self.settings.update(kwargs)

		self._dump()


	def remove(self, *args):
		if not len(args):
			self.settings = deepcopy(self.defaults)

		for arg in args:
			if arg in self.settings:
				del self.settings[arg]

		self._dump()



class ConnectionStatus():
	def __init__(self):
		self.clear()

	def clear(self):
		self.busy = False
		self.title = None
		self.description = None
		self.data = None
		self.cancel = False

	def set(self, **kwargs):
		if 'busy' in kwargs:
			self.busy = kwargs.get('busy')

		if 'title' in kwargs:
			self.title = kwargs.get('title')

		if 'description' in kwargs:
			self.description = kwargs.get('description')

		if 'data' in kwargs:
			self.data = kwargs.get('data')

		if 'cancel' in kwargs:
			self.cancel = kwargs.get('cancel')

	def to_dict(self):
		return {
			"busy": self.busy,
			"title": self.title,
			"description": self.description,
			"data": self.data,
			"cancel": self.cancel
		}



import shutil
import random
import string

class TempFileContainer:
	def __init__(self, dir=None, name=None, ext=None, keep=False):
		self.dir = dir
		if not self.dir:
			self.dir = os.path.dirname(os.path.abspath(sys.argv[0]))

		self.file_path = None
		
		if name:
			self.file_path = self._name_join_(name, ext)
			if os.path.exists(self.file_path):
				raise Exception('File already exists')

		else:
			while True:
				name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
				self.file_path = self._name_join_(name, ext)
				if not os.path.exists(self.file_path):
					break
		
		self.keep = keep

	def __enter__(self):
		if not os.path.exists(self.dir):
			os.makedirs(self.dir)

		with open(self.file_path, 'w') as file:
			pass

		return self.file_path

	def __exit__(self, exc_type, exc_value, traceback):
		if not self.keep:
			if len(os.listdir(self.dir)) > 1:
				try:
					os.remove(self.file_path)
				except:
					pass
			else:
				shutil.rmtree(self.dir, ignore_errors=True)

	def _name_join_(self, name, ext):
		if ext:
			name += f'.{ext}'

		return os.path.join(self.dir, name)




class CancelationToken:
	def __init__(self):
		self.reset()

	def reset(self):
		self.cancelled = False

	def cancel(self):
		if not self.cancelled:
			self.cancelled = True

	@property
	def condition(self):
		return self.cancelled


import time
from requests.exceptions import RequestException


def re2quest(method, url, cancellation_token=None, output=None, retries=5, session=None, **kwargs):
	params = {
		"timeout": 5
	}

	params.update(kwargs)

	if not session:
		session = requests.Session()
	
	attempt = 0
	while attempt < retries:
		if cancellation_token and cancellation_token.condition:
			return None
		
		try:
			response = session.request(method, url, **params)
			if output == 'json':
				response = response.json()
			elif output == 'text':
				response = response.text
			elif output == 'content':
				response = response.content
				
			return response
		
		except requests.exceptions.SSLError as e:
			if 'verify' not in params:
				params["verify"] = False
				continue

		except RequestException as e:
			time.sleep(1)
		
		attempt += 1

	return False



class ProgressBar():
	def __init__(self, window):
		self.js_progress_bar = 'progress_bar'
		self.window = window
	
	def _evaluate(self, action, *args):
		return self.window.evaluate_js(f'{self.js_progress_bar}.{action}({", ".join(args)});')

	def is_open(self):
		return self._evaluate('is_open')

	def show(self):
		self._evaluate('show')
	
	def hide(self):
		self._evaluate('hide')

	def set_title(self, title, reset_progress=True):
		self._evaluate('set_title', f'\"{title}\"', str(reset_progress).lower())

	def set_progress(self, progress):
		self._evaluate('set_progress', str(progress))

	def add_progress(self, progress):
		self._evaluate('add_progress', str(progress))



def length_to_parts(length, quantity):
	parts = []
	chunk_size = length // quantity
	while length > 0:
		end = length
		length -= chunk_size
		start = length

		if length < chunk_size:
			start -= length
			length = 0
			
		if start != 0:
			start += 1
			
		parts.insert(0, (start, end))

	return parts


from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

class Downloader:
	def __init__(self, cancellation_token=None, progress_bar=None):
		self.cancellation_token = cancellation_token
		self.progress_bar = progress_bar
	
	def _download(self, url, method='GET', retries=10, session=None, chunk_size=1024*128, total_parts=1, **kwargs):
		if self.cancellation_token and self.cancellation_token.condition:
			return None
		
		response = re2quest(method, url, self.cancellation_token, retries=retries, stream=True, session=session, **kwargs)
		if not response:
			return response
		
		stream = BytesIO()

		content_length = int(response.headers.get('Content-Length', 0))
		for chunk in response.iter_content(chunk_size=chunk_size):
			if not chunk or (self.cancellation_token and self.cancellation_token.condition):
				stream.close()
				return None

			if self.progress_bar and content_length:
				self.progress_bar.add_progress(100 / total_parts / content_length * chunk_size)

			stream.write(chunk)

		return stream
		


	def download(self, url, path, method='GET', retries=10, parts=20, **kwargs):
		if self.progress_bar:
			self.progress_bar.set_progress(0)

		session = requests.Session()

		response = re2quest('HEAD', url, self.cancellation_token, retries=retries, session=session, **kwargs)
		if response and response.headers.get('Accept-Ranges') == 'bytes' and (content_length:=int(response.headers.get('Content-Length', 0))):
			content_length_parts = length_to_parts(content_length, parts)
			
			futures = []
			with ThreadPoolExecutor(max_workers=10) as executor:
				for start_byte, end_byte in content_length_parts:
					part_kwargs = deepcopy(kwargs)
					range_headers = part_kwargs.get('headers', {})
					range_headers["Range"] = f'bytes={start_byte}-{end_byte}'
					part_kwargs["headers"] = range_headers

					future = executor.submit(self._download, url, method=method, retries=retries, session=session, total_parts=len(content_length_parts), **part_kwargs)
					futures.append(future)

			
			streams = []
			status = True
			for future in futures:
				stream = future.result()
				if stream:
					streams.append(stream)
				else:
					status = stream
					break

			if status:
				with open(path, 'ab') as f:
					for stream in streams:
						f.write(stream.getvalue())

			for stream in streams:
				stream.close()

			return status

		else:
			stream = self._download(url, method=method, retries=retries, session=session, **kwargs)
			if not stream:
				return stream
		
			with open(path, 'ab') as f:
				f.write(stream.getvalue())

			stream.close()

			return True
	

from zipfile import ZipFile
from subprocess import Popen
import hashlib
import psutil


def directory_hash(directory, ignore=[]):
	_hash_ = hashlib.sha256()
	for root, _, files in os.walk(directory):
		for file in files:
			file_path = os.path.join(root, file)
			if file_path in ignore:
				continue
			
			with open(file_path, 'rb') as f:
				while True:
					chunk = f.read(4096)
					if not chunk:
						break
					_hash_.update(chunk)


	return _hash_.hexdigest()



class Updater():
	def __init__(self, config):
		self.config = config
		self.last_versions = None
		self.downloader = Downloader()

		self._update_setup()
	
	def _update_setup(self):
		if sys.platform == 'linux':
			linux_icon_path = f'/usr/share/applications/{self.config.app_name}.desktop'
			if not os.path.exists(linux_icon_path):
				try:
					with open(linux_icon_path, 'w', encoding='utf-8') as file:
						file.write(f'[Desktop Entry]\nName={self.config.app_name}\nExec={self.config.ss14Starter_path}\nIcon={self.config.images_dir}/icon.png\nTerminal=false\nType=Application\nCategories=Application;')
				except:
					pass

		if not os.path.exists(self.config.new_version_dir) or sys.argv[0].endswith('.py'):
			return

		new_version_hash_path = os.path.join(self.config.new_version_dir, '__hash__')
		try:
			new_version_hash = quick_file_reader(new_version_hash_path)

		except:
			shutil.rmtree(self.config.new_version_dir, ignore_errors=True)
			return
		
		if new_version_hash != directory_hash(self.config.new_version_dir, ignore=[new_version_hash_path]):
			shutil.rmtree(self.config.new_version_dir, ignore_errors=True)
			return
		
		try:
			normcased_dotnet_path = os.path.normcase(self.config.dotnet_path)
			for proc in psutil.process_iter(['exe']):
				proc_path = proc.info.get('exe')
				if proc_path and os.path.normcase(proc_path) == normcased_dotnet_path:
					return
				
			os.remove(new_version_hash_path)

		except:
			return
		
		updater_content = []
		if sys.platform == 'linux':
			updater_content.append('#!/bin/bash')

		for item_name in os.listdir(self.config.current_dir):
			item_path = os.path.join(self.config.current_dir, item_name)
			if item_path in (self.config.new_version_dir,
							self.config.engines_dir,
							self.config.content_database_path,
							self.config.content_database_path + '-shm',
							self.config.content_database_path + '-wal',
							self.config.settings_path,
							self.config.backup_settings_path,
							self.config.unins000_exe,
							self.config.unins000_dat,
							self.config.local_server_dir,
							self.config.replays_dir,
							self.config.cache_dir,
							self.config.notes_dir,
							self.config.stc_model_dir):
				continue
		
			
			if sys.platform == 'win32':
				del_command = 'Remove-Item -Path "{}" -Force'
				if os.path.isdir(item_path):
					del_command += ' -Recurse'
			else:
				del_command = 'rm -'
				if os.path.isdir(item_path):
					del_command += 'r'
				del_command += 'f {}'

			updater_content.append(del_command.format(item_path))

		if sys.platform == 'win32':
			updater_content.append(f'Move-Item -Path "{self.config.new_version_dir}\*" -Destination "{self.config.current_dir}"')
			updater_content.append(f'Remove-Item -Path "{self.config.new_version_dir}" -Force -Recurse')
			updater_content.append(f'Start-Process -FilePath "{self.config.ss14Starter_path}"')
			updater_content.append('Remove-Item -Path $MyInvocation.MyCommand.Path -Force')
			updater_content.append('Exit')

		else:
			updater_content.append(f'mv {self.config.new_version_dir}/* {self.config.current_dir}')
			updater_content.append(f'rm -rf {self.config.new_version_dir}')
			updater_content.append(f'chmod +x {self.config.ss14Starter_path}')
			updater_content.append(self.config.ss14Starter_path)
			updater_content.append(f'rm -f "$0"')
			updater_content.append('exit')


		with open(self.config.new_version_updater_path, 'w') as updater_file:
			updater_file.write('\n'.join(updater_content))


		if sys.platform == 'win32':
			Popen(['start', 'powershell', '-ExecutionPolicy', 'Bypass', '-File', self.config.new_version_updater_path], shell=True)
		else:
			Popen(['bash', self.config.new_version_updater_path])

		sys.exit()

	def check_last_versions(self):
		last_versions = {}
		if last_versions_info := re2quest('GET', self.config.URLS.last_versions_info, output='text'):
			for line in last_versions_info.split('\n'):
				context, content_hash, download_url, platform, version = line.strip().split(',')

				if context == 'app':
					if platform != self.config.platform:
						continue

					last_versions[context] = {
						"version": float(version)
					}
				
				elif context == 'stc_model':
					last_versions[context] = {
						"current_hash": quick_file_reader(os.path.join(self.config.stc_model_dir, '__hash__'))
					}
				
				else:
					continue

				last_versions[context]["hash"] = content_hash
				last_versions[context]["download_url"] = download_url

			self.last_versions = last_versions
								
		return self.last_versions


	def download_last_version(self, context):
		if not self.last_versions and context not in self.last_versions:
			return
		
		if not (download_url := self.last_versions[context].get('download_url')) or not (content_hash := self.last_versions[context].get('hash')):
			return
		
		if context == 'app':
			direction = self.config.new_version_dir

			self.downloader.progress_bar.set_title('launcher_downloading')

		elif context == 'stc_model':
			direction = self.config.stc_model_dir
			
			self.downloader.progress_bar.set_title('stc_model_downloading')

		else:
			return

		if os.path.exists(direction):
			shutil.rmtree(direction, ignore_errors=True)

		try:
			with TempFileContainer(self.config.temp_dir, ext='zip') as temp_file:
				if not (downloding := self.downloader.download(download_url, temp_file)):
					return
			
				with ZipFile(temp_file, 'r') as zip_file:
					os.mkdir(direction)
					zip_file.extractall(direction)
					
					if content_hash != (new_hash:=directory_hash(direction)):
						pass
					
					with open(os.path.join(direction, '__hash__'), 'w') as hash_file:
						hash_file.write(content_hash)

					return True
		except:
			shutil.rmtree(direction, ignore_errors=True)

		finally:
			shutil.rmtree(self.config.temp_dir, ignore_errors=True)
			
			self.downloader.cancellation_token.reset()

			self.downloader.progress_bar.hide()

			


from bs4 import BeautifulSoup

def get_local_server_builds_data(builds_url):
	last_version_file_response = re2quest('GET', builds_url)
	if not last_version_file_response:
		return
	
	soup = BeautifulSoup(last_version_file_response.content, 'html.parser')
	
	output = {
		"hash": soup.body.select_one('span.versionNumber').get_text(strip=True),
		"builds": {}
	}
	
	for build_item in soup.body.ul.find_all('a'):
		build_platform = build_item.get_text(strip=True).lower()
		url = build_item["href"]
		if url.startswith('/'):
			parsed_last_version_file_response_url = parse.urlparse(last_version_file_response.url)
			url = f'{parsed_last_version_file_response_url.scheme}://{parsed_last_version_file_response_url.netloc}{url}'

		output["builds"][build_platform] = url

	return output



def serialize_cvars(name, *cvars):
	serialized_cvars = []
	for key, value in cvars:
		serialized_cvars.extend(['--cvar', f'{name}.{key}={value}'])

	return serialized_cvars


def string_to_md5(string):
	return hashlib.md5(string.encode('utf-8')).hexdigest()

