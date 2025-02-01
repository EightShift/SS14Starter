import os
import sys
import ctypes

# INFO
app_name = 'SS14Starter'
app_version = 2.14
platform = sys.platform

gui = 'gtk'

# DEBUG
debug = False
if len(sys.argv) > 1:
	if '--debug' in sys.argv:
		debug = True

# WINDOW CONFIG
window_size = (860, 600)
scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
window_size = [int(i * scale_factor) for i in window_size]

background_color = '#212126'


# PATHS
current_dir = f'.{os.sep}'
ss14Starter_path = os.path.join(current_dir, os.path.basename(sys.argv[0]))
if not ss14Starter_path.endswith('.exe'):
	ss14Starter_path = os.path.join(current_dir, f'{app_name}.bat')

temp_dir = os.path.join(current_dir, 'temp')
engines_dir = os.path.join(current_dir, 'engines')

languages_dir = os.path.join(current_dir, 'languages')

assets_dir = os.path.join(current_dir, 'assets')
images_dir = os.path.join(assets_dir, 'images')
main_html_path = os.path.join(assets_dir, 'main.html')
js_dir = os.path.join(assets_dir, 'js')
css_dir = os.path.join(assets_dir, 'css')
scss_dir = os.path.join(assets_dir, 'scss')

if os.path.exists(assets_dir):
	main_html_py = {}
	for root, dirnames, files in os.walk(assets_dir):
		if root.startswith(scss_dir):
			continue
		
		for file in files:
			file_path = os.path.join(root, file)
			with open(file_path, 'rb') as f:
				key = file
				if assets_dir != root:
					key = os.path.basename(root) + '/' + key

				content_type = 'text/html'
				if file.split('.')[-1] == 'js':
					content_type = 'application/javascript'

				if file.split('.')[-1] == 'css':
					content_type = 'text/css'

				main_html_py[key] = {"content": f.read(), "content_type": content_type}

	with open('main_html.py', 'w') as f:
		f.write(f'main_html={main_html_py}\n')
			
signing_key_path = os.path.join(current_dir, 'signing_key')

settings_name = 'settings.pickle'
settings_path = os.path.join(current_dir, settings_name)

backup_settings_name = f'{settings_name}.backup'
backup_settings_path = os.path.join(current_dir, backup_settings_name)

content_database_name = 'content.db'
content_database_path = os.path.join(current_dir, content_database_name)


new_version_dir = os.path.join(current_dir, '!_NEW_VERSION_!')
new_version_updater_path = os.path.join(current_dir, 'updater.' + ('ps1' if platform == 'win32' else 'sh'))

dotnet_dir = os.path.join(current_dir, 'dotnet')
dotnet_name = 'dotnet'
if platform == 'win32':
	dotnet_name += '.exe'
dotnet_path = os.path.join(dotnet_dir, dotnet_name)

loader_dir = os.path.join(current_dir, 'loader')
loader_path = os.path.join(loader_dir, 'SS14.Loader.dll')

unins000_exe = os.path.join(current_dir, 'unins000.exe')
unins000_dat = os.path.join(current_dir, 'unins000.dat')

cache_dir = os.path.join(current_dir, 'cache')
replays_dir = os.path.join(current_dir, 'replays')
notes_dir = os.path.join(current_dir, 'notes')
stc_model_dir = os.path.join(current_dir, 'stc_model')

local_server_dir = os.path.join(current_dir, 'local_server')
local_server_path = os.path.join(local_server_dir, 'Robust.Server.dll')


refresh_interval = 1000
long_refresh_interval = refresh_interval * 10
account_token_refresh_time = 14 * 24 * 60 * 60 * 1000



class URLS():
	localhost_address_template = 'http://127.0.0.1:{}/'

	auth = 'https://auth.spacestation14.com'
	sign_in = f'{auth}/api/auth/authenticate'
	refresh_token = f'{auth}/api/auth/refresh'

	central = f'https://central.spacestation14.io'

	servers = f'{central}/hub/api/servers'
	server_info = f'{servers}/info'
	register = f'{central}/web/Identity/Account/Register'

	robust_builds_manifest = f'{central}/builds/robust/manifest.json'
	robust_modules_manifest = f'{central}/builds/robust/modules.json'

	local_server_builds = {
		"wizards": f'{central}/builds/wizards/builds.html',
		"syndicate": 'https://cdn.station14.ru/fork/syndicate-public'
	}

	last_versions_info = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRtcYKSOSD-hV_7O3kO_zDbmIb1-FscdDmeojTIKvPwiTbU1vbFrm36Yj3CQxgu4BmoG-yUrPahh85n/pub?output=csv'

	share = 'https://discord.gg/gh4jzGSqWb'

	# multiverse_hub = 'https://cdn.spacestationmultiverse.com/hub'
	# multiverse_hub_servers = f'{multiverse_hub}/api/servers'
	# multiverse_hub_server_info = f'{multiverse_hub}/info'

content_compression_scheme = {
	None: 0,
    "Deflate": 1,
    "ZStd": 2
	}

auth_modes = (
    'Optional',
    'Required',
    'Disabled'
)

ss14_schemes = {
	"ss14": {
		"port": 1212,
		"scheme": 'http'
		}, 
	"ss14s": {
		"port": 443,
		"scheme": 'https'
		}
	}



