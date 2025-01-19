import os
import sys

only_arg = '--only'
only = None
if only_arg in sys.argv:
	only_index = sys.argv.index(only_arg) + 1
	if len(sys.argv) >= only_index + 1:
		only = sys.argv[only_index]


current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)

os.chdir(app_dir)
sys.path.append(app_dir)

activate_this_path = '/.venv/{}/activate_this.py'.format('Scripts' if sys.platform == 'win32' else 'bin')

venv_activator = os.path.normpath(os.sep.join(os.getcwd().split(os.sep)) + activate_this_path)
exec(compile(open(venv_activator, 'rb').read(), venv_activator, 'exec'), dict(__file__=venv_activator))


import subprocess
import shutil
import config
import zipfile
import hashlib

last_version_content = []


def zipper(zip_path, directory):
	with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
		_hash_ = hashlib.sha256()

		for root, _, files in os.walk(directory):
			for f in files:
				if f == '__hash__':
					continue
				
				file_path = os.path.join(root, f)
				print(file_path)

				with open(file_path, 'rb') as f:
					while True:
						chunk = f.read(4096)  # Read the file in chunks
						if not chunk:
							break
						_hash_.update(chunk)

				arc_name = os.path.relpath(file_path, directory)
				zipf.write(file_path, arcname=arc_name)

		return _hash_.hexdigest()
		




# params
last_version_path = os.path.normpath(os.path.join(current_dir, f'__last_versions__.csv'))

release_dir = os.path.normpath(os.path.join(current_dir, 'release'))
release_platform_dir = os.path.normpath(os.path.join(release_dir, sys.platform))


icon_path = os.path.normpath(os.path.join(app_dir, '_logo_/icon.ico'))

dist_dir = os.path.normpath(os.path.join(release_platform_dir, f'{config.app_name}'))
if sys.platform == 'win32':
	dist_dir += '.dist'

if not only or only == 'app':
	app_zip = os.path.normpath(os.path.join(release_platform_dir, f'{config.app_name}-{config.app_version}.zip'))
	if os.path.exists(app_zip):
		os.remove(app_zip)

		from utils import update_css
		update_css(os.path.join(app_dir, f'assets/css'), os.path.join(app_dir, f'assets/scss'))


	# exe
	if sys.platform == 'win32':
		cmd = [
			'nuitka',
			'--standalone',
			'--disable-console',
			'--clang',
			'--remove-output',
			f'--windows-icon-from-ico={icon_path}',
			f'--output-dir={release_platform_dir}',
			f'--product-name={config.app_name}',
			f'--file-version={config.app_version}',
			f'{config.app_name}.py'
		]

		subprocess.call(cmd, shell=True, cwd=app_dir)

	else:
		cmd = [
			'pyinstaller',
			'--noconfirm',
			'--onedir',
			'--windowed',
			'--icon',
			'_logo_/logo_transparent.png',
			'--distpath',
			f'{release_platform_dir}',
			f'{config.app_name}.py'
		]

		subprocess.call(cmd, cwd=app_dir)

	# copy
	shutil.copyfile('signing_key', os.path.normpath(os.path.join(dist_dir, 'signing_key')))

	shutil.copytree('languages', os.path.normpath(os.path.join(dist_dir, 'languages')), dirs_exist_ok=True)
	shutil.copytree('loader', os.path.normpath(os.path.join(dist_dir, 'loader')), dirs_exist_ok=True)
	shutil.copytree('dotnet', os.path.normpath(os.path.join(dist_dir, 'dotnet')), dirs_exist_ok=True)

	shutil.rmtree(os.path.normpath(os.path.join(dist_dir, 'assets/css/scss')), ignore_errors=True)

	if sys.platform == 'linux':
		shutil.rmtree(os.path.normpath(os.path.join(dist_dir, 'share')), ignore_errors=True)

	app_hash = zipper(app_zip, dist_dir)

	last_version_content.append(["app", app_hash, '', 'win32', config.app_version])





if not only or only == 'stc_model':
	# stc_model
	stc_model_dir = os.path.normpath(os.path.join(app_dir, 'stc_model'))

	stc_model_zip = os.path.join(release_dir, 'stc_model.zip')
	if os.path.exists(stc_model_zip):
		os.remove(stc_model_zip)


	stc_model_hash = zipper(stc_model_zip, stc_model_dir)

	last_version_content.append(["stc_model", stc_model_hash, '', '', ''])


with open(last_version_path, 'w', encoding='utf-8') as last_version_f:
	last_version_f.write('\n'.join([','.join([str(o) for o in i]) for i in last_version_content]))

input('Ready!')