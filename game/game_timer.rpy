init python:
    class GameTimer(object):
        def __init__(self):
            self.active = False
            self.frames = 0

        def start(self, seconds):
            self.frames = seconds * 60
            self.active = True

        def stop(self):
            self.active = False

        def finish(self):
            self.frames = 0

        def seconds(self):
            if self.active:
                return self.frames / 60
            else:
                return None
