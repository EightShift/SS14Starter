import os
import sys
import time
import zstd
import json
from zipfile import ZipFile, BadZipFile
from urllib.parse import urlparse
from peewee import SqliteDatabase
import shutil
import hashlib
from datetime import datetime, timedelta
import requests
import subprocess
from threading import Thread

from models import database_proxy, ContentVersion, Content, ContentManifest, tables
from utils import split_list, int_from_4_bytes, catch_disconnect_line, get_local_server_builds_data, serialize_cvars, string_to_md5, TempFileContainer, CancelationToken


from __main__ import logger


class ss14Api():
	def __init__(self, config, window, settings):
		self.config = config
		self.window = window
		self.settings = settings
		
		self.LOADING = False

		self.cancellation_token = CancelationToken()

		self.db = SqliteDatabase(self.config.content_database_path)
		database_proxy.initialize(self.db)

		self.db.create_tables(tables)

		# Миграция ZipHash. Потому-что я в прошлом был ленивой жопой. Через какое-то количество версий это, наверное, можно будет убрать
		if not ContentVersion.ZipHash.name in [i.name for i in self.db.get_columns(ContentVersion._meta.name)]:
			from playhouse.migrate import SqliteMigrator, migrate

			migrator = SqliteMigrator(self.db)
			migrate(
				migrator.add_column(ContentVersion._meta.name, ContentVersion.ZipHash.name, ContentVersion.ZipHash)
			)

		self.db.pragma('journal_mode', 'WAL')

	def JS_LP(self, **kwargs):
		self.window.evaluate_js(f'ss14starter.loading_process({kwargs});')

	def _request(self, method, url, retries=32, output=None, **kwargs):
		params = {
			"stream": True,
			"timeout": 5,
			"allow_redirects": True
		}

		params.update(kwargs)

		while retries:
			if self.cancellation_token.status:
				raise LoadingCancelled()
			
			try:
				response = requests.request(method, url, **params)
				if response.status_code != 200:
					raise

				if output == 'json':
					response = response.json()
				elif output == 'text':
					response = response.text
				elif output == 'content':
					response = response.content
					
				return response

			except:
				retries -= 1

		return None

	def _download(self, url, file_path, method='GET', **kwargs):
		response = self._request(method, url, **kwargs)
		if not response:
			return None
		
		file_size = int(response.headers.get("Content-Length", 0))
		
		with open(file_path, "wb") as f:
			for chunk in response.iter_content(1024):
				if file_size > 0: self.JS_LP(progress=f.tell() * 100 / file_size)
				if self.cancellation_token.status:
					raise LoadingCancelled()
				
				f.write(chunk)

		return response

	def _parse_ss14_uri(self, address):
		ss14_url = urlparse(address)

		if not ss14_url.scheme:
			ss14_url = ss14_url._replace(scheme=list(self.config.ss14_schemes.keys())[0])

		if ss14_url.scheme not in self.config.ss14_schemes or not ss14_url.netloc:
			return None

		return ss14_url.geturl()

	def _get_server_api_address(self, address):
		address = urlparse(address)

		ss14_scheme = self.config.ss14_schemes[address.scheme or 'ss14']
		address = address._replace(scheme=ss14_scheme["scheme"])

		if not address.netloc:
			address = address._replace(netloc='localhost')

		if not address.port:
			address = address._replace(netloc=f'{address.hostname}:{ss14_scheme["port"]}')

		address = address.geturl()
		if address.endswith('/'):
			address = address[:-1]

		return address

	def _cache(self, *args, **kwargs):
		caching = self.settings.get('caching')
		if caching == False:
			return None
		
		if not os.path.exists(self.config.cache_dir):
			os.mkdir(self.config.cache_dir)
		
		for file_name, data in kwargs.items():
			cache_path = os.path.join(self.config.cache_dir, f'{file_name}.json')
			try:
				with open(cache_path, 'w', encoding='utf-8') as cache_file:
					json.dump(data, cache_file)
			except:
				pass

		cached_data_list = []
		for file_name in args:
			cache_path = os.path.join(self.config.cache_dir, f'{file_name}.json')
			cached_data = None
			try:
				with open(cache_path, 'r', encoding='utf-8') as cache_file:
					cached_data = json.load(cache_file)
			except:
				pass

			cached_data_list.append(cached_data)

		if len(cached_data_list) == 0:
			return None
		
		if len(cached_data_list) == 1:
			return cached_data_list[0]

		return cached_data_list

	def refresh_token(self, token):
		return self._request('POST', self.config.URLS.refresh_token, retries=1, output='json', json=dict(token=token))

	def sign_in(self, sign_in_data):
		return self._request('POST', self.config.URLS.sign_in, retries=1, output='json', json=sign_in_data)

	def load_server_status(self, address):
		api_address = self._get_server_api_address(address)
		return self._request('GET', f'{api_address}/status', output='json', retries=2)

	def load_server_info(self, address, added):
		server_api_address = self._get_server_api_address(address)

		server_info = self._request('GET', f'{server_api_address}/info', output='json', retries=2)
		if not added:
			if not server_info:
				server_info = self._request('GET', f'{self.config.URLS.server_info}?url={address}', output='json', retries=2)
				
			if not server_info:
				server_info = self._request('GET', f'{self.config.URLS.multiverse_hub_server_info}?url={address}', output='json', retries=2)

		info_cache_file_name = f'server_info-{string_to_md5(address)}'

		if not server_info:
			server_info = self._cache(info_cache_file_name)
			if server_info:
				return server_info
			else:
				return None
	
		if not server_info.get('connect_address'):
			server_info["connect_address"] = urlparse(server_api_address)._replace(scheme='udp').geturl()

		build = server_info.get('build', {})

		azs = build.get('acz')
		if (azs or 'download_url' not in build):
			build['download_url'] = f'{server_api_address}/client.zip'

			if azs:
				build["manifest_url"] = f'{server_api_address}/manifest.txt'
				build["manifest_download_url"] = f'{server_api_address}/download'

		server_info["build"] = build
		
		self._cache(**{info_cache_file_name:server_info})

		return server_info

	def load_servers(self):
		servers = self._request('GET', self.config.URLS.servers, output='json') or []

		if self.settings.get('multiverse_hub'):
			multiverse_hub_servers = self._request('GET', self.config.URLS.multiverse_hub_servers, output='json') or []
			for server in multiverse_hub_servers:
				if not next((i for i in servers if i.get('address') == server.get('address')), None):
					servers.append(server)

		if len(servers):
			self._cache(servers=servers)
		else:
			servers = self._cache('servers')

		if not len(servers):
			return

		server_index = 0
		while server_index != len(servers) - 1:
			address = self._parse_ss14_uri(servers[server_index]["address"])
			if not address:
				del servers[server_index]
				continue

			servers[server_index]["address"] = address
			server_index += 1

		return servers

	def _get_platform_build_engine(self, engine_version):
		builds_manifest = self._request('GET', self.config.URLS.robust_builds_manifest, output='json')
		if builds_manifest:
			self._cache(builds_manifest=builds_manifest)
		else:
			builds_manifest = self._cache('builds_manifest')

		if not builds_manifest:
			raise Exception('unable_to_load_builds_manifest')

		build_engine = builds_manifest.get(engine_version)
		if not engine_version:
			raise Exception('unable_to_get_build_engine')

		platform_key = 'win-x64'

		################################

		platform_build_engine = build_engine["platforms"].get(platform_key)
		if not platform_build_engine:
			raise Exception('unable_to_get_platform_build_engine')

		return platform_build_engine

	def _get_engine_path(self, engine_version, platform_build_engine):
		self.JS_LP(title='engine_preparation', progress=0)

		if not os.path.exists(self.config.engines_dir):
			os.mkdir(self.config.engines_dir)

		engine_path = os.path.join(self.config.engines_dir, f'{engine_version}.zip')
		if not os.path.exists(engine_path):
			self.JS_LP(title='downloading_engine')

			with TempFileContainer(self.config.temp_dir, ext='zip') as temp_file:
				if not self._download(platform_build_engine.get('url'), temp_file):
					raise Exception('unable_to_download_engine')
				
				os.replace(temp_file, engine_path)

		return engine_path

	def _download_content_archive(self, download_url, file_path):
		self.JS_LP(title='downloading_content_archive', progress=0)
		if not self._download(download_url, file_path):
			raise UnableToDownloadContent()

	def _build_manifest(self, file_path):
		self.JS_LP(title='building_manifest', progress=0)

		with ZipFile(file_path, 'r') as zip_file:
			zip_file_namelist = zip_file.namelist()
			
			manifest = []
			for index, content_item_path in enumerate(zip_file_namelist):
				self.JS_LP(progress=index * 100 / len(zip_file_namelist))
				if self.cancellation_token.status:
					raise LoadingCancelled()
				
				file_data = zip_file.read(content_item_path)
				content_hash = hashlib.blake2b(file_data, digest_size=32).digest()
				
				manifest.append((index, content_hash, content_item_path))

			return manifest
	
	def _collect_content_files(self, content_version, manifest):
		self.JS_LP(title='collecting_content', progress=0)

		missing_manifest = []

		with ContentManifest.buffer() as content_manifest_buffer:
			sub_manifests = split_list(manifest, max_size=999)
			for sub_manifest_index, sub_manifest in enumerate(sub_manifests):
				self.JS_LP(progress=sub_manifest_index * 100 / len(sub_manifests))
				if self.cancellation_token.status:
					raise LoadingCancelled()
				
				contents = Content.select().where(Content.Hash.in_([i[1] for i in sub_manifest]))
				contents_manifest = ContentManifest.select().where(ContentManifest.Path.in_([i[2] for i in sub_manifest]) & ContentManifest.ContentId.in_([i.Id for i in contents]))
				
				for index, content_hash, content_item_path in sub_manifest:
					_contents_manifest = [cm.ContentId for cm in contents_manifest if content_item_path == cm.Path]
					_contents = [c for c in contents if content_hash == c.Hash and c.Id in _contents_manifest]
					if not len(_contents):
						missing_manifest.append((index, content_hash, content_item_path))
						continue
					
					content_manifest_buffer.insert(VersionId=content_version.Id, Path=content_item_path, ContentId=_contents[0].Id)
			
		return missing_manifest

	def _download_missing_content_files(self, manifest_download_url, missing_manifest, content_version_id):
		self.JS_LP(title='downloading_missing_content_files', progress=0)
		
		robust_download_protocol_headers = {
			"X-Robust-Download-Protocol": '1',
			"Accept-Encoding": 'zstd',
			"Content-Type": 'application/octet-stream'
		}
		
		found_manifest_indexes = []

		splited_missing_manifest = split_list(missing_manifest, num_splits=20)
		splited_missing_manifest.reverse() # Потому что первые файлы очень объёмные, а смотреть на пустой прогресс-бар скучно

		for part_index, part_missing_manifest in enumerate(splited_missing_manifest):
			self.JS_LP(progress=part_index * 100 / len(splited_missing_manifest))
			if self.cancellation_token.status:
				raise LoadingCancelled()
			
			part_missing_manifest_bytearray = bytearray().join([i[0].to_bytes(4, byteorder='little') for i in part_missing_manifest])
			with TempFileContainer(self.config.temp_dir) as temp_file:
				response = self._download(manifest_download_url, temp_file, method='POST', data=part_missing_manifest_bytearray, headers=robust_download_protocol_headers)
				if not response:
					break

				with open(temp_file, 'rb') as missing_content_files:
					stream = missing_content_files.read()

					if response.headers.get('Content-Encoding') == 'zstd':
						print('СУКА БЛЯТЬ КАКАЯ-ТО ХУЙНЯ С ZSTD!')
						stream = zstd.decompress(stream)

					is_compressed = int_from_4_bytes(stream[:4])
					stream = stream[4:]
					
					with ContentManifest.buffer() as content_manifest_buffer:
						for index, content_hash, content_item_path in part_missing_manifest:
							if self.cancellation_token.status:
								raise LoadingCancelled()
					
							length = int_from_4_bytes(stream[:4])
							stream = stream[4:]

							if is_compressed:
								compressed_length = int_from_4_bytes(stream[:4])
								stream = stream[4:]
								
								if compressed_length > 0:
									file_data = zstd.decompress(stream[:compressed_length])
									length = compressed_length
								else:
									file_data = stream[:length]
							else:
								file_data = stream[:length]

							stream = stream[length:]
							
							found_manifest_indexes.append(index)

							content = Content.create(Hash=content_hash, Size=len(file_data), Data=file_data)
							content_manifest_buffer.insert(VersionId=content_version_id, Path=content_item_path, ContentId=content.Id)
						
		return [x for x in missing_manifest if x[0] not in found_manifest_indexes]
	
	def _collect_missing_content_files(self, content_version, not_found_manifest, file_path):
		self.JS_LP(title='collecting_missing_content_files', progress=0)

		with ZipFile(file_path, 'r') as zip_file:
			with ContentManifest.buffer() as content_manifest_buffer:
				for index, (_, content_hash, content_item_path) in enumerate(not_found_manifest):
					self.JS_LP(progress=index * 100 / len(not_found_manifest))
					if self.cancellation_token.status:
						raise LoadingCancelled()
					
					try:
						file_data = zip_file.read(content_item_path)
					except:
						raise UnableToDownloadContent()
					
					content = Content.create(Hash=content_hash, Size=len(file_data), Data=file_data)
					content_manifest_buffer.insert(VersionId=content_version.Id, Path=content_item_path, ContentId=content.Id)

	def _get_content_version(self, build, engine_version):
		self.JS_LP(title='preparing_content', progress=0)

		fork_id = build.get('fork_id')
		fork_version = build.get('version')
		_hash_ = build.get('manifest_hash') or build.get('hash')
		if _hash_:
			_hash_ = bytes.fromhex(_hash_)

		content_version = ContentVersion.select().where(
			ContentVersion.EngineVersion == engine_version,
			ContentVersion.ForkId == fork_id,
			ContentVersion.ForkVersion == fork_version,
			ContentVersion.Hash == _hash_
			).get_or_none()

		if content_version:
			if content_version.content_manifest.exists():
				content_version.LastUsed = datetime.now().date()
				content_version.save()
				
				return content_version

		else:
			content_version = ContentVersion.create(
				EngineVersion = engine_version,
				ForkId=fork_id,
				ForkVersion=fork_version,
				Hash=_hash_
				)

		download_url = build.get('download_url')
		manifest_url = build.get('manifest_url')
		manifest_download_url = build.get('manifest_download_url')

		manifest = []
		if manifest_url:
			raw_manifest = self._request('GET', manifest_url, output='text')
			if raw_manifest:
				lined_manifest = raw_manifest.split('\n')
				if lined_manifest.pop(0) != 'Robust Content Manifest 1':
					raise Exception('unknown_manifest_header')
				splitted_manifest = [i.split() for i in lined_manifest if len(i)]
				manifest = [(i, bytes.fromhex(c[0]), ' '.join(c[1:])) for i, c in enumerate(splitted_manifest)]

		with TempFileContainer(self.config.temp_dir, ext='zip') as temp_file:
			if not len(manifest):
				self._download_content_archive(download_url, temp_file)

				manifest = self._build_manifest(temp_file)

			if not len(manifest):
				raise UnableToDownloadContent()

			if Content.select().exists():
				manifest = self._collect_content_files(content_version, manifest)

			if not len(manifest):
				return content_version
			
			manifest = self._download_missing_content_files(manifest_download_url, manifest, content_version.Id)
			if not len(manifest):
				return content_version
			
			if not os.path.getsize(temp_file):
				self._download_content_archive(download_url, temp_file)

			self._collect_missing_content_files(content_version, manifest, temp_file)

			return content_version

	def _cleaning_old_data(self):
		old_content_versions = ContentVersion.select().where(
			ContentVersion.LastUsed < datetime.now() - timedelta(weeks=1)
			)
		
		if not old_content_versions.count():
			return
		
		for index, old_content_version in enumerate(old_content_versions):
			self.JS_LP(progress=index * 100 / len(old_content_versions))
			
			ContentManifest.delete().where(ContentManifest.VersionId == old_content_version.Id).execute()

			Content.delete().where(~Content.Id.in_(ContentManifest.select(ContentManifest.ContentId))).execute()

			if not ContentVersion.select().where(ContentVersion.EngineVersion == old_content_version.EngineVersion, ContentVersion.Id != old_content_version.Id).exists():
				old_engine_path = os.path.join(self.config.engines_dir, f'{old_content_version.EngineVersion}.zip')
				if os.path.exists(old_engine_path):
					try: os.remove(old_engine_path)
					except: pass

			old_content_version.delete_instance()
	
	def _get_replay_content_version(self, content_version, replay_path):
		self.JS_LP(title='preparing_replay_data', progress=0)
		
		zip_hash = hashlib.sha256()
		with open(replay_path, 'rb') as replay_file:
			for byte_block in iter(lambda: replay_file.read(4096), b''):
				if self.cancellation_token.status:
					raise LoadingCancelled()
				
				zip_hash.update(byte_block)
				
		zip_hash = zip_hash.digest()

		replay_content_version = ContentVersion.select().where(
			ContentVersion.EngineVersion == content_version.EngineVersion,
			ContentVersion.ForkId == content_version.ForkId,
			ContentVersion.ForkVersion == content_version.ForkVersion,
			ContentVersion.Hash == content_version.Hash,
			ContentVersion.ZipHash == zip_hash
			).get_or_none()
		
		if replay_content_version:
			if replay_content_version.content_manifest.exists():
				replay_content_version.LastUsed = datetime.now().date()
				replay_content_version.save()

				return replay_content_version

		else:
			replay_content_version = ContentVersion.create(
				EngineVersion = content_version.EngineVersion,
				ForkId=content_version.ForkId,
				ForkVersion=content_version.ForkVersion,
				Hash=content_version.Hash,
				ZipHash=zip_hash
				)

		with ContentManifest.buffer() as content_manifest_buffer:
			content_manifest_lenght = content_version.content_manifest.count()
			for index, content_manifest_item in enumerate(content_version.content_manifest):
				self.JS_LP(progress=index * 100 / content_manifest_lenght)
				if self.cancellation_token.status:
					raise LoadingCancelled()
				
				content_manifest_buffer.insert(VersionId=replay_content_version.Id, Path=content_manifest_item.Path, ContentId=content_manifest_item.ContentId)


			with ZipFile(replay_path, 'r') as zip_file:
				zip_file_namelist = zip_file.namelist()
				for index, content_item_path in enumerate(zip_file_namelist):
					self.JS_LP(progress=index * 100 / len(zip_file_namelist))
					if self.cancellation_token.status:
						raise LoadingCancelled()
					
					file_data = zip_file.read(content_item_path)
					content_hash = hashlib.blake2b(file_data, digest_size=32).digest()

					content = Content.create(Hash=content_hash, Size=len(file_data), Data=file_data)
					content_manifest_buffer.insert(VersionId=replay_content_version.Id, Path=content_item_path, ContentId=content.Id)

		return replay_content_version
	
	def _start_preparation(self, engine_version, build, server_address=None, server_info=None, account_data=None, replay_path=None):
		with self.db.atomic():
			platform_build_engine = self._get_platform_build_engine(engine_version)
			engine_path = self._get_engine_path(engine_version, platform_build_engine)

			content_version = self._get_content_version(build, engine_version)
			
			command = [
					self.config.dotnet_path,
					self.config.loader_path,
					engine_path,
					platform_build_engine.get('sig'),
					self.config.signing_key_path
				]

			auth = None

			launch_cvars = [('launcher', 'true')]
			if all((server_address, server_info)):
				self.JS_LP(title='connecting')

				auth = server_info.get('auth')

				command += [
					'--launcher',
					'--connect-address',
					server_info.get('connect_address'),
					'--ss14-address',
					f'{server_address}'
					]

				if account_data:
					command[-1] += '#' + account_data.get('userId')
					command += [
						'--username', account_data.get('username')
						]

				command += serialize_cvars('build', *list(build.items()))

			elif replay_path:
				content_version = self._get_replay_content_version(content_version, replay_path)
				
				self.JS_LP(title='loading_replay')

				launch_cvars.append(('content_bundle', 'true'))

			else:
				raise

			self._cleaning_old_data()

		command += serialize_cvars('launch', *launch_cvars)
		command += serialize_cvars('replay', ('directory', self.config.replays_dir.replace("\\", "/")))
		command += serialize_cvars('display', ('compat', 'true' if self.settings.get('compat_mode') else 'false'))


		# environs

		os.environ["SS14_LAUNCHER_PATH"] = self.config.ss14Starter_path
		os.environ["SS14_LOADER_CONTENT_DB"] = self.config.content_database_path
		os.environ["SS14_LOADER_CONTENT_VERSION"] = str(content_version)

		os.environ["DOTNET_MULTILEVEL_LOOKUP"] = '0'
		os.environ["DOTNET_TieredPGO"] = '1'
		os.environ["DOTNET_TC_QuickJitForLoops"] = '1'
		os.environ["DOTNET_ReadyToRun"] = '0'

		robust_auth_keys = [
			'ROBUST_AUTH_TOKEN',
			'ROBUST_AUTH_USERID',
			'ROBUST_AUTH_SERVER'
		]
		
		robust_auth_public_key = 'ROBUST_AUTH_PUBKEY'

		for key in robust_auth_keys + [robust_auth_public_key]:
			if key in os.environ:
				del key

		if auth:
			auth_mode = auth.get('mode')

			os.environ[robust_auth_public_key] = auth.get('public_key')

			if auth_mode != self.config.auth_modes[2]:
				if account_data:
					connect_with_account_only = self.settings.get('connect_with_account_only')
					if (connect_with_account_only and auth_mode == self.config.auth_modes[0]) or auth_mode == self.config.auth_modes[1]:
						robust_auth_values = (
							account_data.get('token'),
							account_data.get('userId'),
							self.config.URLS.auth
						)
						for index, key in enumerate(robust_auth_keys):
							os.environ[key] = robust_auth_values[index]

				elif auth_mode == self.config.auth_modes[1]:
					raise Exception('authentication_required')

					

		if self.config.platform == 'linux':
			os.environ["GLIBC_TUNABLES"] = 'glibc.rtld.dynamic_sort=1'
		
		return command

	def _start_game_process(self, command, timeout=1):
		process = subprocess.Popen(command, encoding='utf-8', stdout=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if self.config.platform == 'win32' else 0)

		threshold = 0.1
		timeout_counter = 0
		while timeout_counter < timeout:
			return_code = process.poll()
			
			if return_code is not None:
				return
			
			time.sleep(threshold)
			timeout_counter += threshold

		return process

	def _loading_wrapper(rollback=False):
		def decorator(func):
			def wrapper(self, *args, **kwargs):
				if self.LOADING:
					return
					
				self.LOADING = True
				try:
					return func(self, *args, **kwargs)
				
				except Exception as exception:
					logger.debug(exception)
					
					if isinstance(exception, (requests.ConnectionError, requests.ConnectTimeout)):
						exception = 'connection_problems'
					
					elif isinstance(exception, BadZipFile):
						exception = 'bad_zip_file'

					else:
						exception = str(exception)
						
					self.window.evaluate_js(f'ss14starter.log("{exception}", "error");')
					self.window.evaluate_js(f'ss14starter.notification("{exception}", "danger")')
					
					if rollback:
						try: self.db.rollback()
						except: pass

				finally:
					shutil.rmtree(self.config.temp_dir, ignore_errors=True)

					self.JS_LP(progress=0, action='hide')

					self.LOADING = False
					self.cancellation_token.reset()

			return wrapper
		return decorator

	@_loading_wrapper(True)
	def connect_server(self, server_address, user_id):
		is_favorite = server_address in (self.settings.get('favorite_servers') or [])
		is_added = server_address in (self.settings.get('added_servers') or [])
		
		accounts = self.settings.get('accounts')
		account_data = None
		if accounts:
			account_data = next((i for i in accounts if i["userId"] == user_id), None)
			if not account_data:
				account_data = next((i for i in accounts if i["selected"]), None)
		
		self.JS_LP(action='show', title='preparing_to_connect')

		server_info = self.load_server_info(server_address, is_added)
		if not server_info:
			raise Exception('unable_to_load_server_information')
		
		build = server_info.get('build')
		if not build: raise Exception('unable_to_get_build')
		
		engine_version = build.get('engine_version')
		if not engine_version: raise Exception('unable_to_get_engine_version')

		command = self._start_preparation(engine_version, build, server_address, server_info, account_data)

		if self.cancellation_token.status:
			raise LoadingCancelled()
			
		self.JS_LP(title='connecting')
		
		process = self._start_game_process(command)
		if process and self.settings.get('reconnect_to_favorite') and (is_favorite or is_added):
			Thread(target=self.pipe_reader, args=[process, server_address, user_id], daemon=True).start()

	def pipe_reader(self, process, server_address, user_id):
		while True:
			line = process.stdout.readline()
			if not line:
				break

			if self.config.debug:
				try: self.window.evaluate_js(f'ss14starter.log("{line.strip()}");')
				except: pass

			match catch_disconnect_line(line):
				case True:
					time.sleep(14.5)

				case None:
					continue

				
			if self.LOADING:
				continue
		
			process.terminate()

			self.connect_server(server_address, user_id)

		process.stdout.close()

	def _get_replay_path(self, replay_name):
		replay_path = os.path.join(self.config.replays_dir, f'{replay_name}.zip')
		if not os.path.exists(replay_path):
			return
		
		return replay_path

	@_loading_wrapper(True)
	def start_replay(self, replay_name):
		replay_path = self._get_replay_path(replay_name)
		if not replay_path:
			return

		with ZipFile(replay_path, 'r') as zip_file:
			raw_meta_data = zip_file.open("rt_content_bundle.json")
			if not raw_meta_data: raise Exception('replay_has_no_metadata')

		self.JS_LP(action='show', title='preparing_to_load_replay')

		meta_data = json.loads(raw_meta_data.read())
		if not len(meta_data): raise Exception('replay_metadata_is_empty')
		
		engine_version = meta_data.get('engine_version')
		if not engine_version: raise Exception('unable_to_get_engine_version')

		build = meta_data.get('base_build')
		if not build: raise Exception('unable_to_get_build')

		command = self._start_preparation(engine_version, build, replay_path=replay_path)
		
		if self.cancellation_token.status:
			raise LoadingCancelled()
		
		self.JS_LP(title='loading_replay')

		self._start_game_process(command)

	def remove_replay(self, replay_name):
		replay_path = self._get_replay_path(replay_name)
		if not replay_path:
			return False
		
		try:
			os.remove(replay_path)
		except:
			return False
		
		return True

	def check_replays(self):
		if not os.path.exists(self.config.replays_dir):
			os.mkdir(self.config.replays_dir)
		
		replays = []
		for replay_name in os.listdir(self.config.replays_dir):
			if replay_name.endswith('.zip'):
				replay_path = os.path.join(self.config.replays_dir, replay_name)
				replay_data = {
					'name': os.path.splitext(replay_name)[0],
					'time': os.path.getmtime(replay_path)
				}
				
				replays.append(replay_data)

		return replays
	
	def clear_content_data(self):
		for table in tables:
			table.delete().execute()

		self.db.commit()

		self.db.execute_sql("VACUUM")

	def remove_engines(self):
		shutil.rmtree(self.config.engines_dir, ignore_errors=True)

	def open_replays_folder(self):
		subprocess.Popen(['explorer' if self.config.platform == 'win32' else 'xdg-open', self.config.replays_dir])

	@_loading_wrapper()
	def check_latest_local_server(self):
		build_name = self.settings.get('local_server_build')
		if not build_name:
			build_name = list(self.config.URLS.local_server_builds.keys())[0]
			self.settings.set(local_server_build=build_name)

		self.JS_LP(action='show', title='checking_local_server')

		local_server_builds_data = get_local_server_builds_data(self.config.URLS.local_server_builds[build_name])
		if not local_server_builds_data:
			return
		
		current_version = None
		if os.path.exists(self.config.local_server_version_path):
			with open(self.config.local_server_version_path, 'r', encoding='utf-8') as f:
				current_version = f.read()

		return current_version, local_server_builds_data
	
	@_loading_wrapper()
	def download_local_server(self, url, version):
		self.JS_LP(action='show', title='downloading_local_server')

		with TempFileContainer(self.config.temp_dir, ext='zip') as temp_file:
			if not self._download(url, temp_file):
				raise Exception('unable_to_download_local_server')
			
			if os.path.exists(self.config.local_server_dir):
				for item_name in os.listdir(self.config.local_server_dir):
					if item_name == 'data':
						continue

					item_path = os.path.join(self.config.local_server_dir, item_name)
					
					if os.path.isfile(item_path):
						os.remove(item_path)
					elif os.path.isdir(item_path):
						shutil.rmtree(item_path)
					
			else:
				os.mkdir(self.config.local_server_dir)
			
			
			with ZipFile(temp_file, 'r') as temp_zip_file:
				temp_zip_file.extractall(self.config.local_server_dir)

		with open(self.config.local_server_version_path, 'w', encoding='utf-8') as f:
			f.write(version)

		return True
	
	def cancel_loading(self):
		if self.cancellation_token.status or not self.LOADING:
			return
		
		self.JS_LP(title='canceling')

		self.cancellation_token.cancel()
		
		while self.cancellation_token.status:
			time.sleep(0.1)

	def start_local_server(self):
		if not os.path.exists(self.config.local_server_path):
			return
		
		command = [
			self.config.dotnet_path,
			self.config.local_server_path
		]

		if sys.platform == 'win32':
			subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)

		else:
			string_command = ' '.join(command)
			terminal_command = f'bash -c "{string_command}; exec bash"'

			try:
				subprocess.Popen(f'gnome-terminal -- {terminal_command}', shell=True)
			except FileNotFoundError:
				subprocess.Popen(f'xterm -e {terminal_command}', shell=True)

	def open_local_server_folder(self):
		subprocess.Popen(['explorer' if sys.platform == 'win32' else 'xdg-open', self.config.local_server_dir])

	def default_exception_handler(self, exception):
		logger.debug(exception)
		
		if isinstance(exception, (requests.ConnectionError, requests.ConnectTimeout)):
			exception = 'connection_problems'
		else:
			exception = str(exception)
			
		self.window.evaluate_js(f'ss14starter.log("{exception}", "error");')
		self.window.evaluate_js(f'ss14starter.notification("{exception}", "danger")')
		
		self.db.rollback()
		
class LoadingCancelled(Exception):
	def __init__(self, message="loading_has_been_canceled"):
		self.message = message
		super().__init__(self.message)

class UnableToDownloadContent(Exception):
	def __init__(self, message="unable_to_download_content"):
		self.message = message
		super().__init__(self.message)
