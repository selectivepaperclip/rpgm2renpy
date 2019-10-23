screen urban_demons_phone(
    background,
    date,
    time,
    contacts
):
    modal True
    add Solid(Color("#000"))
    add background
    add rpgm_path("Graphics/Phone/PhoneForeground.png")

    button:
        xpos 0
        ypos 0
        xsize config.screen_width
        ysize 200
        action Hide("urban_demons_phone")

    button:
        xpos 0
        ypos 760
        xsize config.screen_width
        ysize config.screen_height
        action Hide("urban_demons_phone")

    text date:
        xpos 210
        ypos 242
        size 32

    text time:
        xpos 600
        ypos 242
        size 32

    button:
        xpos 182 + 20 + 130 * 0
        ypos 232 + 80
        xsize 110
        background rpgm_path("Graphics/Phone/message_icon.png")
        action Show("urban_demons_phone_messages", messages = GameSpecificCodeUrbanDemonsTextMessageSystem.get_all_available_texts())

    button:
        xpos 182 + 20 + 130 * 1
        ypos 232 + 80
        xsize 110
        background rpgm_path("Graphics/Phone/rel_icon.png")
        action Show("urban_demons_phone_contacts", contacts = contacts)

    button:
        xpos 182 + 20 + 130 * 2
        ypos 232 + 80
        xsize 110
        background rpgm_path("Graphics/Phone/pic_icon.png")

    button:
        xpos 182 + 20 + 130 * 3
        ypos 232 + 80
        xsize 110
        background rpgm_path("Graphics/Phone/note_icon.png")
        action Show("urban_demons_phone_notes", journal_name = "General", notes = GameSpecificCodeUrbanDemonsJournalSystem.get_all_available_entries(0))

screen urban_demons_phone_messages(
    messages
):
    modal True
    frame:
        xpos 182
        ypos 299
        xsize 892
        ysize 450
        background Solid(Color("#000"))

        viewport:
            scrollbars "vertical"
            mousewheel True

        vbox:
            text "Messages" size 40

            for (message_sender, message_text) in messages:
                text game_state.replace_names(message_sender)
                text game_state.replace_names(message_text)
                null height 10

        button:
            xpos 200
            ypos 200
            background rpgm_path("Graphics/Phone/back-icon.png")
            action Hide('urban_demons_phone_messages')

screen urban_demons_phone_contacts(
    contacts
):
    modal True
    frame:
        xpos 182
        ypos 299
        xsize 892
        ysize 450
        background Solid(Color("#000"))

        viewport:
            scrollbars "vertical"
            mousewheel True

            vbox:
                for contact in contacts:
                    hbox:
                        vbox:
                            add contact.bust_image
                            null height 10
                        vbox:
                            null height 80
                            text contact.name min_width 160
                        vbox:
                            null height 80
                            text "%s (%s)  " % (contact.progress_level, contact.progress_string) min_width 220
                        vbox:
                            null height 80
                            hbox:
                                add contact.inf_icon
                                text " %s/100" % contact.inf_score min_width 160
                        vbox:
                            null height 65
                            hbox:
                                button:
                                    background im.Scale(rpgm_path("Graphics/Phone/message_icon.png"), 55, 55)
                                    action Show("urban_demons_phone_messages", messages = [])
                                    xsize 55
                                    ysize 55
                                button:
                                    background im.Scale(rpgm_path("Graphics/Phone/note_icon.png"), 55, 55)
                                    action Show(
                                        "urban_demons_phone_notes",
                                        journal_name = game_state.actors.actor_name(contact.actor_id),
                                        notes = GameSpecificCodeUrbanDemonsJournalSystem.get_all_available_entries(contact.actor_id)
                                    )
                                    xsize 55
                                    ysize 55

        button:
            xpos 500
            ypos 400
            background rpgm_path("Graphics/Phone/back-icon.png")
            action Hide('urban_demons_phone_contacts')


screen urban_demons_phone_notes(
    journal_name,
    notes
):
    modal True
    frame:
        xpos 182
        ypos 299
        xsize 892
        ysize 450
        background Solid(Color("#000"))

        vbox:
            text ("Journal - %s" % journal_name) size 40
            null height 20

            for (note_title, note_desc) in notes:
                text game_state.replace_names(note_title)
                text game_state.replace_names(note_desc)
                null height 10

        button:
            xpos 200
            ypos 200
            background rpgm_path("Graphics/Phone/back-icon.png")
            action Hide('urban_demons_phone_notes')
