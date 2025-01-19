const tooltip_offset = 15;
const animation_duration = 300;

const server_regex = /^ss14s?:\/\/(([\w-]+\.)+[\w-]+|([\d.]+))(:\d{1,5})?(\/.*)?$/;
const ipv4_regex = /^(\d{1,3}\.){3}\d{1,3}(:\d{1,5})?$/;
const localhost_regex = /^(ss14s?:\/\/)?(localhost|127\.0\.0\.1)(:\d{1,5})?\/?$/;

const share_emojies = [
    "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "🥲", "🥹", "😊", "😇",
    "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚", "😋", "😛",
    "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🥸", "🤩", "🥳", "😏", "😒",
    "😞", "😔", "😟", "😕", "🙁", "☹️", "😣", "😖", "😫", "😩", "🥺", "😢",
    "😭", "😮‍💨", "😤", "😠", "😡", "🤬", "🤯", "😳", "🥵", "🥶", "😱", "😨",
    "😰", "😥", "😓", "🫣", "🤗", "🫡", "🤔", "🫢", "🤭", "🤫", "🤥", "😶",
    "😶‍🌫️", "😐", "😑", "😬", "🫠", "🙄", "😯", "😦", "😧", "😮", "😲", "🥱",
    "😴", "🤤", "😪", "😵", "😵‍💫", "🤐", "🥴", "🤧", "😷", "🤒", "🤕", "😈",
    "👿", "👺", "🤡", "💩", "👻", "💀", "☠️", "👽", "👾", "🤖", "🎃", "😺",
    "😸", "😹", "😻", "😼", "😽", "🙀", "😿", "😾"
];


var hotkey_reader_press_counter = 0;
var hotkey_reader_key_buffer = [];

function hotkey_reader_keydown(e) {
    e.preventDefault();

    if (!hotkey_reader_key_buffer.includes(e.keyCode)) {
        hotkey_reader_press_counter += 1;
        hotkey_reader_key_buffer.push(e.keyCode);
    }

    pywebview.api.stc_get_hotkey_names(hotkey_reader_key_buffer).then((keynames) => {
        if (keynames && keynames.length) {
            e.target.value = keynames.map(keyname => keyname.charAt(0).toUpperCase() + keyname.slice(1)).join(' + ')
        }
    });


}

function hotkey_reader_keyup(e, setter_name) {
    e.preventDefault();

    if (hotkey_reader_press_counter) {
        hotkey_reader_press_counter -= 1;
    }
    
    if (!hotkey_reader_press_counter) {
        pywebview.api.stc_get_hotkey_names(hotkey_reader_key_buffer).then((keynames) => {
            if (!keynames) {
                return;
            }

            if (keynames.length) {
                ss14starter.settings[setter_name](e, keynames);
            }

        });

        hotkey_reader_key_buffer = [];
    }
}


function check_auth_data() {
    if (auth_login.value.length >= 2 && auth_password.value.length >= 6) {
        auth_submit_button.disabled = false;
    } else {
        auth_submit_button.disabled = true;
    }
}


function show_confirm_window(title_text, yes_action, no_action) {
    confirm_title.innerText = title_text;

    confirm_button_yes.onclick = () => { yes_action() };

    if (no_action) {
        confirm_button_no.onclick = () => { no_action() };
    }

    confirm_window.show();
}


function tfa_code_cancel() {
    auth_login.classList.remove("uk-form-small");
    auth_password.classList.remove("uk-form-small");

    auth_login.disabled = false;
    auth_password.disabled = false;

    auth_tfa_code_container.hidden = true;
    auth_tfa_code.value = null;
}


window.addEventListener('pywebviewready', function () {
    window.main_grid = UIkit.util.$('#main_grid');

    window.app_name = UIkit.util.$('#app_name', main_grid);
    window.app_version = UIkit.util.$('#app_version', main_grid);
    window.share_link = UIkit.util.$('#share_link', main_grid);
    window.share_link_tooltip = UIkit.tooltip(share_link, { pos: "right-center", duration: animation_duration });

    window.minimize_button = UIkit.util.$('#minimize_button', main_grid);
    window.minimize_button.hidden = false;

    window.close_button = UIkit.util.$('#close_button', main_grid);
    window.close_button.hidden = false;
    
    window.content_preloader = UIkit.util.$('#content_preloader', main_grid);
    window.content_grid = UIkit.util.$('#content_grid', main_grid);

    window.start_local_server_button = UIkit.util.$('#start_local_server_button', content_grid);
    window.start_local_server_button_tooltip = UIkit.tooltip(start_local_server_button, { offset: tooltip_offset, duration: animation_duration});

    window.replays_button = UIkit.util.$('#replays_button', content_grid);
    window.replays_button_tooltip = UIkit.tooltip(replays_button, { offset: tooltip_offset, duration: animation_duration });

    window.notes_button = UIkit.util.$('#notes_button', content_grid);
    window.notes_button_tooltip = UIkit.tooltip(notes_button, { offset: tooltip_offset, duration: animation_duration });

    window.textart_button = UIkit.util.$('#textart_button', content_grid);
    window.textart_button_tooltip = UIkit.tooltip(textart_button, { offset: tooltip_offset, duration: animation_duration });

    window.stc_button = UIkit.util.$('#stc_button', content_grid);
    window.stc_button_tooltip = UIkit.tooltip(stc_button, { offset: tooltip_offset, duration: animation_duration });

    window.servers_search = UIkit.util.$('#servers_search', content_grid);

    window.add_server_button = UIkit.util.$('#add_server_button', content_grid);
    window.add_server_button_tooltip = UIkit.tooltip(add_server_button, { offset: tooltip_offset, duration: animation_duration });

    window.settings_button = UIkit.util.$('#settings_button', content_grid);
    window.settings_button_tooltip = UIkit.tooltip(settings_button, { offset: tooltip_offset, duration: animation_duration, pos: "top-right" });

    window.accounts_button = UIkit.util.$('#accounts_button', content_grid);
    window.servers_list = UIkit.util.$('#servers_list', content_grid);
    window.servers_list_accordion = UIkit.accordion(servers_list);

    window.add_server_window = UIkit.modal('#add_server_window');
    window.adding_a_server_title = UIkit.util.$('#adding_a_server_title', add_server_window.$el);
    window.server_address = UIkit.util.$('#server_address', add_server_window.$el);
    window.add_server_submit_button = UIkit.util.$('#add_server_submit_button', add_server_window.$el);

    window.settings_window = UIkit.modal('#settings_window');
    window.settings_title = UIkit.util.$('#settings_title', settings_window.$el);
    window.language_selector_button = UIkit.util.$('#language_selector_button', settings_window.$el);
    window.language_selector_button_label = UIkit.util.$('#language_selector_button_label', language_selector_button);
    window.language_selector_button_language_name = UIkit.util.$('#language_selector_button_language_name', language_selector_button);
    window.language_selector_container = UIkit.util.$('#language_selector_container');
    window.language_selector_container_dropdown = UIkit.dropdown(language_selector_container);
    window.language_selector_list = UIkit.util.$('#language_selector_list', language_selector_container);
    window.reconnect_to_favorite_checkbox = UIkit.util.$('#reconnect_to_favorite_checkbox', settings_window.$el);
    window.reconnect_to_favorite_label = UIkit.util.$('#reconnect_to_favorite_label', settings_window.$el);
    window.hide_not_favorite_checkbox = UIkit.util.$('#hide_not_favorite_checkbox', settings_window.$el);
    window.hide_not_favorite_label = UIkit.util.$('#hide_not_favorite_label', settings_window.$el);
    window.priority_for_account_connection_checkbox = UIkit.util.$('#priority_for_account_connection_checkbox', settings_window.$el);
    window.priority_for_account_connection_label = UIkit.util.$('#priority_for_account_connection_label', settings_window.$el);
    // window.multiverse_hub_checkbox = UIkit.util.$('#multiverse_hub_checkbox', settings_window.$el);
    // window.multiverse_hub_label = UIkit.util.$('#multiverse_hub_label', settings_window.$el);
    window.traffic_economy_checkbox = UIkit.util.$('#traffic_economy_checkbox', settings_window.$el);
    window.traffic_economy_label = UIkit.util.$('#traffic_economy_label', settings_window.$el);

    window.compat_mode_checkbox = UIkit.util.$('#compat_mode_checkbox', settings_window.$el);

    window.local_server_build_selector_button = UIkit.util.$('#local_server_build_selector_button', settings_window.$el);
    window.local_server_build_selector_button_label = UIkit.util.$('#local_server_build_selector_button_label', local_server_build_selector_button);
    window.local_server_build_selector_button_build_name = UIkit.util.$('#local_server_build_selector_button_build_name', local_server_build_selector_button);
    window.local_server_build_selector_container = UIkit.util.$('#local_server_build_selector_container');
    window.local_server_build_selector_container_dropdown = UIkit.dropdown(local_server_build_selector_container);
    window.local_server_build_selector_selector_list = UIkit.util.$('#local_server_build_selector_selector_list', local_server_build_selector_container);

    window.open_local_server_folder_button = UIkit.util.$('#open_local_server_folder_button', settings_window.$el);
    window.remove_engines_button = UIkit.util.$('#remove_engines_button', settings_window.$el);
    window.clear_content_data_button = UIkit.util.$('#clear_content_data_button', settings_window.$el);

    window.accounts_window = UIkit.modal('#accounts_window');
    window.accounts_list = UIkit.util.$('#accounts_list', accounts_window.$el);
    window.signing_in_title = UIkit.util.$('#signing_in_title', accounts_window.$el);
    window.auth_login = UIkit.util.$('#auth_login', accounts_window.$el);
    window.auth_password = UIkit.util.$('#auth_password', accounts_window.$el);
    window.auth_tfa_code_container = UIkit.util.$('#auth_tfa_code_container', accounts_window.$el);
    window.auth_tfa_code = UIkit.util.$('#auth_tfa_code', auth_tfa_code_container);
    window.auth_tfa_code_cancel = UIkit.util.$('#auth_tfa_code_cancel', auth_tfa_code_container);
    window.auth_submit_button = UIkit.util.$('#auth_submit_button', accounts_window.$el);
    window.register_new_button = UIkit.util.$('#register_new_button', accounts_window.$el);

    window.progress_bar_window = UIkit.modal('#progress_bar_window');
    window.progress_bar_title = UIkit.util.$('#progress_bar_title', progress_bar_window.$el);
    window.progress_bar_progress = UIkit.util.$('#progress_bar_progress', progress_bar_window.$el);
    window.progress_bar_cancel_button = UIkit.util.$('#progress_bar_cancel_button', progress_bar_window.$el);

    window.replays_window = UIkit.modal('#replays_window');
    window.replays_title = UIkit.util.$('#replays_title', replays_window.$el);
    window.replays_list = UIkit.util.$('#replays_list', replays_window.$el);
    window.open_replays_folder_button = UIkit.util.$('#open_replays_folder_button', replays_window.$el);

    window.textart_window = UIkit.modal('#textart_window');
    window.textart_title = UIkit.util.$('#textart_title', textart_window.$el);
    window.textart_select_button = UIkit.util.$('#textart_select_button', textart_window.$el);
    window.textart_adapt_to_book_button = UIkit.util.$('#textart_adapt_to_book_button', textart_window.$el);
    window.textart_adapt_to_book_button_tooltip = UIkit.tooltip(textart_adapt_to_book_button, { offset: tooltip_offset, duration: animation_duration });
    window.textart_adapt_to_paper_button = UIkit.util.$('#textart_adapt_to_paper_button', textart_window.$el);
    window.textart_adapt_to_paper_button_tooltip = UIkit.tooltip(textart_adapt_to_paper_button, { offset: tooltip_offset, duration: animation_duration });
    window.textart_adapt_to_pda_button = UIkit.util.$('#textart_adapt_to_pda_button', textart_window.$el);
    window.textart_adapt_to_pda_button_tooltip = UIkit.tooltip(textart_adapt_to_pda_button, { offset: tooltip_offset, duration: animation_duration });

    window.textart_width_label = UIkit.util.$('#textart_width_label', textart_window.$el);
    window.textart_width_range = UIkit.util.$('#textart_width_range', textart_window.$el);
    window.textart_palette_size_label = UIkit.util.$('#textart_palette_size_label', textart_window.$el);
    window.textart_palette_size_range = UIkit.util.$('#textart_palette_size_range', textart_window.$el);
    window.textart_copy_button = UIkit.util.$('#textart_copy_button', textart_window.$el);
    window.textart_copy_button_tooltip = UIkit.tooltip(textart_copy_button, { offset: tooltip_offset, duration: animation_duration, pos: "top-right" });
    window.textart_result = UIkit.util.$('#textart_result', textart_window.$el);

    window.confirm_window = UIkit.modal('#confirm_window');
    window.confirm_title = UIkit.util.$('#confirm_title', confirm_window.$el);
    window.confirm_button_no = UIkit.util.$('#confirm_button_no', confirm_window.$el);
    window.confirm_button_yes = UIkit.util.$('#confirm_button_yes', confirm_window.$el);

    window.notes_window = UIkit.modal('#notes_window');
    window.notes_title = UIkit.util.$('#notes_title', notes_window.$el);
    window.notes_list = UIkit.util.$('#notes_list', notes_window.$el);
    window.create_note_button = UIkit.util.$('#create_note_button', notes_window.$el);

    window.stc_window = UIkit.modal('#stc_window');
    window.stc_title = UIkit.util.$('#stc_title', stc_window.$el);
    window.stc_toggle_button = UIkit.util.$('#stc_toggle_button', stc_window.$el);
    window.stc_toggle_button_dropdown = UIkit.tooltip(stc_toggle_button, { offset: tooltip_offset, duration: animation_duration, pos: "top-right" });
    window.stc_instant_send_label = UIkit.util.$('#stc_instant_send_label', stc_window.$el);
    window.stc_instant_send_checkbox = UIkit.util.$('#stc_instant_send_checkbox', stc_window.$el);
    window.stc_activation_key_input_label = UIkit.util.$('#stc_activation_key_input_label', stc_window.$el);
    window.stc_activation_key_input = UIkit.util.$('#stc_activation_key_input', stc_window.$el);
    window.stc_chat_key_input_label = UIkit.util.$('#stc_chat_key_input_label', stc_window.$el);
    window.stc_chat_key_input = UIkit.util.$('#stc_chat_key_input', stc_window.$el);
    window.stc_prefixes_label = UIkit.util.$('#stc_prefixes_label', stc_window.$el);
    window.stc_prefixes_info = UIkit.util.$('#stc_prefixes_info', stc_window.$el);
    window.stc_prefixes_info_tooltip = UIkit.tooltip(stc_prefixes_info, { offset: tooltip_offset, duration: animation_duration, pos: "right" });
    window.stc_prefixes_grid = UIkit.util.$('#stc_prefixes_grid', stc_window.$el);
    window.stc_create_prefix_button = UIkit.util.$('#stc_create_prefix_button', stc_window.$el);

    window.audio_input_devices_selector_button = UIkit.util.$('#audio_input_devices_selector_button', stc_window.$el);
    window.audio_input_devices_selector_button_tooltip = UIkit.tooltip(audio_input_devices_selector_button, { offset: tooltip_offset, duration: animation_duration, pos: "top-left" });
    window.audio_input_devices_selector_container = UIkit.util.$('#audio_input_devices_selector_container');
    window.audio_input_devices_selector_container_dropdown = UIkit.dropdown(audio_input_devices_selector_container);
    window.audio_input_devices_selector_list = UIkit.util.$('#audio_input_devices_selector_list', audio_input_devices_selector_container);

    window.ss14starter = new SS14Starter();


    UIkit.util.on(servers_list, 'beforeshow', (e) => {
        let server = findArrInList(ss14starter.servers, "address", e.target.getAttribute("address"));
        if (server && (!server.info || server.is_cached_info)) {
            server.load_info();
        }
    });

    UIkit.util.on(notes_list, 'beforeshow', (e) => {
        let note = findArrInList(ss14starter.notes, "id", e.target.getAttribute("note_id"));
        if (note) {
            note.edit();
        }
    });


    UIkit.util.on(notes_list, 'stop', () => {
        ss14starter.save_notes_sequence();
    });

    UIkit.util.on(servers_search, 'keyup', () => {
        ss14starter.update_servers();
    });

    UIkit.util.on(reconnect_to_favorite_checkbox, 'change', () => {
        ss14starter.settings.toggle_reconnect_to_favorite();
    });

    UIkit.util.on(hide_not_favorite_checkbox, 'change', () => {
        ss14starter.settings.toggle_hide_not_favorite();
    });

    UIkit.util.on(priority_for_account_connection_checkbox, 'change', () => {
        ss14starter.settings.toggle_priority_for_account_connection();
    });

    // UIkit.util.on(multiverse_hub_checkbox, 'change', () => {
    //     ss14starter.settings.toggle_multiverse_hub();
    // });

    UIkit.util.on(traffic_economy_checkbox, 'change', () => {
        ss14starter.settings.toggle_traffic_economy();
    });
    
    UIkit.util.on(compat_mode_checkbox, 'change', () => {
        ss14starter.settings.toggle_compat_mode();
    });

    UIkit.util.on(remove_engines_button, 'click', () => {
        pywebview.api.remove_engines().then(() => {
            ss14starter.notification('engines_removed', 'success');
        });
    });

    UIkit.util.on(clear_content_data_button, 'click', () => {
        pywebview.api.clear_content_data().then(() => {
            ss14starter.notification('content_data_cleared', 'success');
        });
    });

    UIkit.util.on(stc_toggle_button, 'click', () => {
        ss14starter.settings.toggle_stc();
    });
    
    UIkit.util.on(stc_activation_key_input, 'keydown', (e) => {
        hotkey_reader_keydown(e);
    });
    
    UIkit.util.on(stc_activation_key_input, 'keyup', (e) => {
        hotkey_reader_keyup(e, "set_stc_activation_key");
    });

    UIkit.util.on(stc_chat_key_input, 'keydown', (e) => {
        hotkey_reader_keydown(e);
    });

    UIkit.util.on(stc_chat_key_input, 'keyup', (e) => {
        hotkey_reader_keyup(e, "set_stc_chat_key");
    });


    UIkit.util.on(stc_instant_send_checkbox, 'change', () => {
        ss14starter.settings.toggle_stc_instant_send();
    });
    
    UIkit.util.on(auth_login, 'input', (e) => {
        check_auth_data();
    });

    UIkit.util.on(auth_password, 'input', (e) => {
        check_auth_data();
    });
    

    UIkit.util.on(server_address, 'input', (e) => {
        if (server_regex.test(server_address.value) || ipv4_regex.test(server_address.value) || localhost_regex.test(server_address.value)) {
            add_server_submit_button.disabled = false;
        } else {
            add_server_submit_button.disabled = true;
        }
    });


    UIkit.util.on(document, 'paste', (e) => {
        if (textart_window.isToggled()) {
            const item = e.clipboardData.items[0];
            if (item && item.type && item.type.startsWith('image/')) {
                ss14starter.textart._upload(item.getAsFile());
            }
        }
    });

    UIkit.util.on(auth_tfa_code_cancel, 'click', (e) => {
        tfa_code_cancel();
    });


});



class TextArt {
    constructor() {
        this.image = null;

        this.min_width = parseInt(textart_width_range.min);
        this.max_width = parseInt(textart_width_range.max);
        this.width = parseInt(textart_width_range.value);

        this.min_palette_size = parseInt(textart_palette_size_range.min);
        this.max_palette_size = parseInt(textart_palette_size_range.max);
        this.palette_size = parseInt(textart_palette_size_range.value);

        this.adapts = {
            paper: [42, 6000],
            book: [38, 12000],
            pda: [45, 12000]
        };

        this.text_art = [];

    }

    select(input) {
        let item = input.files[0];
        if (item && item.type.startsWith('image/')) {
            this._upload(item);
        }
    }

    _upload(image) {
        let reader = new FileReader();

        reader.onload = (e) => {
            this.image = new Image();
            this.image.onload = () => {
                if (!this.text_art.length) {
                    textart_adapt_to_book_button.disabled = false;
                    textart_adapt_to_paper_button.disabled = false;
                    textart_adapt_to_pda_button.disabled = false;
                    textart_copy_button.disabled = false;
                }

                this._handle_image();

                this._draw();
            }

            this.image.src = e.target.result;
        }

        reader.readAsDataURL(image);

    }

    set_width() {
        this.width = parseInt(textart_width_range.value);
        this._handle_image();

        this._draw();

    }


    set_palette_size() {
        this.palette_size = parseInt(textart_palette_size_range.value);
        this._handle_image();

        this._draw();

    }

    _handle_image() {
        if (!this.image) {
            return;
        }

        let width_percent = this.width / this.image.width;
        let new_height = Math.floor((this.image.height * width_percent) / 2);

        let canvas = document.createElement('canvas');
        canvas.width = this.width;
        canvas.height = new_height;

        let context = canvas.getContext('2d', { willReadFrequently: true });
        context.drawImage(this.image, 0, 0, this.width, new_height);

        quantize(context, this.palette_size);

        this.text_art = [];
        for (let y = 0; y < new_height; y++) {
            let pix_line = [];

            for (let x = 0; x < this.width; x++) {
                let pixel_data = context.getImageData(x, y, 1, 1).data;
                let hex_color = ((1 << 24) | (pixel_data[0] << 16) | (pixel_data[1] << 8) | pixel_data[2]).toString(16).slice(1);

                let half_hex_color = hex_color.slice(0, 3);
                if (half_hex_color == hex_color.slice(3)) {
                    hex_color = half_hex_color;
                }
                hex_color = "#" + hex_color;

                if (pix_line.length && pix_line[pix_line.length - 1][0] == hex_color) {
                    pix_line[pix_line.length - 1][1] += 1;
                } else {
                    pix_line.push([hex_color, 1]);
                }

            }

            this.text_art.push(pix_line);
        }

        canvas.remove();
    }

    _draw() {
        if (!this.text_art.length) {
            return;
        }

        while (textart_result.firstChild) {
            textart_result.removeChild(textart_result.lastChild);
        }

        for (let y = 0; y < this.text_art.length; y++) {
            let div = crel('div');
            for (let x = 0; x < this.text_art[y].length; x++) {
                div.appendChild(crel('span', { 'text': '█'.repeat(this.text_art[y][x][1]), 'style': `color: ${this.text_art[y][x][0]}` }));
            }
            textart_result.appendChild(div);
        }
    }

    adapt_to(target) {
        if (!this.text_art.length) {
            return;
        }

        this.width = this.adapts[target][0];
        textart_width_range.value = this.width;

        this.palette_size = this.max_palette_size;
        while (this.palette_size > this.min_palette_size) {
            this._handle_image();
            if (this._get_result().length <= this.adapts[target][1]) {
                break;
            }

            this.palette_size -= 1;
        }
        textart_palette_size_range.value = this.palette_size;

        this._draw();

    }

    copy() {
        if (!this.text_art.length) {
            return;
        }

        navigator.clipboard.writeText(this._get_result());

    }

    _get_result() {
        let text_art_lines = [];

        for (let y = 0; y < this.text_art.length; y++) {
            let text_art_line = '';
            for (let x = 0; x < this.text_art[y].length; x++) {
                text_art_line += `[color=${this.text_art[y][x][0]}]` + '█'.repeat(this.text_art[y][x][1]);
            }
            text_art_lines.push(text_art_line);
        }

        return text_art_lines.join('\n');
    }

}

class Note {
    constructor(note_data) {
        this.id = null;
        this.name = ss14starter.CLF.untitled_note;
        this.text = '';

        if (note_data) {
            this.id = note_data.id;
            this.name = note_data.name;
            this.text = note_data.text;
        }

        this.set_note_item_element();
        
        if (!note_data) {
            this.save();
        }
    }

    dict() {
        return {
            id: this.id,
            name: this.name,
            text: this.text
        };
    }
    
    set_note_item_element() {
        this.$element = crel('li');
        
        let container = crel('div', { "class": "accordion_item_container" });
        this.$element.appendChild(container);

        let grid = crel('div', { "class": "uk-grid-small", "uk-grid": "" });
        container.appendChild(grid);

        let remove_button_cell = crel('div');
        grid.appendChild(remove_button_cell);

        let remove_button = crel('button', { "type": "button", "class": "uk-button uk-button-link uk-button-small uk-text-secondary", "uk-icon": "icon: trash;" });
        remove_button_cell.appendChild(remove_button);

        remove_button.onclick = () => {
            this.remove();
        };

        this.$element.note_name_cell = crel('div', { "class": "uk-width-expand uk-flex uk-flex-middle" });
        grid.appendChild(this.$element.note_name_cell);
        this.$element.note_name = crel('a', { "class": "uk-accordion-title uk-overflow-hidden uk-text-nowrap uk-width-expand", "style": "text-overflow: ellipsis;" });
        this.$element.note_name_cell.appendChild(this.$element.note_name);


        this.$element.note_name_input_cell = crel('div', { "class": "uk-width-expand", "hidden": "" });
        grid.appendChild(this.$element.note_name_input_cell);
        this.$element.note_name_input = crel('input', { "type": "text", "class": "uk-input uk-form-small" });
        this.$element.note_name_input_cell.appendChild(this.$element.note_name_input);


        this.$element.note_save_button_cell = crel('div', { "hidden": "" });
        grid.appendChild(this.$element.note_save_button_cell);
        this.$element.note_save_button = crel('button', { "type": "button", "class": "uk-button uk-button-link uk-button-small uk-text-warning", "uk-icon": "icon: check;", "uk-tooltip": `title: ${ss14starter.CLF.save.toUpperCase()}` });
        this.$element.note_save_button.onclick = () => {
            this.save();
        };
        this.$element.note_save_button_cell.appendChild(this.$element.note_save_button);



        this.$element.note_cancel_button_cell = crel('div', { "hidden": "" });
        grid.appendChild(this.$element.note_cancel_button_cell);
        this.$element.note_cancel_button = crel('button', { "type": "button", "class": "uk-button uk-button-link uk-button-small uk-text-secondary", "uk-icon": "icon: close;", "uk-tooltip": `title: ${ss14starter.CLF.cancel.toUpperCase()}` });
        this.$element.note_cancel_button.onclick = () => {
            this.reset();
            this.refresh_view();
        };
        this.$element.note_cancel_button_cell.appendChild(this.$element.note_cancel_button);


        this.$element.note_copy_button_cell = crel('div');
        grid.appendChild(this.$element.note_copy_button_cell);
        this.$element.note_copy_button = crel('button', { "type": "button", "class": "uk-button uk-button-primary uk-button-small", "uk-icon": "icon: copy;", "uk-tooltip": `title: ${ss14starter.CLF.copy.toUpperCase()}; pos: top-right;` });
        this.$element.note_copy_button.onclick = () => {
            this.copy();
        };
        this.$element.note_copy_button_cell.appendChild(this.$element.note_copy_button);

        let note_text_grid_container = crel('div', { "class": "uk-accordion-content uk-width-1-1" });
        container.appendChild(note_text_grid_container);

        this.$element.note_text = crel('div', { "class": "uk-textarea uk-text-meta", "contenteditable": true });

        note_text_grid_container.appendChild(this.$element.note_text);

        notes_list.appendChild(this.$element);

        this.refresh_view();
    }

    refresh_view() {
        this.$element.setAttribute("note_id", this.id);

        if (this.name) {
            this.$element.note_name.innerText = this.name;
        }

        this.$element.note_text.innerText = this.text;
        
    }

    edit() {
        this.$element.note_name_cell.hidden = true;
        this.$element.note_name_input_cell.hidden = false;
        this.$element.note_save_button_cell.hidden = false;
        this.$element.note_cancel_button_cell.hidden = false;
        this.$element.note_copy_button_cell.hidden = true;

        this.$element.note_name_input.value = this.name;
    }

    save() {
        if (this.id) {
            this.name = this.$element.note_name_input.value;
            
            this.text = this.$element.note_text.innerText;

            this.reset();
            
        }

        pywebview.api.save_note(this.dict()).then((note_current_id) => {
            this.id = note_current_id;

            this.refresh_view();
        });

    }

    reset() {
        if (!this.name.length) {
            this.name = ss14starter.CLF.untitled_note;
        }

        this.$element.note_name_cell.hidden = false;
        this.$element.note_name_input_cell.hidden = true;
        this.$element.note_save_button_cell.hidden = true;
        this.$element.note_cancel_button_cell.hidden = true;
        this.$element.note_copy_button_cell.hidden = false;

        this.$element.note_name.innerText = this.name;
        this.$element.note_text.value = this.text;

        let index = Array.prototype.indexOf.call(notes_list.children, this.$element);
        UIkit.accordion(notes_list).toggle(index);
    }

    remove() {
        this.$element.remove();
        delete ss14starter.notes.splice(ss14starter.notes.indexOf(this), 1);

        return pywebview.api.remove_note(this.id);
        
    }

    copy() {
        if (!this.text.length) {
            return;
        }
        navigator.clipboard.writeText(this.text);
    }
}

class Server {
    constructor(address, status_data) {
        this.address = address;
        this.status_data = {
            name: this.address,
            players: '-',
            soft_max_players: '-'
        };

        this.status_data = {
            ...this.status_data,
            ...status_data
        }

        this.info = null;
        this.is_cached_info = false;

        this.is_favorite = ss14starter.settings.favorite_servers.includes(this.address);
        this.is_added = ss14starter.settings.added_servers.includes(this.address);

        this.set_server_item_element();
        
        this.load_cached_info();
    }

    dict() {
        return {
            address: this.address,
            status_data: this.status_data,
            info: this.info,
            favorite: this.is_favorite,
            added: this.is_added
        };
    }

    draw_server_info() {
        if (this.info.desc) {
            this.$element.server_info_description.innerText = this.info.desc;
        }

        this.$element.server_info_grid.removeAllChildren();

        if (this.info.links) {
            for (let i = 0; i < this.info.links.length; i++) {
                switch (this.info.links[i].icon) {
                    case 'web':
                        this.info.links[i].icon = 'world';
                        break;

                    case 'wiki':
                        this.info.links[i].icon = 'info';
                        break;

                    case 'forum':
                        this.info.links[i].icon = 'users';
                        break;
                }
                
                let server_link_button_cell = crel('div');
                this.$element.server_info_grid.appendChild(server_link_button_cell)

                let server_link_button = crel('a', {
                    "class": "uk-button uk-button-primary uk-button-small uk-flex uk-flex-middle",
                    "text": this.info.links[i].name
                });
                server_link_button_cell.appendChild(server_link_button);

                let server_link_button_icon = crel("span", { "class": "uk-margin-small-right uk-flex-first", "uk-icon": `icon: ${this.info.links[i].icon}; ratio: 0.8;` });
                server_link_button.appendChild(server_link_button_icon);
                server_link_button.onclick = () => {
                    pywebview.api.open_url(this.info.links[i].url);
                };

            }
        }
    }

    load_cached_info() {
        return pywebview.api.load_server_cached_info(this.address).then((cached_info) => {
            if (!cached_info) {
                return;
            }
            
            this.info = cached_info;
            this.is_cached_info = true;

            this.draw_server_info();

            return cached_info;
        });
    }

    load_info() {
        return pywebview.api.load_server_info(this.address, this.is_added).then((info) => {
            if (!info) {
                return;
            }

            this.info = info;

            this.draw_server_info();

            return info;
        });
    }

    _set_name_and_players() {
        this.$element.server_name.innerText = this.status_data.name;
        this.$element.server_players.innerText = `${this.status_data.players} / ${this.status_data.soft_max_players}`;
    }

    refresh_view(status_data) {
        if (status_data) {
            this.status_data = {
                ...this.status_data,
                ...status_data
            }
        }

        if (this.is_added) {
            pywebview.api.load_server_status(this.address).then((status) => {

                if (status) {
                    this.status_data = {
                        ...this.status_data,
                        ...status
                    }
                    
                    this.$element.server_connect_button.innerText = ss14starter.CLF.connect;
                    this.$element.server_connect_button.disabled = false;

                } else {
                    this.status_data = {
                        ...this.status_data,
                        ...{
                            players: '-',
                            soft_max_players: '-'
                        }
                    }

                    this.$element.server_connect_button.innerText = ss14starter.CLF.offline;
                    this.$element.server_connect_button.disabled = true;

                }

                this._set_name_and_players();
            });

        } else {
            if (this.is_favorite) {
                this.$element.favorite_button.classList.add("filled_favorite_button");
            } else {
                this.$element.favorite_button.classList.remove("filled_favorite_button");
            }
        }

        this._set_name_and_players();

    }

    set_server_item_element() {
        this.$element = crel('li', { "address": this.address });

        let container = crel('div', { "class": "accordion_item_container"});
        this.$element.appendChild(container);

        let grid = crel('div', { "class": "uk-grid-small", "uk-grid": "" });
        container.appendChild(grid);

        let favorite_or_remove_button_cell = crel('div');
        grid.appendChild(favorite_or_remove_button_cell);

        if (this.is_added) {
            this.$element.remove_button = crel('button', { "type": "button", "class": "uk-buttonl uk-button-link uk-button-smal uk-text-secondary", "uk-icon": "icon: trash;" });
            favorite_or_remove_button_cell.appendChild(this.$element.remove_button);
            this.$element.remove_button.onclick = () => {
                this.remove();
            };

        } else {
            this.$element.favorite_button = crel('button', { "type": "button", "class": "uk-button uk-button-link uk-button-smal favorite_button", "uk-icon": "icon: star;" });
            favorite_or_remove_button_cell.appendChild(this.$element.favorite_button);
            this.$element.favorite_button.onclick = () => {
                this.favorite();
            };

        }

        let server_name_cell = crel('div', { "class": "uk-width-expand uk-flex uk-flex-middle" });
        grid.appendChild(server_name_cell);
        this.$element.server_name = crel('a', { "class": "uk-accordion-title uk-overflow-hidden uk-text-nowrap uk-width-expand", "style": "text-overflow: ellipsis;" });
        server_name_cell.appendChild(this.$element.server_name);

        let server_players_cell = crel('div', { "class": "uk-flex uk-flex-middle" });
        grid.appendChild(server_players_cell);
        this.$element.server_players = crel('span');
        server_players_cell.appendChild(this.$element.server_players);


        let server_connect_button_cell = crel('div');
        grid.appendChild(server_connect_button_cell);
        this.$element.server_connect_button = crel('button', { "type": "button", "class": "uk-button uk-button-primary uk-button-small", "text": ss14starter.CLF.connect });
        this.$element.server_connect_button.onclick = () => {
            this.connect();
        };
        server_connect_button_cell.appendChild(this.$element.server_connect_button);

        if (this.is_added) {
            this.$element.server_connect_button.innerText = ss14starter.CLF.offline;
            this.$element.server_connect_button.disabled = true;
        }

        let server_info_grid_container = crel('div', { "class": "uk-accordion-content uk-width-1-1" });
        container.appendChild(server_info_grid_container);

        this.$element.server_info_description = crel('div', { "class": "uk-width-1-1 uk-margin" });
        server_info_grid_container.appendChild(this.$element.server_info_description);

        this.$element.server_info_grid = crel('div', { "class": "uk-grid-small", "uk-grid": "" });
        server_info_grid_container.appendChild(this.$element.server_info_grid);
        
        this.refresh_view();

    }

    connect(account) {
        if (!account) {
            account = ss14starter.settings.get_selected_account();
        }

        pywebview.api.connect_server(this.address, account ? account.userId : null);

    }

    favorite() {
        if (this.is_favorite) {
            let avorite_server_index = ss14starter.settings.favorite_servers.indexOf(this.address);
            ss14starter.settings.favorite_servers.splice(avorite_server_index, 1);

            this.$element.favorite_button.classList.remove("filled_favorite_button");

        } else {
            ss14starter.settings.favorite_servers.push(this.address);

            this.$element.favorite_button.classList.add("filled_favorite_button");
        }

        this.is_favorite = !this.is_favorite;

        ss14starter.settings.update().then(() => {
            ss14starter.update_servers();
        });

    }


    remove() {
        let server_index = ss14starter.settings.added_servers.indexOf(this.address);
        ss14starter.settings.added_servers.splice(server_index, 1);

        ss14starter.settings.update().then(() => {
            ss14starter.update_servers();
        });

        ss14starter.notification('server_removed', 'success');
    }

}

class Replay {
    constructor(replay_data) {
        this.name = replay_data.name;
        this.time = replay_data.time;

        this.set_replay_item_element();
    }

    set_replay_item_element() {
        this.$element = crel('li');

        let grid = crel('div', { "class": "uk-grid-small uk-flex-middle", "uk-grid": "" });
        this.$element.appendChild(grid);

        let remove_button_cell = crel('div', { "class": "uk-width-auto" });
        grid.appendChild(remove_button_cell);

        let remove_button = crel('button', { "type": "button", "class": "uk-button uk-button-link uk-button-small uk-text-secondary", "uk-icon": "icon: trash;" });
        remove_button.onclick = () => {
            this.remove();
        };
        remove_button_cell.appendChild(remove_button);

        

        let name_cell = crel('div', { "class": "uk-width-expand" });
        grid.appendChild(name_cell)

        let name = crel('span', {
            "class": `uk-width-1-1`, "text": this.name
        });
        name_cell.appendChild(name);

        let start_button_cell = crel('div');
        grid.appendChild(start_button_cell);

        let start_button = crel('button', { "class": "uk-button uk-button-secondary uk-button-small", "uk-icon": "icon: play;" });
        start_button.onclick = () => {
            this.start();
        };
        start_button_cell.appendChild(start_button);

    }


    start() {
        return pywebview.api.start_replay(this.name).then((result) => {
            console.log(result)
            if (!result) {
                return;
            }

            replays_window.hide();
        });
    }

    remove() {
        return pywebview.api.remove_replay(this.name).then((result) => {
            if (!result) {
                return;
            }

            ss14starter.check_replays();
        });
    }
}

class Account {
    constructor(account_data) {
        this.userId = account_data.userId;
        this.username = account_data.username;
        this.token = account_data.token;
        this.expireTime = account_data.expireTime;
        this.selected = account_data.selected;

        this.set_account_item_element();
    }

    dict() {
        return {
            userId: this.userId,
            username: this.username,
            token: this.token,
            expireTime: this.expireTime,
            selected: this.selected
        };
    }

    set_account_item_element() {
        this.$element = crel('li');

        let grid = crel('div', { "class": "uk-grid-small", "uk-grid": "" });
        this.$element.appendChild(grid);

        let cell_0 = crel('div', { "class": "uk-width-expand" });
        grid.appendChild(cell_0)

        this.$element.account_select_button = crel('button', { "class": `uk-button uk-button-primary uk-button-small uk-width-1-1`, "style": "text-transform: none;", "text": this.username });
        this.$element.account_select_button.onclick = () => {
            ss14starter.settings.select_account(this.userId);
        };

        cell_0.appendChild(this.$element.account_select_button);

        let cell_1 = crel('div');
        grid.appendChild(cell_1)

        let account_remove_button = crel('button', { "class": "uk-button uk-button-secondary uk-button-small", "uk-icon": "icon: trash;" });
        account_remove_button.onclick = () => {
            ss14starter.settings.remove_account(this.userId);
        };
        cell_1.appendChild(account_remove_button);

        this.refresh_view();

    }

    refresh_view() {
        if (this.selected) {
            this.$element.account_select_button.disabled = true;
        } else {
            this.$element.account_select_button.disabled = false;
        }
    }

    refresh_token() {
        return pywebview.api.refresh_account_token(this.token).then((new_token_data) => {
            if (!new_token_data || new_token_data.newToken || new_token_data.expireTime) {
                return;
            }

            this.token = new_token_data.newToken;
            this.expireTime = new_token_data.expireTime;
        });
    }
}

class Settings {
    constructor() {
        this.accounts;
        this.favorite_servers;
        this.added_servers;
        this.reconnect_to_favorite;
        this.hide_not_favorite;
        this.priority_for_account_connection;
        // this.multiverse_hub;
        this.traffic_economy;
        this.compat_mode;
        this.language;
        this.local_server_build;
        this.notes_sequence;
        this.stc;
        this.stc_device;
        this.stc_activation_key;
        this.stc_chat_key;
        this.stc_instant_send;
        this.stc_prefixes;
    }

    dict() {
        let accounts = [];
        for (let i = 0; i < this.accounts.length; i++) {
            accounts.push(this.accounts[i].dict());
        }

        let stc_prefixes = [];
        for (let i = 0; i < this.stc_prefixes.length; i++) {
            if (this.stc_prefixes[i][0] && this.stc_prefixes[i][1].length) {
                stc_prefixes.push(this.stc_prefixes[i]);
            }
        }

        return {
            accounts: accounts,
            favorite_servers: this.favorite_servers,
            added_servers: this.added_servers,
            reconnect_to_favorite: this.reconnect_to_favorite,
            hide_not_favorite: this.hide_not_favorite,
            priority_for_account_connection: this.priority_for_account_connection,
            // multiverse_hub: this.multiverse_hub,
            traffic_economy: this.traffic_economy,
            compat_mode: this.compat_mode,
            language: this.language,
            local_server_build: this.local_server_build,
            notes_sequence: this.notes_sequence,
            stc: this.stc,
            stc_device: this.stc_device,
            stc_activation_key: this.stc_activation_key,
            stc_chat_key: this.stc_chat_key,
            stc_instant_send: this.stc_instant_send,
            stc_prefixes: stc_prefixes
        };

    }

    load() {
        return pywebview.api.load_settings().then((settings) => {
            if (!settings) {
                pywebview.api.remove_settings().then(() => { this.load(); });
                return;
            }
            
            this.accounts = [];
            for (let i = 0; i < settings.accounts.length; i++) {
                let account = new Account(settings.accounts[i]);
                accounts_list.appendChild(account.$element);
                this.accounts.push(account);
            }
        
            this.favorite_servers = settings.favorite_servers;
            this.added_servers = settings.added_servers;
            this.reconnect_to_favorite = settings.reconnect_to_favorite;
            this.hide_not_favorite = settings.hide_not_favorite;
            this.priority_for_account_connection = settings.priority_for_account_connection;
            // this.multiverse_hub = settings.multiverse_hub;
            this.traffic_economy = settings.traffic_economy;
            this.compat_mode = settings.compat_mode;
            this.language = settings.language;
            this.local_server_build = settings.local_server_build;
            this.notes_sequence = settings.notes_sequence;
            this.stc = settings.stc;
            this.stc_device = settings.stc_device;
            this.stc_activation_key = settings.stc_activation_key;
            this.stc_chat_key = settings.stc_chat_key;
            this.stc_instant_send = settings.stc_instant_send;
            this.stc_prefixes = settings.stc_prefixes;

            this._refresh_accounts_tokens();

            this.refresh_view();
        });
    }

    _refresh_accounts_tokens() {
        if (!this.accounts.length) {
            return;
        }
        let accounts_counter = this.accounts.length;
        let two_weeks_later_time = new Date().getTime() + ss14starter.config.account_token_refresh_time;
        for (let i = 0; i < this.accounts.length; i++) {
            if (new Date(this.accounts[i].expireTime).getTime() > two_weeks_later_time) {
                accounts_counter -= 1;
                continue;
            }

            this.accounts[i].refresh_token().then(() => {
                accounts_counter -= 1;
                if (accounts_counter == 0) {
                    this.update();
                }
            });
        }
    }

    update() {
        return pywebview.api.update_settings(this.dict()).then((response) => {
            if (!response) {
                return; // не удалось сохранить настройки
            }
        });
    }

    refresh_accounts_view() {
        accounts_button.innerText = auth_submit_button.innerText;

        for (let i = 0; i < this.accounts.length; i++) {
            this.accounts[i].refresh_view();

            if (this.accounts[i].selected) {
                accounts_button.innerText = this.accounts[i].username;
            }
        }
    }

    refresh_view() {
        this.refresh_accounts_view();

        for (let i = 0; i < local_server_build_selector_selector_list.children.length; i++) {
            let local_server_build_li = local_server_build_selector_selector_list.children[i];

            local_server_build_li.classList = [];
            if (this.local_server_build == local_server_build_li.innerText) {
                local_server_build_li.classList.add("uk-active", "uk-disabled");
            }
        }

        for (let i = 0; i < audio_input_devices_selector_list.children.length; i++) {
            let audio_input_device_li = audio_input_devices_selector_list.children[i];

            audio_input_device_li.classList = [];
            if (this.stc_device == parseInt(audio_input_device_li.getAttribute("device_index"))) {
                audio_input_device_li.classList.add("uk-active", "uk-disabled");
            }
        }

        reconnect_to_favorite_checkbox.checked = this.reconnect_to_favorite;
        hide_not_favorite_checkbox.checked = this.hide_not_favorite;
        priority_for_account_connection_checkbox.checked = this.priority_for_account_connection;
        // multiverse_hub_checkbox.checked = this.multiverse_hub;
        traffic_economy_checkbox.checked = this.traffic_economy;
        compat_mode_checkbox.checked = this.compat_mode;
        local_server_build_selector_button_build_name.innerText = this.local_server_build;

        stc_activation_key_input.value = this.stc_activation_key.map(keyname => keyname.charAt(0).toUpperCase() + keyname.slice(1)).join(' + ');
        stc_chat_key_input.value = this.stc_chat_key.map(keyname => keyname.charAt(0).toUpperCase() + keyname.slice(1)).join(' + ');
        stc_instant_send_checkbox.checked = this.stc_instant_send;

        for (let i = 0; i < this.stc_prefixes.length; i++) {
            this.create_stc_prefix(this.stc_prefixes[i]);
        }

        this._toggle_stc();
    }

    create_stc_prefix(prefix) {
        let prefix_cell = crel('div');
        stc_prefixes_grid.appendChild(prefix_cell);

        let prefix_div = crel('div', { "class": "darker_container cut_diagonal_corners" });
        prefix_cell.appendChild(prefix_div);
        
        let prefix_grid = crel('div', { "class": "uk-grid-small", "uk-grid": ""});
        prefix_div.appendChild(prefix_grid);

        let prefix_remove_button_cell = crel('div');
        prefix_grid.appendChild(prefix_remove_button_cell);
        let prefix_remove_button = crel('button', { "type": "button", "class": "uk-button uk-button-link uk-button-small uk-text-secondary", "uk-icon": "icon: trash;" });
        prefix_remove_button_cell.appendChild(prefix_remove_button);
        prefix_remove_button.onclick = (e) => {
            this.remove_stc_prefix(e);
        };
        
        let prefix_text_cell = crel('div', { "class": "uk-width-expand" });
        prefix_grid.appendChild(prefix_text_cell);
        let prefix_text = crel('input', { "maxlength": "2", "class": "uk-input uk-form-small uk-text-center uk-width-1-1 stc_prefix_text", "uk-tooltip": ss14starter.CLF ? ss14starter.CLF.stc_prefix.toUpperCase() : '', "duration": animation_duration });
        
        prefix_text_cell.appendChild(prefix_text);
        prefix_text.onkeyup = (e) => {
            this.set_stc_prefix_text(e);
        };
        
        let prefix_key_cell = crel('div', { "class": "uk-width-1-1"});
        prefix_grid.appendChild(prefix_key_cell);
        let prefix_key = crel('input', { "class": "uk-input uk-form-small stc_prefix_key", "uk-tooltip": ss14starter.CLF ? ss14starter.CLF.stc_prefix_modificator_key.toUpperCase() : '', "duration": animation_duration });
        prefix_key_cell.appendChild(prefix_key);
        prefix_key.onkeydown = (e) => {
            hotkey_reader_keydown(e);
        };
        prefix_key.onkeyup = (e) => {
            hotkey_reader_keyup(e, "set_stc_prefix_key");
        };

        if (prefix) {
            prefix_text.value = prefix[0];
            prefix_key.value = prefix[1].map(keyname => keyname.charAt(0).toUpperCase() + keyname.slice(1)).join(' + ');
        } else {
            this.stc_prefixes.push([null, []]);
            
        }
    }

    sign_in(e) {
        e.preventDefault();

        auth_submit_button.disabled = true;

        let auths = {
            username: auth_login.value,
            password: auth_password.value
        };
        
        if (auth_tfa_code.value.length) {
            auths["TfaCode"] = auth_tfa_code.value.trim();
        }
        
        return pywebview.api.sign_in(auths).then((account_data) => {
            auth_submit_button.disabled = false;

            if (!account_data || account_data.errors) {
                if (account_data.code == 'TfaRequired') {
                    auth_login.classList.add("uk-form-small");
                    auth_password.classList.add("uk-form-small");

                    auth_login.disabled = true;
                    auth_password.disabled = true;
                    

                    auth_tfa_code_container.hidden = false;

                    return;
                }

                ss14starter.notification('authentication_error', 'danger');
                
                return;
            }

            tfa_code_cancel();

            auth_login.value = null;
            auth_password.value = null;
            

            let account = findArrInList(this.accounts, "userId", account_data.userId);
            if (account) {
                ss14starter.notification('account_already_exists', 'danger');

                account.username = account_data.username;
                account.token = account_data.token;
                account.expireTime = account_data.expireTime;

            } else {
                account = new Account(account_data);
                accounts_list.appendChild(account.$element);
                this.accounts.push(account);
                
                ss14starter.notification('you_have_successfully_logged_in', 'success');

                setTimeout(accounts_window.hide, 500);
            }

            this.select_account(account_data.userId);


        });
    }

    select_account(user_id) {
        for (let i = 0; i < this.accounts.length; i++) {
            this.accounts[i].selected = false;
            if (this.accounts[i].userId == user_id) {
                this.accounts[i].selected = true;
            }
        }

        this.refresh_accounts_view();

        this.update();
    }

    remove_account(user_id) {
        for (let i = 0; i < this.accounts.length; i++) {
            if (this.accounts[i].userId == user_id) {
                if (this.accounts[i].selected) {
                    if (this.accounts[i - 1]) {
                        this.accounts[i - 1].selected = true;
                    } else if (this.accounts[i + 1]) {
                        this.accounts[i + 1].selected = true;
                    }
                }

                this.accounts[i].$element.remove();
                this.accounts.splice(i, 1);
                break;
            }
        }

        this.refresh_accounts_view();

        this.update();

    }

    get_selected_account() {
        return findArrInList(this.accounts, "selected", true);
    }

    add_server(e) {
        e.preventDefault();

        let server_address = e.target.elements['server_address'].value.toLowerCase();

        if (!server_address.startsWith('ss14://') && !server_address.startsWith('ss14s://')) {
            server_address = 'ss14://' + server_address;
        }

        if (!server_address.endsWith('/')) {
            server_address += '/';
        }

        
        if (this.added_servers.includes(server_address)) {
            ss14starter.notification('server_already_added', 'warning');
            add_server_window.hide();
            return;
        }

        this.added_servers.push(server_address);

        add_server_window.hide();

        this.update();

        ss14starter.refresh_servers();

        ss14starter.notification('server_added', 'success');

    }

    toggle_reconnect_to_favorite() {
        this.reconnect_to_favorite = reconnect_to_favorite_checkbox.checked;

        this.update();
    }

    toggle_hide_not_favorite() {
        this.hide_not_favorite = hide_not_favorite_checkbox.checked;

        ss14starter.update_servers();

        this.update();
    }

    toggle_priority_for_account_connection() {
        this.priority_for_account_connection = priority_for_account_connection_checkbox.checked;

        this.update();
    }

    // toggle_multiverse_hub() {
    //     this.multiverse_hub = multiverse_hub_checkbox.checked;

    //     ss14starter.refresh_servers();

    //     this.update();
    // }

    toggle_traffic_economy() {
        this.traffic_economy = traffic_economy_checkbox.checked;

        this.update();
    }

    toggle_compat_mode() {
        this.compat_mode = compat_mode_checkbox.checked;

        this.update();
    }

    _toggle_stc() {
        if (this.stc) {
            stc_toggle_button.classList.remove('uk-button-primary');
            stc_toggle_button.classList.add('uk-button-secondary');

            if (ss14starter.CLF) {
                stc_toggle_button_dropdown.title = ss14starter.CLF.on.toUpperCase();
            }

            pywebview.api.stc_enable().then((result) => {
                if (!result) {
                    this.toggle_stc(false);
                }

                if (result == null) {
                    show_confirm_window(
                        ss14starter.CLF.need_stc_model,
                        function () {
                            pywebview.api.download_last_version("stc_model").then((result) => {
                                if (result) {
                                    stc_window.show();
                                    ss14starter.settings.toggle_stc(true);
                                } else {
                                    ss14starter.notification('error_while_downloading', 'danger')
                                }
                            });
                        }
                    );
                }

                
            });

        } else {
            stc_toggle_button.classList.remove('uk-button-secondary');
            stc_toggle_button.classList.add('uk-button-primary');

            if (ss14starter.CLF) {
                stc_toggle_button_dropdown.title = ss14starter.CLF.off.toUpperCase();
            }

            pywebview.api.stc_disable();
        }

        stc_toggle_button.classList.remove('uk-disabled');
    }

    toggle_stc(stc) {
        if (stc == undefined) {
            this.stc = !this.stc;
        } else {
            this.stc = stc;
        }
        
        stc_toggle_button.classList.add('uk-disabled');
        this.update().then(() => {
            this._toggle_stc();
        });
    }

    set_stc_activation_key(e, hotkey) {
        this.stc_activation_key = hotkey;
        this.toggle_stc(false);
    }

    set_stc_chat_key(e, hotkey) {
        this.stc_chat_key = hotkey;
        this.toggle_stc(false);
    }
    
    get_stc_prefix_index(e) {
        let stc_prefixes_grid_item = e.target;
        while (stc_prefixes_grid_item.parentNode != stc_prefixes_grid) {
            stc_prefixes_grid_item = stc_prefixes_grid_item.parentNode;
        }

        return Array.from(stc_prefixes_grid_item.parentNode.children).indexOf(stc_prefixes_grid_item);
    }

    set_stc_prefix_text(e) {
        let prefix_index = this.get_stc_prefix_index(e);

        this.stc_prefixes[prefix_index][0] = e.target.value.trim();
        if (!this.stc_prefixes[prefix_index][0].length) {
            this.stc_prefixes[prefix_index][0] = null;
        }

        this.update();
    }

    set_stc_prefix_key(e, hotkey) {
        let prefix_index = this.get_stc_prefix_index(e);
        
        this.stc_prefixes[prefix_index][1] = hotkey;

        this.update();
    }

    remove_stc_prefix(e) {
        let prefix_index = this.get_stc_prefix_index(e);

        stc_prefixes_grid.children[prefix_index].remove();

        this.stc_prefixes.splice(prefix_index, 1);

        this.update();
    }

    toggle_stc_instant_send() {
        this.stc_instant_send = stc_instant_send_checkbox.checked;
        this.update();
    }
    

    select_language(li, code) {
        language_selector_container_dropdown.hide();

        this.language = code;

        this.update();
        
        ss14starter.apply_language();

        for (let i = 0; i < ss14starter.servers.length; i++) {
            let server_connect_button = ss14starter.servers[i].$element.server_connect_button
            server_connect_button.innerText = server_connect_button.disabled ? ss14starter.CLF.offline : ss14starter.CLF.connect;
        }

        for (let i = 0; i < ss14starter.notes.length; i++) {
            ss14starter.notes[i].$element.note_save_button.setAttribute("uk-tooltip", `title: ${ss14starter.CLF.save.toUpperCase()}`);
            ss14starter.notes[i].$element.note_cancel_button.setAttribute("uk-tooltip", `title: ${ss14starter.CLF.cancel.toUpperCase()}`);
            ss14starter.notes[i].$element.note_copy_button.setAttribute("uk-tooltip", `title: ${ss14starter.CLF.copy.toUpperCase()}; pos: top-right;`);
        }

        for (let i = 0; i < language_selector_list.children.length; i++) {
            language_selector_list.children[i].classList = [];
        }

        li.classList.add("uk-active", "uk-disabled");
        
        language_selector_button_language_name.innerText = ss14starter.languages[code].name;
    }

    select_local_server_build(li, build_name) {
        local_server_build_selector_container_dropdown.hide();

        this.local_server_build = build_name;
        
        this.update();

        for (let i = 0; i < local_server_build_selector_selector_list.children.length; i++) {
            local_server_build_selector_selector_list.children[i].classList = [];
        }

        li.classList.add("uk-active", "uk-disabled");

        local_server_build_selector_button_build_name.innerText = this.local_server_build;
    }

    select_audio_input_device(li, device) {
        audio_input_devices_selector_container_dropdown.hide();

        this.stc_device = device[0];

        this.toggle_stc(false);

        for (let i = 0; i < audio_input_devices_selector_list.children.length; i++) {
            audio_input_devices_selector_list.children[i].classList = [];
        }

        li.classList.add("uk-active", "uk-disabled");

        audio_input_devices_selector_button.innerText = device[1];
    }
}

class SS14Starter {
    constructor() {
        this.config = {};
        this.servers = [];
        this.settings = new Settings();
        this.loaded_servers = [];
        this.languages = {};
        this.CLF;
        this.replays = [];
        this.notes = [];

        this.textart = new TextArt();

        this.init();

    }

    init() {
        pywebview.api.load_config().then((config) => {
            if (!config) {
                return;
            }

            this.config = config;

            if (this.config.platform == 'linux') {
                UIkit.util.$('style', 'head').innerText += '*::-webkit-scrollbar {width: 0;}';
            }

            this.apply_local_server_builds(this.config.local_server_builds);

            app_name.innerText = this.config.app_name;
            app_name.hidden = false;

            app_version.innerText = 'v' + (this.config.app_version % 1 === 0 ? (this.config.app_version).toFixed(1) : this.config.app_version);
            app_version.hidden = false;

            share_link.hidden = false;

            this.settings.load().then(() => {
                this.load_languages().then(() => {
                    this.load_cached_servers();

                    this.refresh_servers().then(() => {
                        content_grid.hidden = false;
                        content_preloader.hidden = true;

                        setInterval(() => {
                            this.refresh_servers();
                        }, this.config.long_refresh_interval);
                    });

                    this.update_me();
                    
                    share_link_tooltip.show();

                    this.load_notes();

                });

                this.check_replays().then(() => {
                    setInterval(() => {
                        if (replays_window.isToggled()) {
                            this.check_replays();
                        }
                    }, this.config.refresh_interval)
                });

                this.load_audio_input_devices().then(() => {
                    setInterval(() => {
                        if (stc_window.isToggled()) {
                            this.load_audio_input_devices();
                        }
                    }, this.config.refresh_interval)
                });
                
            })

        });

    }

    load_cached_servers() {
        return pywebview.api.load_cached_servers().then((servers) => {
            if (!servers) {
                return;
            }

            this.loaded_servers = servers;

            this.update_servers();

            content_grid.hidden = false;
            content_preloader.hidden = true;

        });
    }

    refresh_servers() {
        return pywebview.api.load_servers().then((servers) => {
            if (!servers || !servers.length) {
                ss14starter.notification('unable_to_load_servers', 'danger');
                return;
            }

            this.loaded_servers = servers;

            this.update_servers();

        });
    }

    update_servers() {
        let servers = [...this.loaded_servers];

        // only favorite servers
        if (this.settings.hide_not_favorite) {
            let server_index = 0;
            while (server_index != servers.length) {
                if (!this.settings.favorite_servers.includes(servers[server_index].address)) {
                    servers.splice(server_index, 1);
                    continue;
                }

                server_index += 1;
            }
        }

        // sort
        servers.sort((a, b) => (a.statusData.players < b.statusData.players) ? 1 : -1);

        servers.sort((a, b) => (this.settings.favorite_servers.includes(a.address) && !this.settings.favorite_servers.includes(b.address)) ? -1 : 1);

        let added_servers = [...this.settings.added_servers];
        added_servers.sort((a, b) => (localhost_regex.test(a)) ? 1 : -1);
        if (added_servers.length) {
            for (let i = 0; i < added_servers.length; i++) {
                servers.unshift({ "address": added_servers[i] });
            }
        }

        // filter
        let servers_search_value = servers_search.value.toLowerCase();
        if (servers_search_value.length) {
            let server_index = 0;
            while (server_index != servers.length) {
                let server = servers[server_index];
                if (!server.address.toLowerCase().includes(servers_search_value) && (!server.statusData || !server.statusData.name.toLowerCase().includes(servers_search_value))) {
                    servers.splice(server_index, 1);
                    continue;
                }

                server_index += 1;
            }
        }

        // add/update
        for (let i = 0; i < servers.length; i++) {
            let server = findArrInList(this.servers, "address", servers[i].address);
            if (server) {
                server.refresh_view(servers[i].statusData);
            } else {
                server = new Server(servers[i].address, servers[i].statusData);
                this.servers.push(server);
            }
            servers_list.appendChild(server.$element);
        }


        // remove
        let server_index = 0;
        while (server_index != this.servers.length) {
            let e_server = this.servers[server_index];
            let n_server = findArrInList(servers, "address", e_server.address);

            if (!n_server) {
                e_server.$element.remove();
                this.servers.splice(server_index, 1);
                continue;
            }

            server_index += 1;
        }


    }

    load_languages() {
        return pywebview.api.load_languages().then((languages) => {
            this.languages = languages;

            Object.entries(this.languages).forEach(([code, language]) => {
                let language_li = crel("li");
                language_selector_list.appendChild(language_li);

                let language_option = crel("a", { "text": language.name });
                language_option.onclick = () => {
                    this.settings.select_language(language_li, code);
                };
                language_li.appendChild(language_option);

                if (code == this.settings.language) {
                    language_li.classList.add("uk-active", "uk-disabled");

                    language_selector_button_language_name.innerText = language.name;
                }
            });
            

            this.apply_language();
        });
    }

    notification(message, status, timeout) {
        if (message in this.CLF) {
            message = this.CLF[message];
        }

        let options = {
            message: message,
            status: 'success',
            pos: 'bottom-center'
        };

        if (status != undefined) {
            options.status = status;
        }
        
        if (timeout != undefined) {
            options.timeout = timeout;
        }
        
        UIkit.notification(options);
    }

    log(message, status) {
        if (!status) {
            status = 'log';
        }

        if (message in this.CLF) {
            message = this.CLF[message];
        }

        console[status](message);
    }

    apply_language() {
        this.CLF = this.languages[this.settings.language].fields;

        share_link_tooltip.title = `${this.CLF.share_launcher.toUpperCase()} ${share_emojies[Math.floor(Math.random() * share_emojies.length)]}`;
        start_local_server_button_tooltip.title = this.CLF.start_local_server.toUpperCase();
        replays_button_tooltip.title = this.CLF.replays.toUpperCase();
        textart_button_tooltip.title = this.CLF.textart.toUpperCase();
        stc_button_tooltip.title = this.CLF.stc.toUpperCase();
        notes_button_tooltip.title = this.CLF.notes.toUpperCase();

        servers_search.placeholder = this.CLF.search;
        add_server_button_tooltip.title = this.CLF.add_server.toUpperCase();
        settings_button_tooltip.title = this.CLF.settings.toUpperCase();
        if (!this.settings.accounts.length) {
            accounts_button.innerText = this.CLF.sign_in.toUpperCase();
        }

        signing_in_title.innerText = this.CLF.signing_in;
        auth_login.placeholder = this.CLF.login.toUpperCase();
        auth_password.placeholder = this.CLF.password.toUpperCase();
        auth_tfa_code.placeholder = this.CLF.tfa_code.toUpperCase();
        auth_tfa_code_cancel.innerText = this.CLF.cancel;
        auth_submit_button.innerText = this.CLF.signing_in;
        register_new_button.innerText = this.CLF.register_new;

        adding_a_server_title.innerText = this.CLF.adding_a_server;
        server_address.placeholder = this.CLF.servers_address_or_localhost.toUpperCase();
        add_server_submit_button.innerText = this.CLF.add_server;

        settings_title.innerText = this.CLF.settings;
        language_selector_button_label.innerText = this.CLF.language;
        reconnect_to_favorite_label.innerText = this.CLF.reconnect_to_favorite_servers;
        hide_not_favorite_label.innerText = this.CLF.hide_not_favorite_servers;
        priority_for_account_connection_label.innerText = this.CLF.priority_for_account_connection;
        // multiverse_hub_label.innerText = this.CLF.multiverse_hub;
        traffic_economy_label.innerText = this.CLF.traffic_economy;
        compat_mode_label.innerText = this.CLF.compatibility_mode;
        open_local_server_folder_button.innerText = this.CLF.open_local_server_folder;
        local_server_build_selector_button_label.innerText = this.CLF.local_server_build;
        remove_engines_button.innerText = this.CLF.remove_engines;
        clear_content_data_button.innerText = this.CLF.clear_content_data;
        
        progress_bar_cancel_button.innerText = this.CLF.cancel;
        
        replays_title.innerText = this.CLF.replays;
        open_replays_folder_button.innerText = this.CLF.open_replays_folder;

        textart_title.innerText = this.CLF.textart;
        textart_select_button.innerText = this.CLF.select;
        textart_adapt_to_book_button_tooltip.title = this.CLF.adapt_to_book.toUpperCase();
        textart_adapt_to_paper_button_tooltip.title = this.CLF.adapt_to_paper.toUpperCase();
        textart_adapt_to_pda_button_tooltip.title = this.CLF.adapt_to_pda.toUpperCase();

        textart_copy_button_tooltip.title = this.CLF.copy.toUpperCase();
        textart_width_label.innerText = this.CLF.size;
        textart_palette_size_label.innerText = this.CLF.palette;

        confirm_button_no.innerText = this.CLF.no;
        confirm_button_yes.innerText = this.CLF.yes;

        notes_title.innerText = this.CLF.notes;
        create_note_button.innerText = this.CLF.create_note;

        stc_title.innerText = this.CLF.stc;
        audio_input_devices_selector_button_tooltip.title = this.CLF.microphone.toUpperCase();
        stc_toggle_button_dropdown.title = this.settings.stc ? this.CLF.on.toUpperCase() : this.CLF.off.toUpperCase();
        stc_activation_key_input_label.innerText = this.CLF.activation_key;
        stc_chat_key_input_label.innerText = this.CLF.chat_key;
        stc_instant_send_label.innerText = this.CLF.stc_instant_send;

        stc_prefixes_label.innerText = this.CLF.stc_prefixes;
        stc_prefixes_info_tooltip.title = this.CLF.stc_prefixes_info;
        stc_create_prefix_button.innerText = this.CLF.stc_create_prefix;

        let stc_prefix_texts = UIkit.util.$$('.stc_prefix_text', stc_prefixes_grid);
        for (let i = 0; i < stc_prefix_texts.length; i++) {
            stc_prefix_texts[i].setAttribute("uk-tooltip", `title: ${this.CLF.stc_prefix.toUpperCase()}; duration: ${animation_duration};`);
        }

        let stc_prefix_keys = UIkit.util.$$('.stc_prefix_key', stc_prefixes_grid);
        for (let i = 0; i < stc_prefix_keys.length; i++) {
            stc_prefix_keys[i].setAttribute("uk-tooltip", `title: ${this.CLF.stc_prefix_modificator_key.toUpperCase()}; duration: ${animation_duration};`);
        }
    }

    apply_local_server_builds(local_server_builds) {
        local_server_builds.forEach((build_name) => {
            let build_li = crel("li");
            local_server_build_selector_selector_list.appendChild(build_li);

            let build_option = crel("a", { "text": build_name, "class": "uk-text-uppercase" });
            build_li.appendChild(build_option);

            build_option.onclick = () => {
                this.settings.select_local_server_build(build_li, build_name);
            };
        });

    }

    check_replays() {
        return pywebview.api.check_replays().then((replays) => {
            replays.sort((a, b) => (a.time < b.time) ? 1 : -1);

            // add/update
            for (let i = 0; i < replays.length; i++) {
                let replay = findArrInList(this.replays, "name", replays[i].name);
                if (!replay) {
                    replay = new Replay(replays[i]);
                    this.replays.push(replay);
                }
                replays_list.appendChild(replay.$element);
            }


            // remove
            let replay_index = 0;
            while (replay_index != this.replays.length) {
                let e_replay = this.replays[replay_index];
                let n_replay = findArrInList(replays, "name", e_replay.name);

                if (!n_replay) {
                    e_replay.$element.remove();
                    this.replays.splice(replay_index, 1);
                    continue;
                }

                replay_index += 1;
            }
            
        });
    }

    start_local_server() {
        pywebview.api.check_latest_local_server().then((result) => {
            if (result) {
                let [current_hash, local_server_builds_data] = result;
                let platform_key = this.config.platform == 'win32' ? 'windows x64' : 'linux x64';

                if (current_hash) {
                    if (current_hash != local_server_builds_data.hash) {
                        show_confirm_window(
                            this.CLF.new_local_server_version,
                            function () {
                                pywebview.api.download_local_server(local_server_builds_data.builds[platform_key], local_server_builds_data.hash).then((result) => { if (result) { pywebview.api.start_local_server(); }});
                            },
                            function () {
                                pywebview.api.start_local_server();
                            }
                        );

                        return;
                    }

                } else {
                    pywebview.api.download_local_server(local_server_builds_data.builds[platform_key], local_server_builds_data.hash).then(() => {
                        pywebview.api.start_local_server();
                    });
                }
                
            }
            
            pywebview.api.start_local_server();

        });
    }

    load_notes() {
        pywebview.api.load_notes().then((notes) => {
            notes.sort((a, b) => {
                let indexA = this.settings.notes_sequence.indexOf(a.id);
                let indexB = this.settings.notes_sequence.indexOf(b.id);
                return indexA - indexB;
            });

            for (let i = 0; i < notes.length; i++) {
                this.notes.push(new Note(notes[i]));
            }
        });
    }
    
    create_note() {
        let note = new Note();
        this.notes.push(note);
    }

    save_notes_sequence() {
        let sequence = [];
        for (let i = 0; i < notes_list.children.length; i++) {
            sequence.push(notes_list.children[i].getAttribute("note_id"));
        }

        this.settings.notes_sequence = sequence;
        
        this.settings.update();
    }

    load_audio_input_devices() {
        return pywebview.api.load_audio_input_devices().then((audio_input_devices) => {
            if (!Number.isInteger(this.settings.stc_device)) {
                pywebview.api.load_default_audio_input_device().then((default_audio_input_device) => {
                    if (default_audio_input_device) {
                        this.settings.stc_device = default_audio_input_device[0];
                        this.settings.update();
                    }

                    return this.load_audio_input_devices();
                });

                
            }

            audio_input_devices_selector_list.removeAllChildren();

            if (audio_input_devices.length) {
                audio_input_devices_selector_button.disabled = false;
                stc_toggle_button.disabled = false;

                for (let i = 0; i < audio_input_devices.length; i++) {
                    let audio_input_device_li = crel('li', { "device_index": audio_input_devices[i][0] });

                    let audio_input_device_option = crel("a", { "class": "ellipsis_text", "text": audio_input_devices[i][1] });
                    audio_input_device_option.onclick = () => {
                        this.settings.select_audio_input_device(audio_input_device_li, audio_input_devices[i]);
                    };
                    audio_input_device_li.appendChild(audio_input_device_option);

                    audio_input_devices_selector_list.appendChild(audio_input_device_li);

                    if (audio_input_devices[i][0] == this.settings.stc_device) {
                        audio_input_device_li.classList.add("uk-active", "uk-disabled");
                        audio_input_devices_selector_button.innerText = audio_input_devices[i][1];
                    }

                }
            } else {
                audio_input_devices_selector_button.innerText = '—';
                audio_input_devices_selector_button.disabled = true;
                stc_toggle_button.disabled = true;

                if (this.settings.stc) {
                    this.settings.toggle_stc(false);
                }
            }
           

        });
    }

    
    update_me() {
        return pywebview.api.check_last_versions().then((last_versions) => {
            if (last_versions) {
                if (last_versions.app && last_versions.app.version > this.config.app_version) {
                    show_confirm_window(
                        this.CLF.new_launcher_version,
                        function () {
                            pywebview.api.download_last_version("app").then((result) => {
                                if (result) {
                                    ss14starter.notification('new_update_is_downloaded', 'success', 0);
                                } else {
                                    ss14starter.notification('error_while_downloading', 'danger');
                                }
                            });
                        }
                    );

                } else if (last_versions.stc_model && this.settings.stc && last_versions.stc_model.hash != last_versions.stc_model.current_hash) {
                    show_confirm_window(
                        this.CLF.new_stc_model_version,
                        function () {
                            pywebview.api.download_last_version("stc_model").then((result) => {
                                if (result) {
                                    pywebview.api.stc_enable();
                                } else {
                                    ss14starter.notification('error_while_downloading', 'danger');
                                }
                            });
                        }
                    );
                }

            } else {
                ss14starter.notification('unable_to_check_updatets', 'warning', 0);
            }

        });
    }
}


class ProgressBar {
    constructor() {
        this.progress = 0;
    }

    is_open() {
        return progress_bar_window.isToggled();
    }

    show() {
        this.set_progress(0);
        
        if (!this.is_open()) {
            progress_bar_window.show();
        }
    }

    hide() {
        this.set_progress(0);

        if (this.is_open()) {
            progress_bar_window.hide();
        }
        
    }

    set_title(title, reset_progress) {
        if (reset_progress != false) {
            this.show();
        }

        if (title in ss14starter.CLF) {
            progress_bar_title.innerText = ss14starter.CLF[title];
        } else {
            progress_bar_title.innerText = title;
        }
    }

    set_progress(progress) {
        this.progress = progress;
        this.update_progress();
    }

    add_progress(progress) {
        this.progress += progress;
        if (this.progress > 100) {
            this.progress = 100;
        }

        this.update_progress();
    }

    update_progress() {
        progress_bar_progress.value = parseInt(this.progress);
    }

    close() {
        this.set_progress(0);

        pywebview.api.cancel_operation().then((result) => {
            if (result) {
                this.hide();
            }
        });
    }

}

const progress_bar = new ProgressBar();


