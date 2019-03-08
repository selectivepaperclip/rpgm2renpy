screen gameus_quests_screen(
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
                        if quest['status'] == 'completed':
                            text "**COMPLETED**":
                                color "#0f0"
                        if quest['status'] == 'failed':
                            text "**FAILED**":
                                color "#f00"
                        text quest['description']
                        if len(quest['steps']) > 0:
                            text 'Steps:'
                        for step in quest['steps']:
                            text "* %s" % step['text']:
                                if step['completed']:
                                    color "#0f0"
                                if step['failed']:
                                    color "#f00"
                        null height 20
                        text '-------------------'
                        null height 20

                textbutton "Close":
                    xalign 1.0
                    background "#00c"
                    hover_background "#00f"
                    action Return(0)