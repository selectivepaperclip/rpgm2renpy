init python:
    class GameSpecificCodeIncestAdventure():
        def eval_script(self, line, script_string):
            gre = Re()
            if gre.match('add_skill\(.*\)', line):
                pass
            elif gre.match('set_fmode\(\d+\)', line):
                pass
            elif gre.match('set_fighters\((\d+),\s*(\d+)\)', line):
                groups = gre.last_match.groups()
                player_id = int(groups[0])
                enemy_id = int(groups[1])

                victor_variable = 1

                result = renpy.display_menu([("A duel is happening!", None), ("You Win!", player_id), ("You Lose!", enemy_id)])
                game_state.variables.set_value(victor_variable, result)
            else:
                return False

            return True