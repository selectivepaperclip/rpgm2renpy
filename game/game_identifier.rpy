init python:
    class GameIdentifier:
        def is_milfs_control(self):
            return rpgm_game_data.get('long_name', '') == "Milf's Control"
        def is_milfs_villa(self):
            return game_state.system_data()['gameTitle'] == 'Milfs Villa v1.0 Final'
        def is_ics2(self):
            return game_state.system_data()['gameTitle'] == 'Incest Story 2 v1.0 Final'
        def is_taboo_request(self):
            return game_state.system_data()['gameTitle'] == 'Taboo Request'
        def is_my_summer(self):
            return game_state.system_data()['gameTitle'] == 'My Summer with Mom & Sis v1.00'
        def is_visiting_sara(self):
            return game_state.system_data()['gameTitle'].startswith('Visiting Sara')
