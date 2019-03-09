init python:
    class GalvScreenButtons:
        @classmethod
        def process_script(cls, script_string):
            plugin = game_file_loader.plugin_data_exact('Galv_ScreenButtons')
            if not plugin:
                return False
            if not plugin['status']:
                return False

            gre = Re()
            if gre.match('Galv\.SBTNS\.addButton\((\d+),\'map\',\'(\w+)\',(\d+),(\d+),\[\'event\',(\d+)\]\);?', script_string):
                button_id = int(gre.last_match.groups()[0])
                button_image = gre.last_match.groups()[1]
                button_x = int(gre.last_match.groups()[2])
                button_y = int(gre.last_match.groups()[3])
                event_id = int(gre.last_match.groups()[4])
                if not hasattr(game_state, 'galv_screen_buttons'):
                    game_state.galv_screen_buttons = {}
                game_state.galv_screen_buttons[button_id] = {
                    'x': button_x,
                    'y': button_y,
                    'image': game_file_loader.full_path_for_picture(rpgm_path('www/img/system/%s' % button_image)),
                    'event_id': event_id
                }
                return True
            elif gre.match('\$gameSystem\._hideBtns\s*=\s*(true|false);?\s*', script_string):
                return True
            else:
                return False