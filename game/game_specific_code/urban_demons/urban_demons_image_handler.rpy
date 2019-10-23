init python:
    class GameSpecificCodeUrbanDemonsImageHandler():
        Gallery_Store_Var = 16
        Gallery_Sold_Var = 35
        Gallery_Uploaded_Var = 36
        Gallery_Video_Var = 37
        Gallery_Video_Uploaded_Var = 38

        @classmethod
        def add_pic(cls, name):
          if game_state.variables.value(cls.Gallery_Store_Var) == 0:
            game_state.variables.set_value(cls.Gallery_Store_Var, [])

          game_state.variables.value(cls.Gallery_Store_Var).append(name)

        @classmethod
        def does_have_pic(cls, name):
          if game_state.variables.value(cls.Gallery_Store_Var) == 0:
            return False

          return name in game_state.variables.value(cls.Gallery_Store_Var)

        @classmethod
        def sell_pic(cls, name):
          if game_state.variables.value(cls.Gallery_Sold_Var) == 0:
            game_state.variables.set_value(cls.Gallery_Sold_Var, [])

          game_state.variables.value(cls.Gallery_Sold_Var).append(name)

        @classmethod
        def has_sold_pic(cls, name):
          if game_state.variables.value(cls.Gallery_Sold_Var) == 0:
            return False

          return pic in game_state.variables.value(cls.Gallery_Sold_Var)

        @classmethod
        def can_sell_pic(cls, name):
          if has_sold_pic(name):
            return False

          return does_have_pic(name)

        @classmethod
        def upload_pic(cls, name):
          if game_state.variables.value(cls.Gallery_Uploaded_Var) == 0:
            game_state.variables.set_value(cls.Gallery_Uploaded_Var, [])

          game_state.variables.value(cls.Gallery_Uploaded_Var).append(name)

        @classmethod
        def is_uploaded(cls, name):
          if game_state.variables.value(cls.Gallery_Uploaded_Var) == 0:
            return False

          return pic in game_state.variables.value(cls.Gallery_Uploaded_Var)

        @classmethod
        def add_video(cls, name):
          if game_state.variables.value(cls.Gallery_Video_Var) == 0:
            game_state.variables.set_value(cls.Gallery_Video_Var, [])

          game_state.variables.value(cls.Gallery_Video_Var).append(name)

        @classmethod
        def upload_video(cls, name):
          if game_state.variables.value(cls.Gallery_Video_Uploaded_Var) == 0:
            game_state.variables.set_value(cls.Gallery_Video_Uploaded_Var, [])

          game_state.variables.value(cls.Gallery_Video_Uploaded_Var).append(name)

        @classmethod
        def is_video_uploaded(cls, name):
          if game_state.variables.value(cls.Gallery_Video_Uploaded_Var) == 0:
            return False

          return pic in game_state.variables.value(cls.Gallery_Video_Uploaded_Var)
