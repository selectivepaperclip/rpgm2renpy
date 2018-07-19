init python:
    class GameIdentifier:
        def is_milfs_villa(self):
            return game_state.system_data()['gameTitle'] == 'Milfs Villa v1.0 Final'
        def is_ics2(self):
            return game_state.system_data()['gameTitle'] == 'Incest Story 2 v1.0 Final'
        def is_taboo_request(self):
            return game_state.system_data()['gameTitle'] == 'Taboo Request'
