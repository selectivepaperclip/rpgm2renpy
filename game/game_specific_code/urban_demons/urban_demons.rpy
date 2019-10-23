init python:
    class GameSpecificCodeUrbanDemons():
        PERSUADE_RETURN_SWITCH = 50
        PERSUASION_DISCOVERED_SWITCH = 1003

        def __init__(self):
            if not hasattr(game_state, 'ud_progress'):
                game_state.ud_progress = GameSpecificCodeUrbanDemonsProgressVars()

        def say_text(self, speaker, spoken_text, face_name, face_index):
            if not face_name or len(face_name) == 0:
                return

            game_state.rpgm_side_image = None
            game_state.rpgm_bust_image = None
            if face_name and len(face_name) > 0:
                game_state.rpgm_bust_image = GameSpecificCodeUrbanDemonsMessageBusts.bust_filename("%s-%s" % (face_name, face_index + 1))

                self.last_said_text = spoken_text
                renpy.say(speaker, spoken_text)

            return True

        def eval_script(self, line, script_string):
            gre = Re()
            if line.startswith('play_animation'):
                return self._eval_play_animation_script(line, script_string)
            elif line.startswith('Day_Time'):
                return self._eval_day_time_script(line, script_string)
            elif gre.search('Day_Time\.get_current_date', script_string):
                # The only time this is used currently is to flash ("gab") the date on certain transitions
                renpy.notify(GameSpecificCodeUrbanDemonsDayTime.get_current_date())
                return True
            elif line.startswith('SceneManager.call(Map_Transfer)'):
                game_state.scenes.append(GameSpecificCodeUrbanDemonsSceneMap())
                return True
            elif line.startswith('SceneManager.call(Scene_Phone)'):
                game_state.scenes.append(GameSpecificCodeUrbanDemonsScenePhone())
                return True
            elif line.startswith('DoorMove'):
                return True
            elif '$game_map.effect_surface' in script_string:
                return True
            elif '$game_map.lantern' in script_string:
                return True
            elif line == 'clear_gab':
                return True
            elif line == '':
                return True
            elif gre.match('create_new_progress\((\d+)(?:,(.*?))?\)', line):
                actor_id = int(gre.last_match.groups()[0])
                silent_add_condition = gre.last_match.groups()[1]
                if silent_add_condition == 'true':
                    silent_add_condition = True
                elif silent_add_condition == 'false':
                    silent_add_condition = False
                elif silent_add_condition == None:
                    silent_add_condition = False
                else:
                    silent_add_condition = game_state.eval_fancypants_value_statement(silent_add_condition)
                GameSpecificCodeUrbanDemonsProgressSystem.create_new_progress(id = actor_id, silent_add = silent_add_condition)
                return True
            elif gre.match('give_(purity|corruption)\((\d+),(\d+)\)', line):
                purity_or_corruption = gre.last_match.groups()[0]
                actor_id = int(gre.last_match.groups()[1])
                amount = int(gre.last_match.groups()[2])
                if purity_or_corruption == 'purity':
                    GameSpecificCodeUrbanDemonsProgressSystem.give_purity(id = actor_id, amount = amount)
                if purity_or_corruption == 'corruption':
                    GameSpecificCodeUrbanDemonsProgressSystem.give_corruption(id = actor_id, amount = amount)
                return True
            elif gre.match('update_dialogue_level\((\d+)\)', line):
                actor_id = int(gre.last_match.groups()[0])
                GameSpecificCodeUrbanDemonsProgressSystem.update_dialogue_level(actor_id)
                return True
            elif gre.match('(add_pic|does_have_pic|sell_pic|has_sold_pic|can_sell_pic|upload_pic|is_uploaded|add_video|upload_video|is_video_uploaded)\??\((.*)\)', line):
                fn = gre.last_match.groups()[0]
                name = gre.last_match.groups()[1]
                getattr(GameSpecificCodeUrbanDemonsImageHandler, fn)(eval(name))
                return True
            elif gre.match("persuade_start", line):
                if not game_state.switches.value(self.__class__.PERSUASION_DISCOVERED_SWITCH):
                    game_state.switches.set_value(self.__class__.PERSUADE_RETURN_SWITCH, False)
                else:
                    # Normally a minigame would happen, instead always return true
                    game_state.switches.set_value(self.__class__.PERSUADE_RETURN_SWITCH, True)
                return True
            elif gre.match("(disable|hide)_choice\((\d+),\"(.*)\"\)", line):
                disable_or_hide = gre.last_match.groups()[0]
                choice_id = int(gre.last_match.groups()[1])
                condition = gre.last_match.groups()[2]
                condition_value = game_state.eval_fancypants_value_statement(condition)
                event = game_state.top_event()
                if condition_value:
                    if disable_or_hide == 'disable':
                        event.disable_choice(choice_id)
                    else:
                        event.hide_choice(choice_id)
                return True

            return False

        def _eval_play_animation_script(self, line, script_string):
            gre = Re()
            if gre.match('play_animation\("(\w+)",(\d)(?:,(true|false))?', line):
                # play_animation is New_Scene_Player.rb
                scene_name = gre.last_match.groups()[0]
                actor_id = int(gre.last_match.groups()[1])

                folder_name = game_state.actors.actor_name(actor_id)

                new_scene = GameSpecificCodeUrbanDemonsSceneAnimation(
                    scene_name = scene_name,
                    folder_name = folder_name,
                    folder_name_ext = '-purity', # TODO - based on functions ilike is_blackmailed?
                    dialogue_level = 0, # TODO: based on progress system
                    actor_id = actor_id
                )
                game_state.scenes.append(new_scene)

                return True

            return False

        def _eval_day_time_script(self, line, script_string):
            gre = Re()
            if gre.match('Day_Time\.advance_day', line):
                GameSpecificCodeUrbanDemonsDayTime.advance_day()
                return True
            elif gre.match('Day_Time\.increase_date', line):
                GameSpecificCodeUrbanDemonsDayTime.increase_date()
                return True
            elif gre.match('Day_Time\.increase_month', line):
                GameSpecificCodeUrbanDemonsDayTime.increase_month()
                return True
            elif gre.match('Day_Time\.increase_year', line):
                GameSpecificCodeUrbanDemonsDayTime.increase_year()
                return True

            return False

        def eval_fancypants_value_statement(self, script_string, return_remaining = False, event = None):
            reduced_terms = False
            gre = Re()

            replacers = (
              (re.compile('can_progress\?\((\d+)\)'), lambda m: str(GameSpecificCodeUrbanDemonsProgressSystem.can_progress(int(gre.last_match.groups()[0])))),
              (re.compile('Progress_System\.current_dialogue_complete\?\((\d+)\)'), lambda m: str(GameSpecificCodeUrbanDemonsProgressSystem.current_dialogue_complete(int(gre.last_match.groups()[0])))),
              (re.compile('Progress_System\.is_blackmailed\?\((\d+)\)'), lambda m: str(GameSpecificCodeUrbanDemonsProgressSystem.is_blackmailed(int(gre.last_match.groups()[0])))),
              (re.compile('Progress_System\.is_purity\?\((\d+)\)'), lambda m: str(GameSpecificCodeUrbanDemonsProgressSystem.is_purity(int(gre.last_match.groups()[0])))),
            )

            for (r, l) in replacers:
                while gre.search(r, script_string):
                    reduced_terms = True
                    script_string = re.sub(r, l, script_string)

            if gre.match('(add_pic|does_have_pic|sell_pic|has_sold_pic|can_sell_pic|upload_pic|is_uploaded|add_video|upload_video|is_video_uploaded)\??\((.*)\)', script_string):
                fn = gre.last_match.groups()[0]
                name = gre.last_match.groups()[1]
                return getattr(GameSpecificCodeUrbanDemonsImageHandler, fn)(eval(name))
            elif gre.match('is_purity\?\((\d+)\)', script_string):
                return GameSpecificCodeUrbanDemonsProgressSystem.is_purity(int(gre.last_match.groups()[0]))
            elif gre.match('get_current_dialogue_level\((\d+)\)', script_string):
                return GameSpecificCodeUrbanDemonsProgressSystem.get_current_dialogue_level(int(gre.last_match.groups()[0]))
            if reduced_terms:
                return game_state.eval_fancypants_value_statement(script_string, return_remaining, event)

            return