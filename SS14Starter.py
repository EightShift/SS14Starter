import config
import logging

config.debug = True

logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


from utils import Settings, Updater, Server
settings = Settings(config)
updater = Updater(config)

server = Server(config, settings)


if config.debug:
	from utils import update_css
	update_css(config.css_dir, config.scss_dir)

	import json
	logger.debug(f'SETTINGS: \n{json.dumps(settings.get(), sort_keys=True, indent=4)}')

import webview
from API import Api
window = webview.create_window(
	config.app_name,
	url=server.address,
	background_color=config.background_color,
	frameless=True,
	easy_drag=False,
	width=config.window_size[0],
	height=config.window_size[1],
	min_size=config.window_size,
	js_api=Api
	)

window._js_api = window._js_api(config, settings, updater, window)

server.set_window(window)

webview.start(gui=config.gui, debug=config.debug, server=server)
