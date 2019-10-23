init python:
    class GameSpecificCodeUrbanDemonsSceneMap():
        def __init__(self):
            glob_string = os.path.join(config.basedir, rpgm_path("Data/Map"), "*")
            files = glob.glob(glob_string)
            game_state.urban_demons_locations = [GameSpecificCodeUrbanDemonsLocation(file) for file in files]

        def background_name(self):
            if game_state.switches.value(10):
                return "MainMap - Morning.png"
            elif game_state.switches.value(13):
                return "MainMap - Evening.png"
            elif game_state.switches.value(14):
                return "MainMap - Night.png"
            else:
                return "MainMap.jpeg"

        def do_next_thing(self):
            renpy.show_screen(
                "urban_demons_map",
                background = rpgm_path("Graphics/Map/%s" % self.background_name()),
                locations = game_state.urban_demons_locations,
                location_icon = rpgm_path("Graphics/Map/Pointer.png")
            )
            return True

    class GameSpecificCodeUrbanDemonsLocation():
      def __init__(self, file_path):
        with renpy.file(file_path.replace('\\', '/')) as f:
            self.map_data_to_loc(f.read())

      @classmethod
      def transfer(cls, location):
          renpy.hide_screen("urban_demons_map")

          game_state.reset_user_zoom()
          game_state.focus_zoom_rect_on_next_map_render = True
          game_state.map = game_state.map_registry.get_map(location.transfer_id)
          game_state.map.update_for_transfer()
          game_state.player_x = location.transfer_x
          game_state.player_y = location.transfer_y
          # TODO: direction?

          # TODO: dry this up with the game_state code?
          del game_state.parallel_events[:]
          if hasattr(game_state, 'move_routes'):
              del game_state.move_routes[:]
          else:
              game_state.move_routes = []
          game_state.queue_common_and_parallel_events()

      def map_data_to_loc(self, data):
        gre = Re()
        if gre.search("<name:(.+)>", data):
            self.name = gre.last_match.groups()[0]

        if gre.search("<x:(.+)>", data):
            self.x_loc = int(gre.last_match.groups()[0])

        if gre.search("<y:(.+)>", data):
            self.y_loc = int(gre.last_match.groups()[0])

        if gre.search("<transfer-map-id:(.+)>", data):
            self.transfer_id = int(gre.last_match.groups()[0])

        if gre.search("<transfer-map-x:(.+)>", data):
            self.transfer_x = int(gre.last_match.groups()[0])

        if gre.search("<transfer-map-y:(.+)>", data):
            self.transfer_y = int(gre.last_match.groups()[0])

        self.chars_available  = []
        self.chars_not_present = []

        # TODO: chars available / unavailable logic
        return

        #Actor ID | Day | Time | Is There Eval | Player Know Eval
        #<loc:(.+)\|(.+)\|(.+)|(.+)|(.+)\>
        #if match = data.scan(/<loc:(.+)\|(.+)\|(.+)\|(.+)>/) then
        #  match.each do | cur_match |
        #    actor_id = cur_match[0]
        #    day = cur_match[1].to_i #1-7 = Monday - Sunday, 8 = Weekdays 9 = Weekends
        #    time = cur_match[2].to_i
        #    does_player_know = cur_match[3]
        #
        #    result = eval(does_player_know)
        #
        #    self.chars_not_present.push [actor_id, day, time, result]
