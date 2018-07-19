init python:
    class GameSkips:
        def ics2_skip_unpacking(self):
            for variable_id in xrange(14, 22 + 1):
                game_state.variables.set_value(variable_id, 2)
            game_state.variables.set_value(13, 9)
            for event_id in [1, 7, 8, 9, 11, 12, 13, 14, 15]:
                game_state.self_switches.set_value((45, event_id, 'A'), True)
