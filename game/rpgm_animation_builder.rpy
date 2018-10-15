init python:
    class RpgmAnimationBuilder():
        def __init__(self, picture_frames):
            self.picture_frames = picture_frames

        @classmethod
        def image_for_picture(cls, picture_frame):
            return Transform(
                child = picture_frame['image_name'],
                xpos = picture_frame.get('x', 0),
                ypos = picture_frame.get('y', 0),
                size = picture_frame.get('size', None),
            )

        def build(self, loop = False):
            picture_transitions = []
            for i, picture_frame in enumerate(self.picture_frames):
                picture_transitions.append(RpgmAnimationBuilder.image_for_picture(picture_frame))
                wait_seconds = 0
                if 'wait' in picture_frame:
                    wait_seconds = (picture_frame['wait'] / animation_fps)

                if i + 1 < len(self.picture_frames):
                    next_picture_frame = self.picture_frames[i + 1]
                    if 'x' in picture_frame and (next_picture_frame['x'] != picture_frame['x'] or next_picture_frame['y'] != picture_frame['y']):
                        picture_transitions.append(0.0001)
                        picture_transitions.append(MoveTransition(picture_frame.get('wait', 0.001) / animation_fps))
                    else:
                        picture_transitions.append(wait_seconds)
                        picture_transitions.append(None)
                    if not loop and (i + 1 == len(self.picture_frames) - 1): # Last Frame
                        picture_transitions.append(RpgmAnimationBuilder.image_for_picture(next_picture_frame))
                        break
                else:
                    picture_transitions.append(wait_seconds)
                    picture_transitions.append(None)

            return picture_transitions