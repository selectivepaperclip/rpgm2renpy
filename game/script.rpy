define mapdest = None

init python:
    import json

    for ix in range(0, 16 + 1):
        renpy.image("Intro %i" % ix, "unpacked/www/img/pictures/Intro %i.png" % ix)

    class GameEvent:
        def __init__(self, event_data):
            self.event_data = event_data
            self.list_index = 0
            self.new_map_id = None
            self.x = None
            self.y = None

        def do_next_thing(self):
            if not self.done():
                list_item = self.event_data['pages'][0]['list'][self.list_index]

                if list_item['code'] == 401 and len(list_item['parameters']) > 0 and list_item['parameters'][0][0] != "\\":
                    renpy.say(None, list_item['parameters'][0])
                elif list_item['code'] == 201:
                    method, self.new_map_id, self.new_x, self.new_y = list_item['parameters'][0:4]
                    if method != 0:
                        renpy.say(None, "Method on transfer was nonzero (%d), plz implement!" % method)

                elif list_item['code'] == 231:
                    renpy.scene()
                    renpy.show(list_item['parameters'][1])
                    renpy.pause()

                self.list_index += 1

        def done(self):
            return self.list_index == len(self.event_data['pages'][0]['list'])

    class GameMap:
        def __init__(self, map_id, x, y):
            self.map_id = map_id
            self.x = x
            self.y = y
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

        def map_options(self):
            coords = []
            for e in self.data['events']:
                if e:
                    if e['pages'][0]['conditions']['variableId'] == 1:
                        if e['pages'][0]['trigger'] != 3:
                            coords.append((e['x'], e['y']))

            return coords

    class GameState:
        def __init__(self, starting_map_id, starting_x, starting_y):
            self.event = None
            self.starting_map_id = starting_map_id
            self.ran_auto_trigger_events = False
            self.map = GameMap(starting_map_id, starting_x, starting_y)

        def do_next_thing(self, mapdest):
            if self.event:
                self.event.do_next_thing()
                if self.event.done():
                    if self.event.new_map_id:
                        self.map = GameMap(self.event.new_map_id, self.event.new_x, self.event.new_y)
                    self.event = None
                return True

            if not self.ran_auto_trigger_events:
                self.event = self.map.find_auto_trigger_event()
                self.ran_auto_trigger_events = True
                return True

            if mapdest:
                self.event = self.map.find_event_for_location(mapdest[0], mapdest[1])
                renpy.say(None, "%d,%d" % mapdest)
                return True

            coordinates = self.map.map_options()
            renpy.call_screen("mapscreen", coords = coordinates)

screen mapscreen:
    for i, coord in enumerate(coords):
        button xalign (coord[0] / 80.0) yalign (coord[1] / 64.0) xsize 8 ysize 8 background "#f00":
            action SetVariable("mapdest", coord), Jump("game")

label start:
    python:
        with open("/Users/tjgrathwell/renpy/projects/ics2/game/unpacked/www/data/System.json") as f:
            system_data = json.load(f)
            game_state = GameState(system_data['startMapId'], system_data['startX'], system_data['startY'])

label game:
    $ end_game = False

    while end_game == False:
        $ game_state.do_next_thing(mapdest)
        $ mapdest = None

    return