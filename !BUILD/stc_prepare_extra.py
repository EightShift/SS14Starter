import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)

os.chdir(app_dir)
sys.path.append(app_dir)

activate_this_path = '/.venv/{}/activate_this.py'.format('Scripts' if sys.platform == 'win32' else 'bin')

venv_activator = os.path.normpath(os.sep.join(os.getcwd().split(os.sep)) + activate_this_path)
exec(compile(open(venv_activator, 'rb').read(), venv_activator, 'exec'), dict(__file__=venv_activator))

from stc import words_replces


with open(os.path.join(current_dir, 'pre_extra.txt'), "r", encoding='utf-8') as pre_extra_file:
    pre_extra = [i for i in pre_extra_file.read().split('\n') if len(i)]

extra = []
for text in pre_extra:
    words = []
    for word in text.lower().split():
        if replaced_word := next((i[1] for i in words_replces if word == i[0].lower()), None):
            word = replaced_word
        words.append(word)
    extra.append(' '.join(words))

with open(os.path.join(current_dir, 'extra.txt'), "w", encoding='utf-8') as pre_extra_file:
    pre_extra_file.write('\n'.join(extra))
