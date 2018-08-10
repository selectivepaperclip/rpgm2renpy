init python:
    class GameSpecificCodeMilfsVilla():
        def hide_buggy_event(self, map, event, page):
            # Climbing onto the dresser twice in the maid's room to get the credit card can lead to bugs
            if map.map_id == 9:
                if event['id'] in [4]:
                    # Don't show if any of the day 1 maid sequences have progressed
                    return (game_state.switches.value(9) == True) or (game_state.switches.value(10) == True) or (game_state.switches.value(11) == True)

            # Milf's Villa has a scene where you need to cover a hole with an ottoman.
            # If you move the ottoman to the area before there is a hole, even in the original game, it will be lost forever.
            if map.map_id == 19:
                # Fix broken state from savegames before this fix was in - if the hole was covered before the hole existed,
                # the switches will be in the wrong state
                if game_state.switches.value(59) == True and game_state.switches.value(61) == True:
                    game_state.switches.set_value(61, False)

                # Hide the ottoman destination tiles if the quest is not to the phase where the ottoman should be moved there
                if event['id'] in [14, 15, 16]:
                    return game_state.switches.value(59) != True

            return False
