screen maic_quests_screen(
    quest_data
):
    modal True
    add Solid(Color("#000", alpha = 0.75))
    frame:
        area (0.25, 0.1, 500, 500)
        vbox:
            viewport:
                scrollbars "vertical"
                mousewheel True
                vbox:
                    for quest in quest_data:
                        text "Name: %s" % quest['name']
                        if 'location' in quest:
                            text "Location: %s" % quest['location']
                        text quest['description']
                        if 'objectives' in quest:
                            text 'Objectives:'
                            for objective in quest['objectives']:
                                text objective['text']:
                                    if objective['completed']:
                                        color "#0f0"
                        null height 20

                textbutton "Close":
                    xalign 1.0
                    background "#00c"
                    hover_background "#00f"
                    action Return(0)