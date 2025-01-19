import sys
import webbrowser
import time

from utils import load_languages, string_to_md5, CancelationToken, ProgressBar, Downloader



class Api():
	def __init__(self, config, settings, updater, window):
		self.config = config
		self.settings = settings
		self.updater = updater
		self.window = window

		self.cancellation_token = CancelationToken()
		self.progress_bar = ProgressBar(self.window)
		self.downloader = Downloader(self.cancellation_token, self.progress_bar)

		self.updater.downloader = self.downloader

	def load_config(self):
		from ss14API import ss14Api
		from notes import Notes
		from stc import STC

		self.ss14api = ss14Api(self.config, self.settings, self.window, self.cancellation_token, self.progress_bar, self.downloader)
		self.stc = STC(self.config, self.settings, self.window)
		self.notes = Notes(self.config)
		
		return {
			"platform": self.config.platform,
			"app_name": self.config.app_name,
			"app_version": self.config.app_version,
			"local_server_builds": list(self.config.URLS.local_server_builds.keys()),
			"refresh_interval": self.config.refresh_interval,
			"long_refresh_interval": self.config.long_refresh_interval,
			"account_token_refresh_time": self.config.account_token_refresh_time
		}
	
	def close(self):
		self.cancel_operation()

		self.window.destroy()
		
		sys.exit(0)

	def minimize(self):
		self.window.minimize()

	def load_settings(self):
		return self.settings.get()

	def load_languages(self):
		return load_languages(self.config.languages_dir)
	
	def update_settings(self, new_settings):
		self.settings.set(**new_settings)

	def remove_settings(self):
		self.settings.remove()

	def load_cached_servers(self):
		return self.ss14api._cache('servers')
		
	def load_servers(self):
		return self.ss14api.load_servers()

	def load_server_status(self, address):
		return self.ss14api.load_server_status(address)
	
	def load_server_info(self, address, is_added):
		return self.ss14api.load_server_info(address, is_added)

	def load_server_cached_info(self, address):
		info_cache_file_name = f'server_info-{string_to_md5(address)}'
		return self.ss14api._cache(info_cache_file_name)

	def connect_server(self, server_address, user_id):
		return self.ss14api.connect_server(server_address, user_id)

	def cancel_operation(self):
		if self.cancellation_token.condition or not self.progress_bar.is_open():
			return

		self.cancellation_token.cancel()

		self.progress_bar.set_title('canceling')

		while self.cancellation_token.condition:
			time.sleep(0.1)

		return True

	def get_connection_status(self):
		return self.ss14api.get_connection_status()

	def sign_in(self, sign_in_data):
		return self.ss14api.sign_in(sign_in_data)

	def refresh_account_token(self, token):
		return self.ss14api.refresh_token(token)

	def open_url(self, url):
		if hasattr(self.config.URLS, url):
			url = getattr(self.config.URLS, url)

		webbrowser.open(url)

	def check_last_versions(self):
		return self.updater.check_last_versions()

	def download_last_version(self, context):
		return self.updater.download_last_version(context)

	def clear_content_data(self):
		self.ss14api.clear_content_data()

	def remove_engines(self):
		self.ss14api.remove_engines()

	def check_latest_local_server(self):
		return self.ss14api.check_latest_local_server()

	def download_local_server(self, url, version):
		return self.ss14api.download_local_server(url, version)
	
	def start_local_server(self):
		return self.ss14api.start_local_server()
	
	def open_local_server_folder(self):
		return self.ss14api.open_local_server_folder()
	
	def check_replays(self):
		return self.ss14api.check_replays()
	
	def start_replay(self, replay_name):
		return self.ss14api.start_replay(replay_name)
	
	def remove_replay(self, replay_name):
		return self.ss14api.remove_replay(replay_name)
	
	def open_replays_folder(self):
		return self.ss14api.open_replays_folder()
	
	def load_notes(self):
		return self.notes.load()

	def save_note(self, note_data):
		return self.notes.save(note_data)

	def remove_note(self, note_id):
		return self.notes.remove(note_id)

	def load_audio_input_devices(self):
		return self.stc.get_audio_input_devices()
	
	def load_default_audio_input_device(self):
		return self.stc.get_default_audio_input_device()
	
	def stc_enable(self):
		return self.stc.start()
	
	def stc_disable(self):
		return self.stc.stop()
	
	def stc_get_hotkey_names(self, keycodes):
		return self.stc.get_hotkey_names(keycodes)