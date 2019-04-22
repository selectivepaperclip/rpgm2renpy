init python:
    class GameSpecificCodeLustEpidemic():
        def eval_full_script(self, script_string):
            gre = Re()
            if re.match('\$gameScreen\.clearPictures\(\);', script_string):
                del game_state.queued_pictures[:]
                game_state.shown_pictures.clear()
                return True

            script_lines = script_string.split("\n")
            intro_lines = [
                "var xhr = new XMLHttpRequest();",
                "xhr.open(\"GET\",\"names.txt\",false);",
                "xhr.send(null); ",
                "var fileContent = xhr.responseText.split(\",\");"
            ]
            if script_lines[0:4] == intro_lines:
                names_txt = renpy.file(rpgm_path('www/names.txt')).read().split(",")
                if gre.match('var res = (.*)', script_lines[4]) and len(script_lines) == 6:
                    replaced = re.sub('res', gre.last_match.groups()[0], script_lines[5])
                    replaced = re.sub('fileContent\[(\d+)\]', lambda m: "\"%s\"" % names_txt[int(m.group(1))], replaced)

                    if gre.match('\$gameVariables\.setValue\((\d+), (.*)\)', replaced):
                        variable_id = int(gre.last_match.groups()[0])
                        game_state.variables.set_value(variable_id, game_state.eval_fancypants_value_statement(gre.last_match.groups()[1]))
                        return True

            if gre.match('var ([^\s]+) = (.*)', script_lines[0]) and len(script_lines) == 2:
                replaced = re.sub(gre.last_match.groups()[0], gre.last_match.groups()[1], script_lines[1])

                if gre.match('\$gameVariables\.setValue\((\d+), (.*)\)', replaced):
                    variable_id = int(gre.last_match.groups()[0])
                    game_state.variables.set_value(variable_id, game_state.eval_fancypants_value_statement(gre.last_match.groups()[1]))
                    return True

            if gre.match("if\s*\(\$gameVariables\.value\((\d+)\) == \"([^\"]*)\"\)\s*\{\s*\$gameVariables\.setValue\((\d+),\s*(\d+)\)\s*\}\s*", script_string):
                variable_check_id = int(gre.last_match.groups()[0])
                str_to_check = gre.last_match.groups()[1]
                variable_set_id = int(gre.last_match.groups()[2])
                value_to_set = int(gre.last_match.groups()[3])
                if game_state.variables.value(variable_check_id) == str_to_check:
                    game_state.variables.set_value(variable_set_id, value_to_set)
                return True

            msgset_lines = [
                "var MSGperson = $gameVariables.value(21).slice(0,2);",
                "var MSGemotion = $gameVariables.value(21).slice(3,5);",
                "var MSGbody = $gameVariables.value(21).slice(6,8);",
                "var MSGmessage = $gameVariables.value(21).slice(9);",
                "$gameVariables.setValue(22, MSGperson);",
                "$gameVariables.setValue(23, MSGemotion);",
                "$gameVariables.setValue(24, MSGbody);",
                "$gameVariables.setValue(25, MSGmessage);"
            ]
            if script_lines == msgset_lines:
                gv_21 = game_state.variables.value(21)
                msg_person = gv_21[0:2]
                msg_emotion = gv_21[3:5]
                msg_body = gv_21[6:8]
                msg_message = gv_21[9:-1]
                game_state.variables.set_value(22, msg_person)
                game_state.variables.set_value(23, msg_emotion)
                game_state.variables.set_value(24, msg_body)
                game_state.variables.set_value(25, msg_message)
                return True

            voperson_lines = [
                "var VOperson = $gameVariables.value(50).slice(0,2);",
                "var VOemotion = $gameVariables.value(50).slice(3,5);",
                "var VObradaim = $gameVariables.value(50).slice(6,8);",
                "$gameVariables.setValue(51, VOperson);",
                "$gameVariables.setValue(52, VOemotion);",
                "$gameVariables.setValue(34, VObradaim);"
            ]
            if script_lines == voperson_lines:
                gv_50 = game_state.variables.value(50)
                vo_person = gv_50[0:2]
                vo_emotion = gv_50[3:5]
                vo_bradaim = gv_50[6:8]
                game_state.variables.set_value(51, vo_person)
                game_state.variables.set_value(52, vo_emotion)
                game_state.variables.set_value(34, vo_bradaim)
                return True

        def eval_script(self, line, script_string):
            pass
