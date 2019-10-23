init python:
    class GameSpecificCodeUrbanDemonsDayTime():
      # Nergal's Day Time System (Day_Time_System.rb from Urban Demons)
      # - Re-usable for commerical use, just credit needed

      #Array must match number of days in week
      PERIODS_OF_DAY_NAMES = ["Morning", "Midday", "Afternoon", "Evening", "Night"]

      PERIOD_TIMES = ["08:00","12:30","16:00","19:30","00:00"]

      #Array must match number of days in week
      DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

      #Array must match number of months
      MONTHS_OF_YEAR = ["January","February","March","April","May","June","July","August","September","October","November","December"]

      DAYS_OF_MONTHS = [31,28,31,30,31,30,31,31,30,31,30,31]

      TIME_OF_DAY_VAR = 2
      DAY_VAR = 3
      DATE_VAR = 4
      MONTH_VAR = 5
      YEAR_VAR = 6

      PERIOD_CHANGE_COMMON_EVENT = 26 #This common even will run whenever the period of day changes
      DAY_CHANGE_COMMON_EVENT = 27 #This common event will run whenever the day changes
      MONTH_CHANGE_COMMON_EVENT = 28 #This common event will run whenever the month changes
      YEAR_CHANGE_COMMON_EVENT = 29 #This common event will run whenevr the year changes

      NO_OF_PERIODS = len(PERIODS_OF_DAY_NAMES) - 1
      DAYS_PER_WEEK = len(DAY_NAMES) - 1
      MONTHS_IN_YEAR = len(MONTHS_OF_YEAR) - 1

      @classmethod
      def advance_day(cls):
        current_time_of_day = game_state.variables.value(cls.TIME_OF_DAY_VAR)
        if current_time_of_day == cls.NO_OF_PERIODS:
          game_state.variables.set_value(cls.TIME_OF_DAY_VAR, 0)
          cls.increase_date()
        else:
          game_state.variables.set_value(cls.TIME_OF_DAY_VAR, current_time_of_day + 1)
          game_state.queue_common_event(cls.PERIOD_CHANGE_COMMON_EVENT)

      @classmethod
      def increase_date(cls):
        current_day = game_state.variables.value(cls.DAY_VAR)
        if current_day == cls.DAYS_PER_WEEK:
          game_state.variables.set_value(cls.DAY_VAR, 0)
        else:
          game_state.variables.set_value(cls.DAY_VAR, current_day + 1)

        current_date = game_state.variables.value(cls.DATE_VAR)
        current_month = game_state.variables.value(cls.MONTH_VAR)
        if current_date == cls.DAYS_OF_MONTHS[current_month]:
           game_state.variables.set_value(cls.DATE_VAR, 1)
           cls.increase_month()
        else:
           game_state.variables.set_value(cls.DATE_VAR, current_date + 1)
           game_state.queue_common_event(cls.DAY_CHANGE_COMMON_EVENT)

      @classmethod
      def increase_month(cls):
        current_month = game_state.variables.value(cls.MONTH_VAR)
        if current_month == cls.MONTHS_IN_YEAR:
          game_state.variables.set_value(cls.MONTH_VAR, 0)
          cls.increase_year()
        else:
          game_state.variables.set_value(cls.MONTH_VAR, current_month + 1)
          game_state.queue_common_event(cls.MONTH_CHANGE_COMMON_EVENT)

      @classmethod
      def increase_year(cls):
        current_year = game_state.variables.value(cls.YEAR_VAR)
        game_state.variables.set_value(cls.YEAR_VAR, current_year + 1)
        game_state.queue_common_event(cls.YEAR_CHANGE_COMMON_EVENT)

      @classmethod
      def get_current_time_period(cls):
        return cls.get_time_period(game_state.variables.value(cls.TIME_OF_DAY_VAR))

      @classmethod
      def get_time_period(cls, period):
        return cls.PERIODS_OF_DAY_NAMES[period]

      @classmethod
      def get_current_day_name(cls):
        return cls.get_day_name(game_state.variables.value(cls.DAY_VAR))

      @classmethod
      def get_day_name(cls, day):
          return cls.DAY_NAMES[day]

      @classmethod
      def get_current_month_name(cls):
        return cls.get_month_name(game_state.variables.value(cls.MONTH_VAR))

      @classmethod
      def get_month_name(cls, month):
          return cls.MONTHS_OF_YEAR[month]

      @classmethod
      def get_current_date_full(cls):
        period = cls.get_current_time_period
        day = cls.get_current_day_name()
        date = game_state.variables.value(cls.DATE_VAR)
        month = cls.get_current_month_name()
        year = game_state.variables.value(cls.YEAR_VAR)

        return "%s: %s %s %s %s" % (period, day, date, month, year)

      @classmethod
      def get_phone_time(cls):
        return cls.PERIOD_TIMES[game_state.variables.value(cls.TIME_OF_DAY_VAR)]

      @classmethod
      def get_phone_date(cls):
        day_char = cls.get_current_day_name()[0:3]
        date = game_state.variables.value(cls.DATE_VAR)
        month = cls.get_current_month_name()[0:3]

        return "%s %s %s" % (day_char, date, month.upper())

      @classmethod
      def get_current_date(cls):
        period = cls.get_current_time_period()
        day = cls.get_current_day_name()[0:3]
        date = game_state.variables.value(cls.DATE_VAR)
        month = cls.get_current_month_name()[0:3]

        return "%s: %s %s %s" % (period, day, date, month)
