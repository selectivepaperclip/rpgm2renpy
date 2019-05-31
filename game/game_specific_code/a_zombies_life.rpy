init python:
    class GameSpecificCodeAZombiesLife():
        def eval_script(self, line, script_string):
            if line.startswith('Stats_Windows'):
                return self._eval_stat_window_script(line, script_string)

            gre = Re()
            # Cosmetic / undesirable commands - ignore completely
            if gre.search('\$game_map\.effect_surface', line):
                return True
            elif gre.search('s\.change_color', line):
                return True
            elif gre.search('bust_mirror', line):
                return True
            elif gre.match('DoorMove\.(open|close)_door', line):
                return True
            elif gre.match('WeightMove\.set_speed', line):
                return True
            elif gre.match('auto_save_game', line):
                return True

            if gre.match('add_rep\((.*?)(,false)?\)', line):
                # TODO
                return True
            elif gre.match('increase_rep\((.*?)\)', line):
                # TODO
                return True
            elif gre.match('color_choice\((\d+),\s*(\d+),\s*(.*?)\)', line):
                # TODO
                return True
            elif gre.match('craft\(\d+\)', line):
                # TODO
                return True
            elif gre.match('play_scene\("(.*?)",\s*(\d+)\s*,\s*(\d+)\s*\)', line):
                # TODO
                return True

            return False

        def _eval_stat_window_script(self, line, script_string):
            gre = Re()
            if gre.match('Stats_Windows\.update_stat_window\((\d+)\)', line):
                return True
            elif gre.match('Stats_Windows\.update_stat_values', line):
                return True
            elif gre.match('Stats_Windows\.show_stats_points_remaining', line):
                return True
            elif gre.match('Stats_Windows\.show_(\w+)_value\((\w+)\)', line):
                return True
            elif gre.match('Stats_Windows\.close_all_windows', line):
                return True

            return False

        def eval_fancypants_value_statement(self, script_string):
            gre = Re()
            if gre.match('return_rep\((.*?)\)', script_string):
                # like $game_actors\[2\]\.name
                return True

            return None