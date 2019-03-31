screen galv_quests_screen(
    quest_data
):
    modal True
    add Solid(Color("#000", alpha = 0.75))
    frame:
        area (0.1, 0.1, int(config.screen_width * 0.8), 500)
        vbox:
            viewport:
                scrollbars "vertical"
                mousewheel True
                vbox:
                    for quest in quest_data:
                        text "Name: %s" % quest['name']
                        if quest['status'] == 1:
                            text "**COMPLETED**":
                                color "#0f0"
                        if quest['status'] == 2:
                            text "**FAILED**":
                                color "#f00"
                        if 'resolution' in quest:
                            text quest['resolution']:
                                color "#00f"
                        text quest['description']
                        if len(quest['objectives']) > 0:
                            text 'Objectives:'
                        for objective in quest['objectives']:
                            text objective['text']:
                                if objective['completed']:
                                    color "#0f0"
                                if objective['failed']:
                                    color "#f00"
                        null height 20

                textbutton "Close":
                    xalign 1.0
                    background "#00c"
                    hover_background "#00f"
                    action Return(0)