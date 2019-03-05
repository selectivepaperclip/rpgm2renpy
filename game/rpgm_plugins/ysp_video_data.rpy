init python:
    class YspVideoData:
        def __init__(self):
            self.data = {}

        def new_video(self, id, path):
            self.data[id] = path

        def video_by_id(self, id):
            return self.data[id]
