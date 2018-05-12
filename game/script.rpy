init python:
    import json

    for ix in range(0, 16 + 1):
        renpy.image("Intro %i" % ix, "unpacked/www/img/pictures/Intro %i.png" % ix)

    class GameEvent:
        def __init__(self, event_data):
            self.event_data = event_data
            self.list_index = 0

        def do_next_thing(self):
            if not self.done():
                list_item = self.event_data['pages'][0]['list'][self.list_index]

                if list_item['code'] == 401 and len(list_item['parameters']) > 0 and list_item['parameters'][0][0] != "\\":
                    renpy.say(None, list_item['parameters'][0])
                elif list_item['code'] == 231:
                    renpy.scene()
                    renpy.show(list_item['parameters'][1])
                    renpy.pause()

                self.list_index += 1

        def done(self):
            return self.list_index == len(self.event_data['pages'][0]['list'])

    class GameMap:
        def __init__(self, map_id):
            with open("/Users/tjgrathwell/renpy/projects/ics2/game/unpacked/www/data/Map0%d.json" % map_id) as f:
                self.data = json.load(f)

        def find_event_for_location(self, x, y):
            for e in self.data['events']:
                if e and e['x'] == x and e['y'] == y:
                    return GameEvent(e)
            return None

        def find_auto_trigger_event(self):
            for e in self.data['events']:
                if e and e['pages'][0]['trigger'] == 3:
                    return GameEvent(e)
            return None

        def show_map_options(self):
            coords = []
            for e in self.data['events']:
                if e:
                    coords.append(("%d,%d" % (e['x'], e['y']), (e['x'], e['y'])))

            return renpy.display_menu(coords)

    class GameState:
        def __init__(self, starting_map_id):
            self.event = None
            self.starting_map_id = starting_map_id
            self.ran_auto_trigger_events = False
            self.map = GameMap(starting_map_id)

        def do_next_thing(self):
            if self.event:
                self.event.do_next_thing()
                if self.event.done():
                    self.event = None
                return True

            if not self.ran_auto_trigger_events:
                self.event = self.map.find_auto_trigger_event()
                self.ran_auto_trigger_events = True
                return True

            chosen_coordinates = self.map.show_map_options()
            if chosen_coordinates:
                self.event = self.map.find_event_for_location(chosen_coordinates[0], chosen_coordinates[1])


label start:
    $ game_state = GameState(42)

    $ end_game = False

    while end_game == False:
        $ game_state.do_next_thing()

    return
