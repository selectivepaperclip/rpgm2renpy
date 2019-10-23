init python:
    class GameSpecificCodeUrbanDemonsMessageBusts():
        @classmethod
        def bust_filename(cls, filename, transform = True):
          strings = filename.split('-')
          actor_name = strings[0]

          if actor_name == "MsAmos":
            actor_name = "Ms Amos"

          act_id = cls.get_actor_id_from_name(actor_name)

          # Default appears as "default-1" so check to see if default bust or not
          if cls.is_i(strings[1]):
            bust_type = "default"
            number = strings[1]
          else:
            bust_type = strings[1]
            number = strings[2]

          # Check if any of the xrays are active
          if game_state.switches.value(45) or game_state.switches.value(44):
            bust_type = cls.get_xray_bust_type(bust_type, actor_name, act_id)
          else:
            bust_type = cls.get_normal_bust_type(bust_type, act_id)

          image = rpgm_path("Graphics/Busts/" + actor_name + "/" + bust_type + "/" + number + '.png').replace("\\", "/")
          if actor_name == game_state.actors.actor_name(1):
              image = im.Flip(
                  image,
                  horizontal = True
              )

          if transform:
              return Transform(
                  child = image,
                  xpos = 320
              )
          else:
              return image

        @classmethod
        def is_i(cls, string):
           return re.match('^[-+]?[0-9]+$', string)

        @classmethod
        def get_xray_bust_type(cls, bust_type, actor_name, act_id):
          # If major x-ray is active
          # Show nude regardless of factors
          if game_state.switches.value(45):
            return "nude"

          if bust_type != "default":
            return bust_type

          # If minor is active check if character owns lingerie
          # Show that, show underwear if that exists
          # Else just show whatever it would normally
          if cls.check_actor_level(act_id,5) and cls.own_actor_lingerie(act_id):
            return "lingerie"
          elif cls.does_clothing_folder_exist(actor_name, "underwear"):
            return "underwear"
          else:
            return bust_type

        @classmethod
        def get_normal_bust_type(cls, bust_type, act_id):
          # If character is nude / swimsuit / cosplay etc
          # We don't want to overwrite their outfit with something else
          if bust_type != "default":
            return bust_type

          # Check if a default has been set on the progression system
          # Otherwise check if character is wearing lingerie under default
          if cls.check_for_default(act_id) != "default":
            return cls.check_for_default(act_id)
          elif cls.check_actor_level(act_id,5) and cls.own_actor_lingerie(act_id):
              return "default-lingerie"
          else:
            return "default"

        @classmethod
        def check_actor_level(cls, actor_id, target):
           if actor_id < 2 or actor_id == None:
             return False

           return GameSpecificCodeUrbanDemonsProgressSystem.return_progress_level(actor_id) == target

        @classmethod
        def check_for_default(cls, actor_id):
          outfit = GameSpecificCodeUrbanDemonsProgressSystem.get_actor_outfit(actor_id)

          if outfit == None:
            return "default"

          return outfit

        @classmethod
        def get_actor_id_from_name(cls, actor_name):
          max_i = 20
          i = 1

          while i <= max_i:
            name_to_check = game_state.actors.actor_name(i).lower()

            if name_to_check == actor_name.lower():
              return i

            i = i + 1

          return 0

        @classmethod
        def does_clothing_folder_exist(cls, actor_name,folder):
          return True

        @classmethod
        def own_actor_lingerie(cls, act_id):
          switch_no = 920 + act_id

          return game_state.switches.value(switch_no)
