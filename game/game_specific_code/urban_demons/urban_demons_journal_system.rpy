init python:
    class GameSpecificCodeUrbanDemonsJournalSystem():
        FOLDER_LOC = "Data/Journal/"
        COMMANDS_NAME = "JournalCommands"

        @classmethod
        def get_all_available_entries(cls, actor_id):
          return_list = []

          folder_loc = cls.FOLDER_LOC + str(actor_id) + "/"

          with rpgm_file(folder_loc + cls.COMMANDS_NAME + ".txt") as journal_file:
              data = journal_file.read()
              #EVALUATION|DISPLAY VALUE|TEXT VALUE|REPLY TEXT|SWITCH TO SET
              entry_lines = re.findall('<entry:(.+)\|(.+)\|(.+)\>', data)
              for (evaluation, display_name, file_name) in entry_lines:
                result = game_state.eval_fancypants_value_statement(evaluation)

                if result == False:
                  continue

                text_value = cls.get_entry(file_name, folder_loc)

                return_list.append([display_name,text_value])

          return return_list

        @classmethod
        def get_entry(cls, file_name, folder_loc):
          result = ''
          try:
              with rpgm_file(folder_loc + file_name + ".txt") as entry_file:
                  result = entry_file.read()
          except IOError:
              pass
          return result
