screen molegato_quests_screen(
    unsolved_quests = [],
    solved_quests = []
):
    modal True
    add Solid(Color("#000", alpha = 0.75))
    frame:
        area (0.1, 0.1, 800, 500)
        vbox:
            viewport:
                scrollbars "vertical"
                mousewheel True
                vbox:
                    for quest in unsolved_quests:
                        text "Name: %s" % quest['name']
                        text quest['description']
                        text quest['long_text']
                        null height 20
                    if len(solved_quests) > 0:
                        null height 20
                        text "vv SOLVED vv"
                        null height 20
                        for quest in solved_quests:
                            text "Name: %s" % quest['name']
                            text quest['description']
                            text quest['long_text']
                            null height 20

        textbutton "Close":
            xalign 1.0
            background "#00c"
            hover_background "#00f"
            action Return(0)