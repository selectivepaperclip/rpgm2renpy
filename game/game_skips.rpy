init python:
    class GameSkips:
        def ics2_skip_unpacking(self):
            for variable_id in xrange(14, 22 + 1):
                game_state.variables.set_value(variable_id, 2)
            game_state.variables.set_value(13, 9)
