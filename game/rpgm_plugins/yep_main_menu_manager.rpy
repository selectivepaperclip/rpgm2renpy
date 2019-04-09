init python:
    class YepMainMenuManager:
        @classmethod
        def plugin_active(cls):
            plugin = game_file_loader.plugin_data_exact('YEP_MainMenuManager')
            if not plugin:
                return False
            return plugin['status']

        @classmethod
        def menu_options(cls):
            if not cls.plugin_active():
                return []

            plugin = game_file_loader.plugin_data_exact('YEP_MainMenuManager')
            params = plugin['parameters']
            result = []
            for i in xrange(1, 101):
                if params['Menu %d Show' % i] == 'true' and params['Menu %d Enabled' % i] == 'true':
                    if params['Menu %d Main Bind' % i] == "this.callCommonEvent.bind(this)":
                        result.append((eval(params['Menu %d Name' % i]), int(params['Menu %d Ext' % i])))
            return result

        @classmethod
        def menu(cls):
            options = cls.menu_options()
            if len(options) == 0:
                return

            options.append(("Exit", -1))
            result = renpy.display_menu(options)
            if result != -1:
                game_state.queue_common_event(result)
