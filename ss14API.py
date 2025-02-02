
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
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

from models import database_proxy, ContentVersion, Content, ContentManifest, DatabseInfo, tables
from utils import split_list, int_from_4_bytes, catch_disconnect_line, get_local_server_builds_data, serialize_cvars, string_to_md5, TempFileContainer, Downloader, re2quest

from __main__ import logger


class ss14Api():
	def __init__(self, config, settings, window, cancellation_token, progress_bar, downloader):
		self.config = config
		self.settings = settings
		self.window = window
		
		self.LOADING = False

		self.cancellation_token = cancellation_token
		self.progress_bar = progress_bar
		self.downloader = downloader

		self._init_database()


	def _init_database(self):
		_new_database = True
		if os.path.exists(self.config.content_database_path):
			_new_database = False

		self.db = SqliteDatabase(self.config.content_database_path, thread_safe=False, check_same_thread=False)

		database_proxy.initialize(self.db)
		self.db.create_tables(tables)

		if _new_database:
			DatabseInfo.create(Created=datetime.now())

		elif not DatabseInfo.get_or_none(): # or _database_info.Created < datetime(2024, 1, 10).timestamp():
			self.db.close()

			try: os.remove(self.config.content_database_path)
			except: pass

			return self._init_database()

		self.db.pragma('journal_mode', 'WAL')


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
		return re2quest('POST', self.config.URLS.refresh_token, output='json', json=dict(token=token))

	def sign_in(self, sign_in_data):
		return re2quest('POST', self.config.URLS.sign_in, output='json', json=sign_in_data)

	def load_server_status(self, address):
		api_address = self._get_server_api_address(address)
		return re2quest('GET', f'{api_address}/status', self.cancellation_token, output='json')

	def load_server_info(self, address, added):
		server_api_address = self._get_server_api_address(address)

		server_info = re2quest('GET', f'{server_api_address}/info', self.cancellation_token, output='json')
		if not added:
			if not server_info:
				server_info = re2quest('GET', f'{self.config.URLS.server_info}?url={address}', self.cancellation_token, output='json')
				
			# if not server_info:
			# 	server_info = re2quest('GET', f'{self.config.URLS.multiverse_hub_server_info}?url={address}', self.cancellation_token, output='json')

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
		servers = re2quest('GET', self.config.URLS.servers, output='json', retries=2) or []
		# if self.settings.get('multiverse_hub'):
		# 	multiverse_hub_servers = re2quest('GET', self.config.URLS.multiverse_hub_servers, output='json', retries=2) or []
		# 	for server in multiverse_hub_servers:
		# 		if not next((i for i in servers if i.get('address') == server.get('address')), None):
		# 			servers.append(server)

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
		builds_manifest = re2quest('GET', self.config.URLS.robust_builds_manifest, self.cancellation_token, output='json')
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
		self.progress_bar.set_title('engine_preparation')

		if not os.path.exists(self.config.engines_dir):
			os.mkdir(self.config.engines_dir)

		engine_path = os.path.join(self.config.engines_dir, f'{engine_version}.zip')
		if not os.path.exists(engine_path):
			self.progress_bar.set_title('downloading_engine')

			with TempFileContainer(self.config.temp_dir, ext='zip') as temp_file:
				if not (result := self.downloader.download(platform_build_engine.get('url'), temp_file)):
					if result == None:
						raise LoadingCancelled()
					
					raise Exception('unable_to_download_engine')
				
				os.replace(temp_file, engine_path)

		return engine_path

	def _download_content_archive(self, download_url, file_path):
		self.progress_bar.set_title('downloading_content_archive')

		if not (result := self.downloader.download(download_url, file_path, parts=1)):
			if result == None:
				raise LoadingCancelled()
			
			raise ErrorWhileDownloading()

	def _collect_content_archive(self, content_version, file_path):
		self.progress_bar.set_title('building_manifest')
		
		with ZipFile(file_path, 'r') as zip_file:
			zip_file_namelist = [name for name in zip_file.namelist() if not name.endswith('/')]

			with ContentManifest.buffer() as content_manifest_buffer:
				for content_item_path in zip_file_namelist:
					self.progress_bar.add_progress(100 / len(zip_file_namelist))

					if self.cancellation_token.condition:
						raise LoadingCancelled()
					
					file_data = zip_file.read(content_item_path)
					content_hash = hashlib.blake2b(file_data, digest_size=32).digest()
					
					content = Content.create(Hash=content_hash, Size=len(file_data), Data=file_data)
					content_manifest_buffer.insert(VersionId=content_version.Id, Path=content_item_path, ContentId=content.Id)

	
	def _collect_content_files(self, content_version, manifest):
		self.progress_bar.set_title('collecting_content_files')

		source_content_version = ContentVersion.select(
		).where(
			(ContentVersion.Hash == content_version.Hash) & (ContentVersion.Id != content_version.Id)
		).order_by(
			ContentVersion.ForkVersion.desc(),
			ContentVersion.ForkId.desc()
		).get_or_none()

		if not source_content_version and content_version.ZipHash:
			source_content_version = ContentVersion.select(
			).where(
				(ContentVersion.ZipHash == content_version.ZipHash) & (ContentVersion.Id != content_version.Id)
			).order_by(
				ContentVersion.ForkVersion.desc(),
				ContentVersion.ForkId.desc()
			).get_or_none()
			
		if source_content_version:
			source_content_manifest_count = source_content_version.content_manifest.count()

			offset = 0
			limit = 999
			while offset < source_content_manifest_count:
				source_content_manifest_part = source_content_version.content_manifest.offset(offset).limit(limit)
				ContentManifest.insert_many([{'VersionId': content_version.Id, 'Path': i.Path, 'ContentId': i.ContentId} for i in source_content_manifest_part]).execute()
				offset += limit

				self.progress_bar.add_progress(100 / (source_content_manifest_count / limit))

			return True

		if self.settings.get('traffic_economy'):
			missing_manifest = []

			sub_manifests = split_list(manifest, max_size=999)
			
			with ContentManifest.buffer() as content_manifest_buffer:
				for sub_manifest in sub_manifests:
					self.progress_bar.add_progress(100 / len(sub_manifests))

					content_hashes = [i[1] for i in sub_manifest]
					paths = [i[2] for i in sub_manifest]

					if self.cancellation_token.condition:
						raise LoadingCancelled()
					
					contents = Content.select().where(Content.Hash.in_(content_hashes))
					contents_manifest = ContentManifest.select().where(
						(ContentManifest.Path.in_(paths)) &
						(ContentManifest.ContentId.in_([c.Id for c in contents]))
					)
					
					for index, content_hash, content_item_path in sub_manifest:
						matching_contents_manifest = [cm.ContentId for cm in contents_manifest if content_item_path == cm.Path]

						matching_contents = [c for c in contents if content_hash == c.Hash and c.Id in matching_contents_manifest]
						if not len(matching_contents):
							missing_manifest.append((index, content_hash, content_item_path))
							continue

						content_manifest_buffer.insert(
							VersionId=content_version.Id,
							Path=content_item_path,
							ContentId=matching_contents[0].Id
						)
			
			return missing_manifest if len(missing_manifest) else True
		

		
		

	def _download_content_files(self, manifest_download_url, missing_manifest, content_version_id, parts=20):
		self.progress_bar.set_title('downloading_content_files')

		found_manifest_indexes = []
		download_failed = False

		session = requests.Session()
		session.headers.update({
			"X-Robust-Download-Protocol": '1',
			"Accept-Encoding": 'zstd',
			"Content-Type": 'application/octet-stream'
		})


		def stream_shredder(missing_manifest_part):
			nonlocal found_manifest_indexes, download_failed

			if self.cancellation_token.condition:
				return
			
			data = bytearray().join([i[0].to_bytes(4, byteorder='little') for i in missing_manifest_part])
			response = re2quest('POST', manifest_download_url, self.cancellation_token, stream=True, retries=10, session=session, data=data)
			if not response:
				download_failed = True
				return

			stream = BytesIO()
			for chunk in response.iter_content(chunk_size=1024 * 128):
				if not chunk or self.cancellation_token.condition:
					if not chunk:
						download_failed = True

					stream.close()
					return

				stream.write(chunk)
			
			stream.seek(0)
			if response.headers.get('Content-Encoding') == 'zstd':
				stream = BytesIO(zstd.decompress(stream.getvalue()))

			is_compressed = int_from_4_bytes(stream.read(4))
			for content_index, content_hash, content_item_path, content in missing_manifest_part:
				if self.cancellation_token.condition:
					stream.close()
					return
		
				length = int_from_4_bytes(stream.read(4))
				if is_compressed and (compressed_length := int_from_4_bytes(stream.read(4))):
					file_data = zstd.decompress(stream.read(compressed_length))

				else:
					file_data = stream.read(length)
				
				found_manifest_indexes.append(content_index)

				content.Data = file_data
				content.Size = len(file_data)
				content.save()

			stream.close()

			self.progress_bar.add_progress(100 / parts)


		with ThreadPoolExecutor(max_workers=5) as executor:
			for missing_manifest_part in split_list(missing_manifest, num_splits=parts):
				if self.cancellation_token.condition:
					break

				with ContentManifest.buffer() as content_manifest_buffer:
					for part_content_index, (content_index, content_hash, content_item_path) in enumerate(missing_manifest_part):
						content = Content.create(Hash=content_hash)
						missing_manifest_part[part_content_index] = (content_index, content_hash, content_item_path, content)

						content_manifest_buffer.insert(VersionId=content_version_id, Path=content_item_path, ContentId=content.Id)
				
				executor.submit(stream_shredder, missing_manifest_part)

		if self.cancellation_token.condition:
			raise LoadingCancelled()
		
		if download_failed:
			raise ErrorWhileDownloading()

		return [x for x in missing_manifest if x[0] not in found_manifest_indexes]

	def _get_content_version(self, build, engine_version):
		self.progress_bar.set_title('preparing_content')

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
			raw_manifest = re2quest('GET', manifest_url, self.cancellation_token, 'content')
			if raw_manifest:
				lined_manifest = raw_manifest.decode('utf-8').split('\n')
				if lined_manifest.pop(0) != 'Robust Content Manifest 1':
					raise Exception('unknown_manifest_header')
				splitted_manifest = [i.split() for i in lined_manifest if len(i)]
				manifest = [(i, bytes.fromhex(c[0]), ' '.join(c[1:])) for i, c in enumerate(splitted_manifest)]

		if not len(manifest):
			with TempFileContainer(self.config.temp_dir, ext='zip') as temp_file:
				self._download_content_archive(download_url, temp_file)
				self._collect_content_archive(content_version, temp_file)

			return content_version

		if Content.select().exists():
			collection_result = self._collect_content_files(content_version, manifest)
			if collection_result == True:
				return content_version
			
			if type(collection_result) == list:
				manifest = collection_result

		if manifest_download_url:
			self._download_content_files(manifest_download_url, manifest, content_version.Id)

		return content_version

	def _cleaning_old_data(self):
		old_content_versions = ContentVersion.select().where(
			ContentVersion.LastUsed < datetime.now() - timedelta(weeks=1)
			)
		
		for old_content_version in old_content_versions:
			ContentManifest.delete().where(ContentManifest.VersionId == old_content_version.Id).execute()

			Content.delete().where(~Content.Id.in_(ContentManifest.select(ContentManifest.ContentId))).execute()

			if not ContentVersion.select().where(ContentVersion.EngineVersion == old_content_version.EngineVersion, ContentVersion.Id != old_content_version.Id).exists():
				old_engine_path = os.path.join(self.config.engines_dir, f'{old_content_version.EngineVersion}.zip')
				if os.path.exists(old_engine_path):
					try: os.remove(old_engine_path)
					except: pass

			old_content_version.delete_instance()
	
	def _get_replay_content_version(self, content_version, replay_path):
		self.progress_bar.set_title('preparing_replay_data')

		zip_hash = hashlib.sha256()
		with open(replay_path, 'rb') as replay_file:
			for byte_block in iter(lambda: replay_file.read(4096), b''):
				if self.cancellation_token.condition:
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
			for content_manifest_item in content_version.content_manifest:
				self.progress_bar.add_progress(100 / content_manifest_lenght)

				if self.cancellation_token.condition:
					raise LoadingCancelled()
				
				content_manifest_buffer.insert(VersionId=replay_content_version.Id, Path=content_manifest_item.Path, ContentId=content_manifest_item.ContentId)


			with ZipFile(replay_path, 'r') as zip_file:
				zip_file_namelist = zip_file.namelist()
				for content_item_path in zip_file_namelist:
					self.progress_bar.add_progress(100 / len(zip_file_namelist))

					if self.cancellation_token.condition:
						raise LoadingCancelled()
					
					file_data = zip_file.read(content_item_path)
					content_hash = hashlib.blake2b(file_data, digest_size=32).digest()

					content = Content.create(Hash=content_hash, Size=len(file_data), Data=file_data)
					content_manifest_buffer.insert(VersionId=replay_content_version.Id, Path=content_item_path, ContentId=content.Id)

		return replay_content_version
	
	def _start_preparation(self, engine_version, build, is_favorite_or_added=None, server_address=None, server_info=None, account_data=None, replay_path=None):
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
				self.progress_bar.set_title('connecting', False)

				auth = server_info.get('auth')

				command += [
					'--launcher',
					'--connect-address', server_info.get('connect_address'),
					'--ss14-address', f'{server_address}'
					]

				if account_data:
					if is_favorite_or_added:
						command[-1] += '#' + account_data.get('userId')

					command += [
						'--username', account_data.get('username')
						]

				command += serialize_cvars('build', *list(build.items()))

			elif replay_path:
				content_version = self._get_replay_content_version(content_version, replay_path)
				
				self.progress_bar.set_title('loading_replay', False)

				launch_cvars.append(('content_bundle', 'true'))

			else:
				raise


		command += serialize_cvars('launch', *launch_cvars)
		command += serialize_cvars('replay', ('directory', os.path.abspath(self.config.replays_dir).replace("\\", "/")))
		command += serialize_cvars('display', ('compat', 'true' if self.settings.get('compat_mode') else 'false'))

		# environs
		os.environ["SS14_LAUNCHER_PATH"] = self.config.ss14Starter_path
		os.environ["SS14_LOADER_CONTENT_DB"] = self.config.content_database_path
		os.environ["SS14_LOADER_CONTENT_VERSION"] = str(content_version)

		os.environ["DOTNET_MULTILEVEL_LOOKUP"] = '0'
		os.environ["DOTNET_TieredPGO"] = '1'
		# os.environ["DOTNET_TC_QuickJitForLoops"] = '1'
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
					if (self.settings.get('priority_for_account_connection') and auth_mode == self.config.auth_modes[0]) or auth_mode == self.config.auth_modes[1]:
						auth_token = account_data.get('token')
						if not auth_token:
							raise Exception('authentication_token_is_outdated')

						robust_auth_values = [
							auth_token,
							account_data.get('userId'),
							self.config.URLS.auth + '/'
						]

						# тест прокси
						# if True:
						# 	local_port = self.settings.get('port')
						# 	robust_auth_values[2] = self.config.URLS.localhost_address_template.format(local_port) + 'proxy_auth/'

						for index, key in enumerate(robust_auth_keys):
							os.environ[key] = robust_auth_values[index]

				elif auth_mode == self.config.auth_modes[1]:
					raise Exception('authentication_required')

					

		if self.config.platform == 'linux':
			os.environ["GLIBC_TUNABLES"] = 'glibc.rtld.dynamic_sort=1'
		
		return command

	def _start_game_process(self, command, timeout=1):
		self._cleaning_old_data()

		self._db_vacuum_and_close()

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
					
					time.sleep(1)
					
					self.window.evaluate_js(f'ss14starter.log("{exception}", "error");')
					self.window.evaluate_js(f'ss14starter.notification("{exception}", "danger")')
					
					if rollback:
						try: self.db.rollback()
						except: pass

				finally:
					shutil.rmtree(self.config.temp_dir, ignore_errors=True)
					
					self.progress_bar.hide()

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
		
		self.progress_bar.set_title('preparing_to_connect')
		
		server_info = self.load_server_info(server_address, is_added)
		if not server_info:
			raise Exception('unable_to_load_server_information')

		build = server_info.get('build')
		if not build: raise Exception('unable_to_get_build')
		
		engine_version = build.get('engine_version')
		if not engine_version: raise Exception('unable_to_get_engine_version')
		
		command = self._start_preparation(engine_version, build, (is_favorite or is_added), server_address, server_info, account_data)

		if self.cancellation_token.condition:
			raise LoadingCancelled()
		
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

		self.progress_bar.set_title('preparing_to_load_replay')

		meta_data = json.loads(raw_meta_data.read())
		if not len(meta_data): raise Exception('replay_metadata_is_empty')
		
		engine_version = meta_data.get('engine_version')
		if not engine_version: raise Exception('unable_to_get_engine_version')

		build = meta_data.get('base_build')
		if not build: raise Exception('unable_to_get_build')

		command = self._start_preparation(engine_version, build, replay_path=replay_path)
		
		if self.cancellation_token.condition:
			raise LoadingCancelled()
		
		self.progress_bar.set_title('loading_replay')

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
	
	def _db_vacuum_and_close(self):
		if not os.path.exists(self.config.new_version_dir):
			self.db.execute_sql('VACUUM')
			self.db.close()

	def clear_content_data(self):
		for table in tables:
			table.delete().execute()

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

		self.progress_bar.set_title('checking_local_server')

		local_server_builds_data = get_local_server_builds_data(self.config.URLS.local_server_builds[build_name])
		if not local_server_builds_data:
			return
		
		current_hash = None
		current_hash_file_path = os.path.join(self.config.local_server_dir, '__hash__')
		if os.path.exists(current_hash_file_path):
			with open(current_hash_file_path, 'r', encoding='utf-8') as f:
				current_hash = f.read()

		return current_hash, local_server_builds_data
	
	@_loading_wrapper()
	def download_local_server(self, url, _hash_):
		self.progress_bar.set_title('downloading_local_server')

		with TempFileContainer(self.config.temp_dir, ext='zip') as temp_file:
			if not (result := self.downloader.download(url, temp_file)):
				if result == None:
					raise LoadingCancelled()
				
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
		
		with open(self.config.os.path.join(self.config.local_server_dir, '__hash__'), 'w', encoding='utf-8') as f:
			f.write(_hash_)

		return True
	

	def start_local_server(self):
		if not os.path.exists(self.config.local_server_path):
			return
		
		command = [
			self.config.dotnet_path,
			'--roll-forward', 'Major', # просто игра на dotnet 9, а сервер на dotnet 8
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
		if not os.path.exists(self.config.local_server_dir):
			os.mkdir(self.config.local_server_dir)

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

class ErrorWhileDownloading(Exception):
	def __init__(self, message="error_while_downloading"):
		self.message = message
		super().__init__(self.message)
