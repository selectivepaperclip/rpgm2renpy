init -99 python:
    class RpgmPlugin(object):
        @classmethod
        def plugin_active(cls):
            return False

        @classmethod
        def process_command(cls, command, command_args):
            return False

        @classmethod
        def process_script(cls, event, line, script_string):
            return False
