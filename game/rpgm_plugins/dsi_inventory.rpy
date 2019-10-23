init python:
    # Special code only for Farmer's Dreams, inventory
    class DsiInventory:
        @classmethod
        def plugin_active(cls):
            return game_file_loader.has_active_plugin('DSI-Inventory')

        @classmethod
        def eval_fancypants_value_statement(self, script_string):
            gre = Re()
            if gre.match('\$gameParty\.canGainItem', script_string):
                return True

            return None
