init python:
    class GameSpecificCodeMilfsControl():
        CARD_NAMES = {
            0: 'Nurse',
            1: 'Breast',
            2: 'Butt',
            3: 'Hero',
            4: 'Sister',
            5: 'Pussy',
            6: 'Aunt',
            7: 'Nun',
            8: 'Dick',
            9: 'Ring',
            10: 'Mother',
            11: 'Stockings',
            12: 'Bra',
            13: 'Teacher',
            14: 'Panties',
            15: 'SchoolGirl',
            16: 'Dildo',
            17: 'Friend',
            18: 'Lips',
            19: 'Purse',
            20: 'Stilettos',
            21: 'Award',
            22: 'Badge',
            23: 'Handcuffs',
            24: 'SunGlasses',
            25: 'WhitePanties',
            26: 'Baton',
            27: 'LongBoots',
            28: 'MagicalNecklace',
            29: 'PoliceWoman',
            30: 'RedPanties',
            31: 'SalesWoman',
            32: 'Twins',
            33: 'BallGag',
            34: 'BallGagDelux',
            35: 'Billy',
            36: 'BlackGlasses',
            37: 'BlindFold',
            38: 'BondageHandcuffs',
            39: 'Bullwhip',
            40: 'Camera',
            41: 'Candle',
            42: 'Chain',
            43: 'Condom',
            44: 'Diamond',
            45: 'ElectroDildo',
            46: 'ElectroWand',
            47: 'FaceMask',
            48: 'Hair',
            49: 'Paddle',
            50: 'Padlock',
            51: 'RingGag',
            52: 'Rope',
            53: 'Star',
            54: 'Stocks',
            55: 'Tonker',
        }

        def eval_full_script(self, script_string):
            triad_shop_assignment_command = re.match("^\$triad_shop =", script_string)
            if triad_shop_assignment_command:
                return True

            return False

        def eval_script(self, line, script_string):
            gain_triad_card_command = re.match("gain_triad_card\((\d+), (\d+)\)", line)
            triad_game_command = re.match("triple_triad\((\d+)\)", line)
            chain_commands_command = re.match("chain_commands\((\d+)\)", line)
            disable_choice_command = re.match("disable_choice\((\d+),\s*\"!\$game_switches\[(\d+)\]\"\)", line)

            if gain_triad_card_command:
                groups = gain_triad_card_command.groups()
                card_id, amount = (int(groups[0]), int(groups[1]))
                game_state.say_text(None, "Gained %s DickUp card: %s" % (amount, GameSpecificCodeMilfsControl.CARD_NAMES[card_id]))
                # TODO: save card so later card ownership commands will work
            elif triad_game_command:
                groups = triad_game_command.groups()
                enemy_id = (int(groups[0]))

                win_variable = 1
                num_duels_variable = 2
                num_won_variable = 3
                num_lost_variable = 4
                num_draw_variable = 5

                game_state.variables.operate_variable(num_duels_variable, 1, 1)

                result = renpy.display_menu([("A card battle is happening!", None), ("You Win!", 1), ("You Draw!", 2), ("You Lose!", 3)])
                game_state.variables.set_value(win_variable, result)

                if result == 1:
                    game_state.variables.operate_variable(num_won_variable, 1, 1)
                elif result == 2:
                    game_state.variables.operate_variable(num_draw_variable, 1, 1)
                elif result == 3:
                    game_state.variables.operate_variable(num_lost_variable, 1, 1)

            elif disable_choice_command:
                groups = disable_choice_command.groups()
                choice_index = int(groups[0])
                switch_id = int(groups[1])
                if game_state.switches.value(switch_id) != True:
                    game_state.events[-1].disable_choice(choice_index)
            elif line == "Tidloc.exe \"LockPick\",:game,0,5,":
                game_state.say_text(None, "You picked the lock!")
                game_state.switches.set_value(100, True)
            elif chain_commands_command:
                groups = chain_commands_command.groups()
                switch_id = (int(groups[0]))

                # Skip command minigame in Milf's Control
                game_state.switches.set_value(switch_id, True)
            elif "start_range_game(" in script_string:
                return True
            elif script_string == "SceneManager.call(Shop_Triple_Triad)":
                game_state.say_text(None, "Card Shop not implemented!")
                return True
            else:
                return False

            return True

        def conditional_eval_script(self, script_string):
            if script_string == 'game_result(:range) == true':
                return True
            else:
                renpy.say(None, "Conditional statements for Script not implemented")
                return False

        def has_curated_clickables(self, map_id):
            return map_id == 24

        def curated_clickables(self, coordinates, map_id):
            result = []
            if map_id == 24:
                # The RPGM implementation of this screen splits the events into two segments that look like this:
                # [x][x]
                # [x][x]
                # [x]            [x][x]
                # [x]
                # In RPGM, you use the arrow keys to move your little man and press the action key to activate the events.
                # The upper-leftmost one teleports the little man to the group on the right hand side.
                #
                # For RenPy, each of these events is mapped to a hardcoded clickable area on the screen.
                # The events on the right hand side only show up if the player is in one of those locations (has opened context menu)

                mappings = {
                  (6,3): (35, 45, 120, 120),
                  (6,4): (35, 175, 120, 120),
                  (6,5): (35, 310, 120, 120),
                  (6,6): (35, 435, 120, 120),
                  (7,3): (165, 45, 120, 120),
                  (7,4): (165, 175, 120, 120),
                  (6, 15): (315, 125, 150, 150),
                  (7, 15): (470, 125, 150, 150),
                }
                contextual_coords = [(6, 15), (7, 15)]
                for coord in coordinates:
                    if (coord.x, coord.y) in contextual_coords and (game_state.player_x, game_state.player_y) not in contextual_coords:
                        continue

                    if mappings[(coord.x, coord.y)]:
                        mapping = mappings[(coord.x, coord.y)]
                        coord.reachable = True
                        coord.clicky = True
                        coord.teleport = True
                        result.append({
                            "xpos": mapping[0],
                            "ypos": mapping[1],
                            "xsize": mapping[2],
                            "ysize": mapping[3],
                            "coord": coord
                        })
                    else:
                        renpy.say(None, "No mapping for coord: %s, %s" % (coord.x, coord.y))

            return result