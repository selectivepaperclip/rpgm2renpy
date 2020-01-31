init python:
    class YepXExtMesPack1(RpgmPlugin):
        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('YEP_X_ExtMesPack1')

        @classmethod
        def process_script(cls, event, line, script_string):
            if not cls.plugin_active():
                return False

            gre = Re()
            if gre.match("\$gameSystem\.clearChoiceSettings", line):
                del event.choices_to_hide[:]
                del event.choices_to_disable[:]
                return True
            elif gre.match("\$gameSystem\.hideChoice\((\d+)", line):
                choice_id = int(gre.last_match.groups()[0])
                event.hide_choice(choice_id)
                return True

            return False

        @classmethod
        def process_command(cls, event, command, command_args):
            if not cls.plugin_active():
                return False

            if command in ['ChoiceRowMax']:
                return True
            elif command in ['ClearHiddenChoices']:
                del event.choices_to_hide[:]
                return True
            elif command in ['ClearDisabledChoices']:
                del event.choices_to_disable[:]
                return True
            elif command in ['ClearChoiceSettings']:
                del event.choices_to_hide[:]
                del event.choices_to_disable[:]
                return True

            return False
