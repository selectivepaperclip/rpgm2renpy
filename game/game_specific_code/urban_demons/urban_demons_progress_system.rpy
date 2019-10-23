init python:
    class GameSpecificCodeUrbanDemonsProgressVars():
        def __init__(self):
            self.actor_id = []
            self.progress_level = []
            self.var_id = []
            self.inf_score = []
            self.is_blackmailed = []
            self.complete_dialogue_levels = []
            self.current_dialogue_levels = []
            self.actor_outfit = []

    class GameSpecificCodeUrbanDemonsProgressSystem():
        # Nergal's Progression System (Progression_System.rb from urban demons)
        # - Re-usable for commerical use, just credit needed

        # Name of states (used for UI display in phone)
        STATE_NAMES = ["Acquaintance","Shocked","Hesitant","Pleasured","Corrupted","Broken"]
        #Max level is derived from the number of states defined above
        MAX_LEVEL = len(STATE_NAMES) - 1

        MAX_INF = 100
        MIN_INF = -100

        QUICK_PROGRESS_SWITCH_ID = 90
        SKIP_MINI_GAME_SWITCH_ID = 91

        SEX_VARS = [1031,1045,1065,1066,1085,1163,1183,1206,1223]

        ###Create Methods

        @classmethod
        def create_new_progress(cls, id, silent_add = False):
          if cls.progress_exists(id):
            return

          game_state.ud_progress.actor_id.append(id)
          game_state.ud_progress.progress_level.append(0)
          game_state.ud_progress.var_id.append(1000 + id)
          game_state.ud_progress.inf_score.append(0)
          game_state.ud_progress.is_blackmailed.append(False)

          game_state.ud_progress.current_dialogue_levels.append([0,0,0,0,0,0])

          if game_state.switches.value(cls.QUICK_PROGRESS_SWITCH_ID) == True:
            game_state.ud_progress.complete_dialogue_levels.append([True,True,True,True,True,True])
          else:
            game_state.ud_progress.complete_dialogue_levels.append([False,False,False,False,False,False])

          game_state.ud_progress.actor_outfit.append("default")

          if silent_add == False:
            cls.show_popup("Progress",id,0, False, True)

        ###End of Create Methods

        ###Read Methods

        @classmethod
        def return_progress_level(cls, id):
          if cls.progress_exists(id) == False:
            return 0

          return game_state.ud_progress.progress_level[game_state.ud_progress.actor_id.index(id)]

        @classmethod
        def return_progress_level_string(cls, id):
          lvl_string = ""

          level = cls.return_progress_level(id)

          if level == 0:
            lvl_string = cls.check_overwrites(id)

          if lvl_string != "":
            return lvl_string

          return cls.STATE_NAMES[level]

        @classmethod
        def check_overwrites(cls, id):
          if id == 2:
            return "Mother"

          if id == 3:
            return "Sister"

          if id == 4:
            return "Teacher"

          if id == 7:
            return "Nurse"

          return ""

        @classmethod
        def return_inf_score(cls, id):
          if cls.progress_exists(id) == False:
            return 0

          return game_state.ud_progress.inf_score[game_state.ud_progress.actor_id.index(id)]

        @classmethod
        def return_total_inf(cls):
          total_score = 0
          for score in game_state.ud_progress.inf_score:
            if score < 0:
              score = score * -1
            total_score += score

          return total_score

        @classmethod
        def progress_exists(cls, id):
          return id in game_state.ud_progress.actor_id

        @classmethod
        def is_blackmailed(cls, id):
          index = game_state.ud_progress.actor_id.index(id)

          if index == None:
            return False

          return game_state.ud_progress.is_blackmailed[index]

        @classmethod
        def is_purity(cls, id):
          score = cls.return_inf_score(id)

          if score < 0:
            return False
          else:
            return True

        @classmethod
        def is_mc_pure(cls):
          total_score = 0
          for score in game_state.ud_progress.inf_score:
            total_score = total_score + score

          if total_score < 0:
            return False

          return True

        @classmethod
        def current_dialogue_complete(cls, id):
          if cls.progress_exists(id) == False:
            return False

          dialogues = game_state.ud_progress.complete_dialogue_levels[game_state.ud_progress.actor_id.index(id)]
          prog_lvl = cls.return_progress_level(id)
          if prog_lvl >= len(dialogues):
            print "ERROR - Dialogue returned nil for level: " + prog_lvl.to_s + " for actor: " + id.to_s + " when performing read."
            return False

          return dialogues[prog_lvl]

        @classmethod
        def is_dialogue_complete(cls, id, prog_lvl):

          if cls.progress_exists(id) == False:
            return False

          dialogues = game_state.ud_progress.complete_dialogue_levels[game_state.ud_progress.actor_id.index(id)]

          if prog_lvl >= len(dialogues):
            print "ERROR - Dialogue returned nil for level: " + prog_lvl.to_s + " for actor: " + id.to_s + " when performing read."
            return False

          return dialogues[prog_lvl]

        @classmethod
        def get_current_dialogue_level(cls, id):
          if cls.progress_exists(id) == False:
            return False

          dialogues = game_state.ud_progress.current_dialogue_levels[game_state.ud_progress.actor_id.index(id)]
          prog_lvl = cls.return_progress_level(id)

          if prog_lvl >= len(dialogues):
            print "ERROR - Dialogue returned nil for level: " + prog_lvl.to_s + " for actor: " + id.to_s + " when performing read."
            return False

          return dialogues[prog_lvl]

        @classmethod
        def get_actor_outfit(cls, id):
          if cls.progress_exists(id) == False:
            return "default"

          return game_state.ud_progress.actor_outfit[game_state.ud_progress.actor_id.index(id)]

        ###End of Read Methods

        ###Update Methods

        @classmethod
        def increase_progress_level(cls, id, silent_add = False, amount = 1):
          maxed = False

          if cls.progress_exists(id) == False:
            create_new_progress(id,silent_add)

          #Don't want them to go beyond max level
          if cls.return_progress_level(id) == cls.MAX_LEVEL:
            return

          index = game_state.ud_progress.actor_id.index(id)

          game_state.ud_progress.progress_level[index] += amount

          current_progress = game_state.variables.value(game_state.ud_progress.var_id[index])
          game_state.variables.set_value(game_state.ud_progress.var_id[index], current_progress + amount)

          if cls.return_progress_level(id) == cls.MAX_LEVEL:
            maxed = True

          if silent_add == False:
            cls.show_popup("Progress",id,amount, maxed)

        @classmethod
        def give_purity(cls, id, silent_add = False, amount = 1):
          maxed = False

          if cls.progress_exists(id) == False:
            create_new_progress(id,silent_add)

          #Don't want them to go beyond max level
          if cls.return_inf_score(id) >= cls.MAX_INF:
            return

          index = game_state.ud_progress.actor_id.index(id)

          prog_level = game_state.ud_progress.progress_level[index]

          modifier = prog_level * 2

          amount = amount + modifier

          game_state.ud_progress.inf_score[index] += amount

          if cls.return_inf_score(id) > cls.MAX_INF:
            game_state.ud_progress.inf_score[index] = cls.MAX_INF
            maxed = True

          if silent_add == False:
            cls.show_popup("Purity",id,amount,maxed)

        @classmethod
        def give_corruption(cls, id, silent_add = False, amount = 1):
          maxed = False
          if cls.progress_exists(id) == False:
            cls.create_new_progress(id,silent_add)

          #Don't want them to go beyond max level
          if cls.return_inf_score(id) <= cls.MIN_INF:
            return

          index = game_state.ud_progress.actor_id.index(id)

          prog_level = game_state.ud_progress.progress_level[index]

          modifier = prog_level * 2

          amount = amount + modifier

          game_state.ud_progress.inf_score[index] = game_state.ud_progress.inf_score[index] - amount

          if cls.return_inf_score(id) < cls.MIN_INF:
            game_state.ud_progress.inf_score[index] = cls.MIN_INF
            maxed = True

          if silent_add == False:
            cls.show_popup("Corrupt",id,amount,maxed)

        @classmethod
        def set_blackmail(cls, id):
          index = game_state.ud_progress.actor_id.index(id)

          give_corruption(id,False,100)

          game_state.ud_progress.is_blackmailed[index] = True

        @classmethod
        def complete_current_dialogue_level(cls, id):
          if cls.progress_exists(id) == False:
            return

          index = game_state.ud_progress.actor_id.index(id)
          prog_lvl = cls.return_progress_level(id)

          game_state.ud_progress.complete_dialogue_levels[index][prog_lvl] = True

        @classmethod
        def complete_dialogue_level(cls, id, dialog_lvl):
          if cls.progress_exists(id) == False:
            return

          index = game_state.ud_progress.actor_id.index(id)

          if dialog_lvl >= len(dialogues):
            print "ERROR - Dialogue returned nil for level: " + dialog_lvl.to_s + " for actor: " + id.to_s + " when performing update"
            return

          game_state.ud_progress.complete_dialogue_levels[index][dialog_lvl] = True

        @classmethod
        def update_dialogue_level(cls, id):
          if cls.progress_exists(id) == False:
            return False

          index = game_state.ud_progress.actor_id.index(id)

          prog_lvl = cls.return_progress_level(id)

          if game_state.ud_progress.current_dialogue_levels[index][prog_lvl] == 2:
            game_state.ud_progress.current_dialogue_levels[index][prog_lvl] = 0
            cls.complete_current_dialogue_level(id)
            cls.show_dialogue_popup()
          else:
            game_state.ud_progress.current_dialogue_levels[index][prog_lvl] += 1

        @classmethod
        def update_actor_outfit(cls, id, outfit):
          if cls.progress_exists(id) == False:
            return

          index = game_state.ud_progress.actor_id.index(id)

          game_state.ud_progress.actor_outfit[index] = outfit

        @classmethod
        def remove_blackmail(cls, id):
          index = game_state.ud_progress.actor_id.index(id)

          game_state.ud_progress.is_blackmailed[index] = False

        @classmethod
        def cleanse_character(cls, id):
          index = game_state.ud_progress.actor_id.index(id)

          if cls.progress_exists(id) == False:
            return

          game_state.ud_progress.progress_level[index]  = cls.MAX_LEVEL

          game_state.variables.set_value(game_state.ud_progress.var_id[index], cls.MAX_LEVEL)

        ###End of Update Methods

        ###Misc Methods - mainly for phone

        @classmethod
        def return_actor_ids(cls):
          return game_state.ud_progress.actor_id

        ###End of Misc Methods

        ### Popup

        @classmethod
        def show_popup(cls, type,actor,value, maxed = False, new_prog = False):
          game_state.say_debug("Added %s %s to %s" % (value, type, game_state.actors.actor_name(actor)))
          return True

          # TODO

        @classmethod
        def show_dialogue_popup(cls):
          return True

          # TODO

        @classmethod
        def can_progress(cls, id):
            if not game_state.switches.value(50):
                return False

            #If Quick Progression Mode enabled return true
            if game_state.switches.value(90) or cls.is_blackmailed(id):
                return True

            return cls.current_dialogue_complete(id)
