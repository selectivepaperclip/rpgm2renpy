init python:
    class YepXExtMesPack1:
        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('YEP_MainMenuManager')

        @classmethod
        def valid_command(cls, plugin_command):
            if not cls.plugin_active:
                return False
            if plugin_command in ['ChoiceRowMax']:
                return True
