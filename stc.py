import os
import psutil
import vosk
import pyaudio
import keyboard
from threading import Thread
from io import BytesIO
import time
import json
import re
import ctypes




vosk.SetLogLevel(-1)

words_replces = (
	('СБ', 'эсбэ'),
	('ГСБ', 'гээсбэ'),
	('КЗ', 'кэзэ'),
	('АВД', 'авэдэ'),
	('ГП', 'гэпэ'),
	('КПК', 'капэка'),
	('ГВ', 'гэвэ'),
	('ПДА', 'пэдэа'),
	('НР', 'энэр'),
	('НРа', 'энэра'),
	('НРу', 'энэру'),
	('СИ', 'эси'),
	('КМ', 'кээм'),
	('КМа', 'кээма'),
	('КМу', 'кээму'),
	('СРП', 'эсэрпэ'),
	('БПОЗ', 'бэпэоз'),
	('РНД', 'эрэндэ'),
	('ОБР', 'обээр'),
	('НТ', 'энтэ'),
	('ЦК', 'цэка'),
	('ПЦК', 'пэцэка'),
	('НЩЦК', 'энщецэка'),
	('ТК', 'тэка'),
	('ЛКП', 'элкапэ'),
	('СРП', 'эсэрпэ'),
	('РХБЗЗ', 'эрхабэзэзэ'),
	('ССД', 'эсэсдэ'),
	('C4', 'си четыре'),
	('ядерщики', 'яо')
)

question_words = (
	'как',
	'почему',
	'где',
	'когда',
	'кто',
	'что',
	'какой',
	'сколько',
	'неужели',
	'разве',
	'неужто',
	'в чем',
	'зачем',
	'с чего',
	'с каких пор',
	'с какой целью',
	'каким образом',
	'в каких случаях',
	'почему бы',
	'\S+ ли',
	'не \S+ бы',
	'не \S+ ли'
)

exceptions_question_words = (
    '\S+-то',
	'\S+ бы (?:\S+\s)?н\w'
)

question_words_pattern = fr'^({"|".join(question_words)})'
exceptions_question_words_pattern = fr'^({"|".join(exceptions_question_words)})'



class STC():
	def __init__(self, config, settings, window):
		self.config = config
		self.settings = settings
		self.window = window

		self.audio = pyaudio.PyAudio()

		self.chunk_size = 1024
		self.framerate = 16000
		self.audio_buffer = BytesIO()

		self.model = None
		self.device_info = None
		self.recognizer = None

		self.on_air = False


	def _decode_device_name(self, device_name):
		for codec in ["utf-8", "cp1253", "cp1252"]:
			try:
				device_name = device_name.decode(codec)
				for i in ['\r', '\n']:
					device_name = device_name.replace(i, '')

				return device_name
			except:
				pass
		
		return 'Unknown device'


	def start(self):
		self.stop()

		if not (activation_key:=self.settings.get('stc_activation_key')) or not len(activation_key):
			self.window.evaluate_js(f'ss14starter.notification("stc_activation_key_not_specified", "danger")')
			return False
		
		if not (chat_key := self.settings.get('stc_chat_key')) or not len(chat_key):
			self.window.evaluate_js(f'ss14starter.notification("stc_chat_key_not_specified", "danger")')
			return False
		
		try:
			self.model = vosk.Model(model_path=self.config.stc_model_dir)
		except:
			self._reset_requirements()
			return None
		
		if (stc_device_index := self.settings.get('stc_device')) == None:
			self.window.evaluate_js(f'ss14starter.notification("stc_input_device_not_specified", "danger")')
			return False
		
		try:
			self.device_info = pyaudio.pa.get_device_info(stc_device_index)
			self.recognizer = vosk.KaldiRecognizer(self.model, self.device_info.defaultSampleRate)
		except:
			self._reset_requirements()
			return False

		Thread(target=self.main_loop, daemon=True).start()
			
		return True


	def _reset_requirements(self):
		self.recognizer = None
		self.model = None
		self.device_info = None


	def stop(self):
		self._reset_requirements()

		while self.on_air:
			time.sleep(0.1)


	def is_combo_pressed(self, keys):
		return all([keyboard.is_pressed(key) for key in keys])
	

	def main_loop(self):
		self.on_air = True

		while all((self.device_info, self.recognizer)):
			time.sleep(0.1)

			if not (activation_key:=self.settings.get('stc_activation_key')) or not keyboard.is_pressed(activation_key) or not self.active_game_window():
				continue

			prefix = None
			for _prefix in sorted(self.settings.get('stc_prefixes'), key=lambda x: len(x[1]), reverse=True):
				if keyboard.is_pressed(_prefix[1]):
					prefix = _prefix
					break

			try:
				stream = self.audio.open(format=pyaudio.paInt16, frames_per_buffer=self.chunk_size, channels=self.device_info.maxInputChannels, rate=self.framerate, input=True)
				while len(audio_data := stream.read(self.chunk_size)) and keyboard.is_pressed(activation_key):
					self.audio_buffer.write(audio_data)

				stream.stop_stream()
				stream.close()
			except:
				self.window.evaluate_js(f'ss14starter.notification("unable_to_start_input_device_streaming", "danger")')
				time.sleep(1)
				continue

			try:
				self.recognizer.AcceptWaveform(self.audio_buffer.getvalue())
				result = self.recognizer.FinalResult()

				if (text := json.loads(result).get('text')) and len(text):
					self.write_to_chat(text, prefix)
			
			except:
				pass

			self.audio_buffer.truncate(0)
			self.audio_buffer.seek(0)

		self.on_air = False


	def active_game_window(self):
		if self.config.debug:
			return True
		
		try:
			pid_info = ctypes.wintypes.DWORD()
			ctypes.windll.user32.GetWindowThreadProcessId(ctypes.windll.user32.GetForegroundWindow(), ctypes.byref(pid_info))

			return psutil.Process(pid_info.value).exe() == os.path.abspath(self.config.dotnet_path)
		
		except:
			pass
		

	def write_to_chat(self, text, prefix):
		words = []
		for word in text.split():
			if replaced_word := next((i[0] for i in words_replces if word == i[1]), None):
				word = replaced_word
			words.append(word)

		text = ' '.join(words)
		if not re.match(exceptions_question_words_pattern, text) and re.match(question_words_pattern, text):
			text += '?'

		if prefix:
			text = prefix[0] + text

		if self.config.debug:
			print(f':> {text}')

		keyboard.send(*self.settings.get('stc_chat_key'))

		time.sleep(0.1)
		keyboard.write(text)
		time.sleep(0.1)

		if self.settings.get('stc_instant_send'):
			keyboard.send('enter')


	def get_audio_input_devices(self):
		audio_input_devices = []

		default_host_api_index = pyaudio.pa.get_default_host_api()
		num_devices = pyaudio.pa.get_device_count()
		for i in range(num_devices):
			device_info = pyaudio.pa.get_device_info(i)
			if device_info.maxInputChannels and device_info.hostApi == default_host_api_index:
				audio_input_devices.append((i, self._decode_device_name(device_info.name)))

		return audio_input_devices
	

	def get_default_audio_input_device(self):
		device_index = pyaudio.pa.get_default_input_device()
		if device_index != None:
			device_info = pyaudio.pa.get_device_info(device_index)

			return ((device_index, self._decode_device_name(device_info.name)))
		

	def get_hotkey_names(self, keycodes):
		result = []
		for keycode in keycodes:
			if key:=keyboard._os_keyboard.official_virtual_keys.get(keycode):
				result.append(key[0])
			
		return result
		