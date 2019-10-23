init python:
    class GameSpecificCodeUrbanDemonsTextMessageSystem():
        FOLDER_LOC = "Data/Text Messages/"
        TEXT_CHOICES_LOC = FOLDER_LOC + "Text Choices/"
        
        TEXT_DELAY_COUNT = 15
        
        DELAY_COUNT_VAR = 17
        TEXT_TO_SEND_VAR = 18
        
        TEXT_ORDER_VAR = 19

        @classmethod
        def send_text(cls, name):
          # Audio.se_play("Audio/SE/computer_instant_message_alert_02", 100, 100)
          renpy.notify("New Message Received")
          
          if game_state.variables.value(cls.TEXT_ORDER_VAR) == 0:
            game_state.variables.set_value(cls.TEXT_ORDER_VAR, [])

          text_order = game_state.variables.value(cls.TEXT_ORDER_VAR)
          text_order.unshift(name)
          game_state.variables.set_value(cls.TEXT_ORDER_VAR, text_order)

          # TODO: it truncated the array to length 4 for some reason here

          cls.execute_commands(name)

        @classmethod
        def execute_commands(cls, name):
          gre = Re()
          commands = cls.get_message_commands(name)

          triggered_switches = re.findall("<trigger-switch:(\d+)>", commands)
          for switch_string in triggered_switches:
              game_state.switches.set_value(int(switch_string), True)

          vars_to_set = re.findall("<set-variable:(\d+\|\d+)>", commands)
          for val in vars_to_set:
              vals = val.split("|")

              var_to_change = int(vals[0])
              value_to_set = int(vals[1])

              game_state.variables.set_value(var_to_change, value_to_set)

          vars_to_increase = re.findall("<increase-variable:(\d+\|\d+)>", commands)
          for val in vars_to_increase:
              vals = val.split("|")

              var_to_change = int(vals[0])
              value_to_modify = int(vals[1])

              game_state.variables.set_value(var_to_change, game_state.variables.value(var_to_change) + value_to_modify)

          vars_to_decrease = re.findall("<decrease-variable:(\d+\|\d+)>", commands)
          for val in vars_to_decrease:
              vals = val.split("|")

              var_to_change = int(vals[0])
              value_to_modify = int(vals[1])

              game_state.variables.set_value(var_to_change, game_state.variables.value(var_to_change) - value_to_modify)

          purity_inc = re.findall("<increase-purity:(\d+\|\d+)>", commands)
          for val in purity_inc:
              vals = val.split("|")

              actor_id = int(vals[0])
              value = int(vals[1])

              GameSpecificCodeUrbanDemonsProgressSystem.give_purity(actor_id, value)

          corruption_inc = re.findall("<increase-corruption:(\d+\|\d+)>", commands)
          for val in corruption_inc:
              vals = val.split("|")

              actor_id = int(vals[0])
              value = int(vals[1])

              GameSpecificCodeUrbanDemonsProgressSystem.give_corruption(actor_id, value)

          if gre.search("<add-photo:(.+)>", commands):
              name = gre.last_match.groups()[0]

              if game_state.variables.value(GameSpecificCodeUrbanDemonsImageHandler.Gallery_Store_Var) == 0:
                game_state.variables.set_value(GameSpecificCodeUrbanDemonsImageHandler.Gallery_Store_Var, [])

              gallery_store = game_state.variables.value(GameSpecificCodeUrbanDemonsImageHandler.Gallery_Store_Var)
              gallery_store.push(name)

        @classmethod
        def get_message_text(cls, name):
          message = cls.get_raw_message(name)
          
          if message == None:
            return "ERROR LOADING MESSAGE TEXT FOR: " + name

          text = ""

          gre = Re()
          if gre.search(re.compile("<message>(.+)</message>", re.DOTALL)):
              text = gre.last_match.groups()[0].strip()
              
              if text == "":
                text = "NO MESSAGE TEXT LOADED FOR: " + name
          else:
              text = "NO MESSAGE TEXT LOADED FOR: " + name

          return text

        @classmethod
        def get_message_sender(cls, name):
          message = cls.get_raw_message(name)
          
          if message == None:
            return "ERROR LOADING MESSAGE SENDER FOR: " + name
              
          sender = ""

          gre = Re()
          if gre.search(re.compile("<sender>(.+)</sender>", re.DOTALL)):
              sender = gre.last_match.groups()[0].strip()
              
              if sender == "":
                sender = "NO MESSAGE SENDER LOADED FOR: " + name
          else:
              sender = "NO MESSAGE SENDER LOADED FOR: " + name
                
          return sender

        @classmethod
        def get_message_commands(cls, name):
          message = cls.get_raw_message(name)
              
          if message == None:
            return "ERROR LOADING MESSAGE COMMANDS FOR: " + name
          
          commands = ""

          gre = Re()
          if gre.search(re.compile("<commands>(.+)</commands>", re.DOTALL)):
              commands = gre.last_match.groups()[0]

          return commands

        @classmethod
        def get_raw_message(cls, name):
          data = None
          with rpgm_file(cls.FOLDER_LOC + name + ".txt") as journal_file:
            data = journal_file.read()
          return data

        @classmethod
        def get_all_available_texts(cls):
          return_list = []
          
          if game_state.variables.value(cls.TEXT_ORDER_VAR) == 0:
            return return_list

          for text in game_state.variables.value(cls.TEXT_ORDER_VAR):
            new_text = []

            text_sender = cls.get_message_sender(text)
            text_message = cls.get_message_text(text)

            new_text.append(text_sender)
            new_text.append(text_message)
            
            return_list.append(new_text)

          return return_list

        @classmethod
        def get_player_send_text_options(cls, actor_id):
          file = None
          with rpgm_file(cls.TEXT_CHOICES_LOC + str(actor_id) + ".txt") as send_text_file:
            file = send_text_file.read()

          if file == None:
            print "failed to load: " + str(actor_id) + ".txt"
            return

          choices = []

          #EVALUATION|DISPLAY VALUE|TEXT VALUE|REPLY TEXT
          choice_lines = re.findall('<choice:(.+)\|(.+)\|(.+)\|(.+)\>', data)
          for (evaluation, display_name, text_value, reply_text) in choice_lines:
              if evaluation == None:
                print "evaluation == None"

              result = game_state.eval_fancypants_value_statement(evaluation)
              
              if result == False:
                continue

              text_value = re.sub(r'N<(\d+)>', lambda m: (self.actors.actor_name(int(m.group(1)))), text_value)

              choices.append([display_name,text_value, reply_text])

          return choices
