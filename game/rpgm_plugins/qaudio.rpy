init python:
    class QAudio(RpgmPlugin):
        COMMANDS = [
            'qaudio'
        ]

        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('QAudio')

        @classmethod
        def process_command(cls, event, command, command_args):
            if not cls.plugin_active():
                return False

            if command.lower() in QAudio.COMMANDS:
                return True

            return False