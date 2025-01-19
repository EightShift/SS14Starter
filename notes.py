import json
import os
from uuid import uuid4


class Notes():
	def __init__(self, config):
		self.config = config

	def _notes_dir_check(func):
		def wrapper(self, *args, **kwargs):
			if not os.path.exists(self.config.notes_dir):
				os.mkdir(self.config.notes_dir)

			return func(self, *args, **kwargs)

		return wrapper

	@_notes_dir_check
	def load(self):
		notes = []
		for name in os.listdir(self.config.notes_dir):
			path = os.path.join(self.config.notes_dir, name)
			with open(path, 'r', encoding='utf8') as file:
				note = json.load(file)
				if 'name' not in note or 'text' not in note or 'id' not in note:
					continue

				notes.append(note)
				
		return notes

	@_notes_dir_check
	def save(self, note_data):
		id = note_data.get('id')
		path = None
		if not id:
			while True:
				id = str(uuid4())
				path = os.path.join(self.config.notes_dir, id)
				if not os.path.exists(path):
					break
			
			note_data["id"] = id
			
		if not path:
			path = os.path.join(self.config.notes_dir, id)

		with open(path, 'w', encoding='utf8') as note:
			json.dump(note_data, note)

		return id

	@_notes_dir_check
	def remove(self, id):
		path = None
		for name in os.listdir(self.config.notes_dir):
			path = os.path.join(self.config.notes_dir, name)
			with open(path, 'r', encoding='utf8') as file:
				note = json.load(file)
				if note.get('id') == id:
					break
		if path:
			try:
				os.remove(path)
			except:
				pass