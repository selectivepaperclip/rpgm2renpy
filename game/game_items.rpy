init python:
    class GameItems(SelectivelyPickle):
        def __init__(self):
            pass

        def data(self):
            if not hasattr(self, '_data'):
                with renpy.file('unpacked/www/data/Items.json') as f:
                    self._data = json.load(f)

            return self._data

        def by_id(self, id):
            for item in self.data():
                if item and item['id'] == id:
                    return item
            return None
