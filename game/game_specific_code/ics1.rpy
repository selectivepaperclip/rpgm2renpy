init python:
    class GameSpecificCodeICS1():
        def eval_script(self, line, script_string):
            if '$game_map.effect_surface' in script_string:
                return True
            elif '$game_timer.set_timer' in script_string:
                return True
            else:
                return False
