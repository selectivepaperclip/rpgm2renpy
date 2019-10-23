init python:
    class GameSpecificCodeUrbanDemonsScenePhone():
        def __init__(self):
            pass

        def background_name(self):
            return "PhoneBackground-%s" % game_state.variables.value(20)

        def do_next_thing(self):
            contacts = [
                GameSpecificCodeUrbanDemonsContact(actor_id) for actor_id in
                GameSpecificCodeUrbanDemonsProgressSystem.return_actor_ids()
            ]

            renpy.show_screen(
                "urban_demons_phone",
                background = rpgm_path("Graphics/Phone/%s.png" % self.background_name()),
                date = GameSpecificCodeUrbanDemonsDayTime.get_phone_date(),
                time = GameSpecificCodeUrbanDemonsDayTime.get_phone_time(),
                contacts = contacts
            )
            return True

    class GameSpecificCodeUrbanDemonsContact():
        def __init__(self, actor_id):
            self.actor_id = actor_id
            self.name = game_state.actors.actor_name(actor_id)
            self.progress_level = GameSpecificCodeUrbanDemonsProgressSystem.return_progress_level(actor_id)
            self.progress_string = GameSpecificCodeUrbanDemonsProgressSystem.return_progress_level_string(actor_id)
            self.inf_score = GameSpecificCodeUrbanDemonsProgressSystem.return_inf_score(actor_id)
            if self.inf_score >= 0:
                self.inf_icon = rpgm_path("Graphics/Phone/purity_icon.png")
            else:
                self.inf_icon = rpgm_path("Graphics/Phone/corrupt_icon.png")
            self.inf_icon = im.Scale(self.inf_icon, 25, 25)

            if self.progress_level == 5:
                self.bust = self.name + '-nude-4'
            elif self.progress_level >= 3:
                self.bust = self.name + '-4'
            else:
                self.bust = self.name + '-1'

            self.bust_image = im.Scale(
                im.Crop(
                    GameSpecificCodeUrbanDemonsMessageBusts.bust_filename(self.bust, transform = False),
                    (160, 0, 650, 960)
                ),
                168,
                200
            )
