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

        def eval_script(self, line, script_string):
            gain_triad_card_command = re.match("gain_triad_card\((\d+), (\d+)\)", line)
            triad_game_command = re.match("triple_triad\((\d+)\)", line)
            chain_commands_command = re.match("chain_commands\((\d+)\)", line)

            if gain_triad_card_command:
                groups = gain_triad_card_command.groups()
                card_id, amount = (int(groups[0]), int(groups[1]))
                renpy.say(None, "Gained %s DickUp card: %s" % (amount, GameSpecificCodeMilfsControl.CARD_NAMES[card_id]))
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

            elif line == "Tidloc.exe \"LockPick\",:game,0,5,":
                renpy.say(None, "You picked the lock!")
                game_state.switches.set_value(100, True)
            elif chain_commands_command:
                groups = chain_commands_command.groups()
                switch_id = (int(groups[0]))

                # Skip command minigame in Milf's Control
                game_state.switches.set_value(switch_id, True)
            else:
                return False

            return True