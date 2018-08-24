init python:
    class GameSpecificCodeRobotsTouch():
        def eval_full_script(self, script_string):
            pass

        def eval_script(self, line, script_string):
            game_system_command = re.match("^\$game_system.*", line)

            if game_system_command:
                return True
            elif line == 'combine_choices':
                return True
            else:
                return False
