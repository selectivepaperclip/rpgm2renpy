screen yep_quests_screen(
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
                        text "Title: %s" % quest['title']
                        text "Location: %s" % quest['location']
                        text "From: %s" % quest['from']
                        if quest['status'] == 'completed':
                            text "**COMPLETED**":
                                color "#0f0"
                        if quest['status'] == 'failed':
                            text "**FAILED**":
                                color "#f00"
                        text quest['description']
                        text quest['subtext']
                        if len(quest['objectives']) > 0:
                            text 'Objectives:'
                        for objective in quest['objectives']:
                            text "* %s" % objective['text']:
                                if objective['completed']:
                                    color "#0f0"
                                if objective['failed']:
                                    color "#f00"
                        if len(quest['rewards']) > 0:
                            text 'Rewards:'
                        for reward in quest['rewards']:
                            text "* %s" % reward['text']:
                                if reward['claimed']:
                                    color "#0f0"
                                if reward['denied']:
                                    color "#f00"
                        null height 20
                        text '-------------------'
                        null height 20

                textbutton "Close":
                    xalign 1.0
                    background "#00c"
                    hover_background "#00f"
                    action Return(0)