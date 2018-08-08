#=begin
#***********************************************************************
# Version 2.0
# 2018.01.20
#***********************************************************************

module DEGICA
  module CONVERT
    LOGGING = true # only useful for debugging this script
    LOGSCRIPTS = true # lists any damage formulae and event commands using scripts - you'll need to convert these manually
    LOGCOMMENTS = true # only turn this on if you have scripts that look for certain comments and want to re-implement them

    def self.run(destination_folder:, map_files:)
      @destination_folder = destination_folder
      DataManager.load_normal_database

      #*************************************************************************
      @log = File.open(@destination_folder + "_log.txt", "w") if LOGGING
      @scriptlog = File.open(@destination_folder + "_scripts.txt", "w") if LOGSCRIPTS
      @commentlog = File.open(@destination_folder + "_comments.txt", "w") if LOGCOMMENTS
      #*************************************************************************

      convert_actors
      #convert_classes
      #convert_skills
      convert_items
      convert_weapons
      convert_armors
      #convert_enemies
      #convert_troops
      #convert_states
      #convert_animations
      convert_tilesets
      convert_common_events
      convert_system
      convert_mapinfos

      convert_maps(map_files)

      #*************************************************************************
      @log.close if LOGGING
      @scriptlog.close if LOGSCRIPTS
      @commentlog.close if LOGCOMMENTS
      #*************************************************************************
    end

    #===========================================================================
    #
    # DATABASE CONVERSION
    #
    #===========================================================================

    #===========================================================================
    # ACTORS
    #===========================================================================
    def self.convert_actors
      f = File.open(@destination_folder + "Actors.json", "w")
      f.puts('[')
      f.puts('null,')
      for x in 1 ... $data_actors.size
        actor = $data_actors[x]
        actor = RPG::Actor.new if !actor
        actor_data = '{'

        actor_data += '"id":' + x.to_s + ','
        actor_data += '"battlerName":"",'
        actor_data += '"characterIndex":' + actor.character_index.to_s + ','
        actor_data += '"characterName":"' + actor.character_name + '",'
        actor_data += '"classId":' + actor.class_id.to_s + ','
        actor_data += '"equips":' + actor.equips.to_s.gsub(/ /){''} + ','
        actor_data += '"faceIndex":' + actor.face_index.to_s + ','
        actor_data += '"faceName":"' + actor.face_name + '",'
        actor_data += '"traits":' + get_traits(actor) + ','
        actor_data += '"initialLevel":' + actor.initial_level.to_s + ','
        actor_data += '"maxLevel":' + actor.max_level.to_s + ','
        actor_data += '"name":' + get_text(actor.name) + ','
        actor_data += '"nickname":' + get_text(actor.nickname) + ','
        actor_data += '"note":' + get_text(actor.note) + ','
        actor_data += '"profile":' + get_text(actor.description)

        actor_data += '}'
        actor_data += ',' if x < $data_actors.size - 1
        f.puts(actor_data)
      end
      f.puts(']')
      f.close
    end

    #===========================================================================
    # CLASSES
    #===========================================================================
    def self.convert_classes
      f = File.open(@destination_folder + "Classes.json", "w")
      f.puts('[')
      f.puts('null,')
      for x in 1 ... $data_classes.size
        cls = $data_classes[x]
        cls = RPG::Class.new if !cls
        cls_data = '{'

        cls_data += '"id":' + x.to_s + ','
        cls_data += '"expParams":' + cls.exp_params.to_s.gsub(/ /){''} + ','
        cls_data += '"traits":' + get_traits(cls) + ','
        cls_data += '"learnings":' + get_learnings(cls) + ','
        cls_data += '"name":' + get_text(cls.name) + ','
        cls_data += '"note":' + get_text(cls.note) + ','
        cls_data += '"params":' + get_params(cls)

        cls_data += '}'
        cls_data += ',' if x < $data_classes.size - 1
        f.puts(cls_data)
      end
      f.puts(']')
      f.close
    end

    def self.get_learnings(obj)
      res = '['
      count = 1
      max_count = obj.learnings.size
      obj.learnings.each do |lrn|
        res += '{"level":' + lrn.level.to_s + ','
        res += '"note":' + get_text(lrn.note) + ','
        res += '"skillId":' + lrn.skill_id.to_s + '}'
        res += ',' if count < max_count
        count += 1
      end
      res += ']'
      res
    end

    def self.get_params(cls)
      res = '['
      for p in 0..7
        res += '['
        for l in 0..99
          res += cls.params[p,l].to_s
          res += ',' if l < 99
        end
        res += ']'
        res += ',' if p < 7
      end
      res += ']'
      res
    end

    #===========================================================================
    # SKILLS
    #===========================================================================
    def self.convert_skills
      f = File.open(@destination_folder + "Skills.json", "w")
      f.puts('[')
      f.puts('null,')
      for x in 1 ... $data_skills.size
        skill = $data_skills[x]
        skill = RPG::Skill.new if !skill
        skl_data = '{'

        skl_data += '"id":' + x.to_s + ','
        skl_data += '"animationId":' + skill.animation_id.to_s + ','
        skl_data += '"damage":' + get_damage(skill) + ','
        skl_data += '"description":' + get_text(skill.description) + ','
        skl_data += '"effects":' + get_effects(skill) + ','
        skl_data += '"hitType":' + skill.hit_type.to_s + ','
        skl_data += '"iconIndex":' + skill.icon_index.to_s + ','
        skl_data += '"message1":' + get_text(skill.message1) + ','
        skl_data += '"message2":' + get_text(skill.message2) + ','
        skl_data += '"mpCost":' + skill.mp_cost.to_s + ','
        skl_data += '"name":' + get_text(skill.name) + ','
        skl_data += '"note":' + get_text(skill.note) + ','
        skl_data += '"occasion":' + skill.occasion.to_s + ','
        skl_data += '"repeats":' + skill.repeats.to_s + ','
        skl_data += '"requiredWtypeId1":' + skill.required_wtype_id1.to_s + ','
        skl_data += '"requiredWtypeId2":' + skill.required_wtype_id2.to_s + ','
        skl_data += '"scope":' + skill.scope.to_s + ','
        skl_data += '"speed":' + skill.speed.to_s + ','
        skl_data += '"stypeId":' + skill.stype_id.to_s + ','
        skl_data += '"successRate":' + skill.success_rate.to_s + ','
        skl_data += '"tpCost":' + skill.tp_cost.to_s + ','
        skl_data += '"tpGain":' + skill.tp_gain.to_s

        skl_data += '}'
        skl_data += ',' if x < $data_skills.size - 1
        f.puts(skl_data)
      end
      f.puts(']')
      f.close
    end

    #===========================================================================
    # ITEMS
    #===========================================================================
    def self.convert_items
      f = File.open(@destination_folder + "Items.json", "w")
      f.puts('[')
      f.puts('null,')
      for x in 1 ... $data_items.size
        item = $data_items[x]
        item = RPG::Item.new if !item
        itm_data = '{'

        itm_data += '"id":' + x.to_s + ','
        itm_data += '"animationId":' + item.animation_id.to_s + ','
        itm_data += '"consumable":' + item.consumable.to_s + ','
        itm_data += '"damage":' + get_damage(item) + ','
        itm_data += '"description":' + get_text(item.description) + ','
        itm_data += '"effects":' + get_effects(item) + ','
        itm_data += '"hitType":' + item.hit_type.to_s + ','
        itm_data += '"iconIndex":' + item.icon_index.to_s + ','
        itm_data += '"itypeId":' + item.itype_id.to_s + ','
        itm_data += '"name":' + get_text(item.name) + ','
        itm_data += '"note":' + get_text(item.note) + ','
        itm_data += '"occasion":' + item.occasion.to_s + ','
        itm_data += '"price":' + item.price.to_s + ','
        itm_data += '"repeats":' + item.repeats.to_s + ','
        itm_data += '"scope":' + item.scope.to_s + ','
        itm_data += '"speed":' + item.speed.to_s + ','
        itm_data += '"successRate":' + item.success_rate.to_s + ','
        itm_data += '"tpGain":' + item.tp_gain.to_s

        itm_data += '}'
        itm_data += ',' if x < $data_items.size - 1
        f.puts(itm_data)
      end
      f.puts(']')
      f.close
    end

    #===========================================================================
    # WEAPONS
    #===========================================================================
    def self.convert_weapons
      f = File.open(@destination_folder + "Weapons.json", "w")
      f.puts('[')
      f.puts('null,')
      for x in 1 ... $data_weapons.size
        wpn = $data_weapons[x]
        wpn = RPG::Weapon.new if !wpn
        wpn_data = '{'

        wpn_data += '"id":' + x.to_s + ','
        wpn_data += '"animationId":' + wpn.animation_id.to_s + ','
        wpn_data += '"description":' + get_text(wpn.description) + ','
        wpn_data += '"etypeId":1,' # weapons are 0 in Ace, but 1 in MV
        wpn_data += '"traits":' + get_traits(wpn) + ','
        wpn_data += '"iconIndex":' + wpn.icon_index.to_s + ','
        wpn_data += '"name":' + get_text(wpn.name) + ','
        wpn_data += '"note":' + get_text(wpn.note) + ','
        wpn_data += '"params":' + wpn.params.to_s.gsub(/ /){''} + ','
        wpn_data += '"price":' + wpn.price.to_s + ','
        wpn_data += '"wtypeId":' + wpn.wtype_id.to_s

        wpn_data += '}'
        wpn_data += ',' if x < $data_weapons.size - 1
        f.puts(wpn_data)
      end
      f.puts(']')
      f.close
    end

    #===========================================================================
    # ARMORS
    #===========================================================================
    def self.convert_armors
      f = File.open(@destination_folder + "Armors.json", "w")
      f.puts('[')
      f.puts('null,')
      for x in 1 ... $data_armors.size
        amr = $data_armors[x]
        amr = RPG::Armor.new if !amr
        amr_data = '{'

        amr_data += '"id":' + x.to_s + ','
        amr_data += '"atypeId":' + amr.atype_id.to_s + ','
        amr_data += '"description":' + get_text(amr.description) + ','
        amr_data += '"etypeId":' + amr.etype_id.to_s + ','
        amr_data += '"traits":' + get_traits(amr) + ','
        amr_data += '"iconIndex":' + amr.icon_index.to_s + ','
        amr_data += '"name":' + get_text(amr.name) + ','
        amr_data += '"note":' + get_text(amr.note) + ','
        amr_data += '"params":' + amr.params.to_s.gsub(/ /){''} + ','
        amr_data += '"price":' + amr.price.to_s

        amr_data += '}'
        amr_data += ',' if x < $data_armors.size - 1
        f.puts(amr_data)
      end
      f.puts(']')
      f.close
    end

    #===========================================================================
    # ENEMIES
    #===========================================================================
    def self.convert_enemies
      f = File.open(@destination_folder + "Enemies.json", "w")
      f.puts('[')
      f.puts('null,')
      for x in 1 ... $data_enemies.size
        foe = $data_enemies[x]
        foe = RPG::Enemy.new if !foe
        foe_data = '{'

        foe_data += '"id":' + x.to_s + ','
        foe_data += '"actions":' + get_actions(foe) + ','
        foe_data += '"battlerHue":' + foe.battler_hue.to_s + ','
        foe_data += '"battlerName":"' + foe.battler_name + '",'
        foe_data += '"dropItems":' + get_drop_items(foe) + ','
        foe_data += '"exp":' + foe.exp.to_s + ','
        foe_data += '"traits":' + get_traits(foe) + ','
        foe_data += '"gold":' + foe.gold.to_s + ','
        foe_data += '"name":' + get_text(foe.name) + ','
        foe_data += '"note":' + get_text(foe.note) + ','
        foe_data += '"params":' + foe.params.to_s.gsub(/ /){''}

        foe_data += '}'
        foe_data += ',' if x < $data_enemies.size - 1
        f.puts(foe_data)
      end
      f.puts(']')
      f.close
    end

    def self.get_actions(foe)
      res = '['
      count = 1
      max_count = foe.actions.size
      foe.actions.each do |action|
        res += '{"conditionParam1":' + action.condition_param1.to_s + ','
        res += '"conditionParam2":' + action.condition_param2.to_s + ','
        res += '"conditionType":' + action.condition_type.to_s + ','
        res += '"rating":' + action.rating.to_s + ','
        res += '"skillId":' + action.skill_id.to_s + '}'
        res += ',' if count < max_count
        count += 1
      end
      res += ']'
      res
    end

    def self.get_drop_items(foe)
      res = '['
      count = 1
      max_count = foe.drop_items.size
      foe.drop_items.each do |item|
        res += '{"dataId":' + item.data_id.to_s + ','
        res += '"denominator":' + item.denominator.to_s + ','
        res += '"kind":' + item.kind.to_s + '}'
        res += ',' if count < max_count
        count += 1
      end
      res += ']'
      res
    end

    #===========================================================================
    # TROOPS
    #===========================================================================
    def self.convert_troops
      f = File.open(@destination_folder + "Troops.json", "w")
      f.puts('[')
      f.puts('null,')
      for x in 1 ... $data_troops.size
        troop = $data_troops[x]
        troop = RPG::Troop.new if !troop
        troop_data = '{'

        #***********************************************************************
        log("Troop " + x.to_s + " (" + get_text(troop.name) + ")")
        @logtroop = sprintf('Troop %d %s ', x, troop.name)
        #***********************************************************************

        troop_data += '"id":' + x.to_s + ','
        troop_data += '"members":' + get_troop_members(troop) + ','
        troop_data += '"name":' + get_text(troop.name) + ','
        troop_data += '"pages":' + get_troop_pages(troop)

        troop_data += '}'
        troop_data += ',' if x < $data_troops.size - 1
        f.puts(troop_data)
      end
      f.puts(']')
      f.close
    end

    def self.get_troop_members(troop)
      res = '['
      count = 1
      max_count = troop.members.size
      troop.members.each do |enemy|
        res += '{"enemyId":' + enemy.enemy_id.to_s + ','
        res += '"x":' + enemy.x.to_s + ','
        res += '"y":' + enemy.y.to_s + ','
        res += '"hidden":' + enemy.hidden.to_s + '}'
        res += ',' if count < max_count
        count += 1
      end
      res += ']'
      res
    end

    def self.get_troop_pages(troop)
      res = '['
      count = 1
      max_count = troop.pages.size
      troop.pages.each do |page|
        #***********************************************************************
        log("  Page " + count.to_s)
        @logkey = sprintf('%s Page %d', @logtroop, count)
        #***********************************************************************
        cond = page.condition
        res += '{"conditions":{"actorHp":' + cond.actor_hp.to_s + ','
        res += '"actorId":' + cond.actor_id.to_s + ','
        res += '"actorValid":' + cond.actor_valid.to_s + ','
        res += '"enemyHp":' + cond.enemy_hp.to_s + ','
        res += '"enemyIndex":' + cond.enemy_index.to_s + ','
        res += '"enemyValid":' + cond.enemy_valid.to_s + ','
        res += '"switchId":' + cond.switch_id.to_s + ','
        res += '"switchValid":' + cond.switch_valid.to_s + ','
        res += '"turnA":' + cond.turn_a.to_s + ','
        res += '"turnB":' + cond.turn_b.to_s + ','
        res += '"turnEnding":' + cond.turn_ending.to_s + ','
        res += '"turnValid":' + cond.turn_valid.to_s + '},'

        res += '"list":' + get_command_list(page.list) + ','
        res += '"span":' + page.span.to_s + '}'

        res += ',' if count < max_count
        count += 1
      end
      res += ']'
      res
    end

    #===========================================================================
    # STATES
    #===========================================================================
    def self.convert_states
      f = File.open(@destination_folder + "States.json", "w")
      f.puts('[')
      f.puts('null,')
      for x in 1 ... $data_states.size
        state = $data_states[x]
        state = RPG::State.new if !state
        state_data = '{'

        state_data += '"id":' + x.to_s + ','
        state_data += '"autoRemovalTiming":' + state.auto_removal_timing.to_s + ','
        state_data += '"chanceByDamage":' + state.chance_by_damage.to_s + ','
        state_data += '"iconIndex":' + state.icon_index.to_s + ','
        state_data += '"maxTurns":' + state.max_turns.to_s + ','
        state_data += '"message1":' + get_text(state.message1) + ','
        state_data += '"message2":' + get_text(state.message2) + ','
        state_data += '"message3":' + get_text(state.message3) + ','
        state_data += '"message4":' + get_text(state.message4) + ','
        state_data += '"minTurns":' + state.min_turns.to_s + ','
        state_data += '"motion":0,'
        state_data += '"overlay":0,'
        state_data += '"name":' + get_text(state.name) + ','
        state_data += '"note":' + get_text(state.note) + ','
        state_data += '"priority":' + state.priority.to_s + ','
        state_data += '"removeAtBattleEnd":' + state.remove_at_battle_end.to_s + ','
        state_data += '"removeByDamage":' + state.remove_by_damage.to_s + ','
        state_data += '"removeByRestriction":' + state.remove_by_restriction.to_s + ','
        state_data += '"removeByWalking":' + state.remove_by_walking.to_s + ','
        state_data += '"restriction":' + state.restriction.to_s + ','
        state_data += '"stepsToRemove":' + state.steps_to_remove.to_s + ','
        state_data += '"traits":' + get_traits(state)

        state_data += '}'
        state_data += ',' if x < $data_states.size - 1
        f.puts(state_data)
      end
      f.puts(']')
      f.close
    end

    #===========================================================================
    # ANIMATIONS
    #===========================================================================
    def self.convert_animations
      f = File.open(@destination_folder + "Animations.json", "w")
      f.puts('[')
      f.puts('null,')
      for x in 1 ... $data_animations.size
        anim = $data_animations[x]
        anim = RPG::Animation.new if !anim
        anim_data = '{'

        anim_data += '"id":' + x.to_s + ','
        anim_data += '"animation1Hue":' + anim.animation1_hue.to_s + ','
        anim_data += '"animation1Name":"' + anim.animation1_name + '",'
        anim_data += '"animation2Hue":' + anim.animation2_hue.to_s + ','
        anim_data += '"animation2Name":"' + anim.animation2_name + '",'
        anim_data += '"frames":' + get_anim_frames(anim) + ','
        anim_data += '"name":' + get_text(anim.name) + ','
        anim_data += '"position":' + anim.position.to_s + ','
        anim_data += '"timings":' + get_anim_timings(anim)

        anim_data += '}'
        anim_data += ',' if x < $data_animations.size - 1
        f.puts(anim_data)
      end
      f.puts(']')
      f.close
    end

    def self.get_anim_frames(anim)
      res = '['
      for f in 0 ... anim.frame_max
        res += '['
        frame = anim.frames[f]
        if frame
          for c in 0 ... frame.cell_max
            res += '['
            for i in 0..7
              res += frame.cell_data[c,i].to_s
              res += ',' if i < 7
            end
            res += ']'
            res += ',' if c < frame.cell_max - 1
          end
        else
          res += '[]'
        end
        res += ']'
        res += ',' if f < anim.frame_max - 1
      end
      res += ']'
      res
    end

    def self.get_anim_timings(anim)
      res = '['
      for t in 0 ... anim.timings.size
        timing = anim.timings[t]
        res += '{"flashColor":' + get_color(timing.flash_color) + ','
        res += '"flashDuration":' + timing.flash_duration.to_s + ','
        res += '"flashScope":' + timing.flash_scope.to_s + ','
        res += '"frame":' + timing.frame.to_s + ','
        res += '"se":'
        if timing.se.name == ''
          res += 'null'
        else
          res += get_audio(timing.se)
        end
        res += '}'
        res += ',' if t < anim.timings.size - 1
      end
      res += ']'
      res
    end

    #===========================================================================
    # TILESETS
    #===========================================================================
    def self.convert_tilesets
      f = File.open(@destination_folder + "Tilesets.json", "w")
      f.puts('[')
      f.puts('null,')
      for x in 1 ... $data_tilesets.size
        tileset = $data_tilesets[x]
        tileset = RPG::Tileset.new if !tileset
        ts_data = '{'

        ts_data += '"id":' + x.to_s + ','
        ts_data += '"flags":'
        flags = []
        for t in 0 .. 8191
          flags[t] = tileset.flags[t]
        end
        ts_data += flags.to_s.gsub(/ /){''} + ','
        ts_data += '"mode":' + tileset.mode.to_s + ','
        ts_data += '"name":' + get_text(tileset.name) + ','
        ts_data += '"note":' + get_text(tileset.note) + ','
        ts_data += '"tilesetNames":' + tileset.tileset_names.to_s.gsub(/, /){','}

        ts_data += '}'
        ts_data += ',' if x < $data_tilesets.size - 1
        f.puts(ts_data)
      end
      f.puts(']')
      f.close
    end

    #===========================================================================
    # COMMON EVENTS
    #===========================================================================
    def self.convert_common_events
      f = File.open(@destination_folder + "CommonEvents.json", "w")
      f.puts('[')
      f.puts('null,')
      for x in 1 ... $data_common_events.size
        event = $data_common_events[x]
        event = RPG::CommonEvent.new if !event

        #***********************************************************************
        log("Common Event " + x.to_s + " (" + get_text(event.name) + ")")
        @logkey = sprintf('Common Event %d %s', x, event.name)
        #***********************************************************************

        ev_data = '{'

        ev_data += '"id":' + x.to_s + ','
        ev_data += '"list":' + get_command_list(event.list) + ','
        ev_data += '"name":' + get_text(event.name) + ','
        ev_data += '"switchId":' + event.switch_id.to_s + ','
        ev_data += '"trigger":' + event.trigger.to_s

        ev_data += '}'
        ev_data += ',' if x < $data_common_events.size - 1
        f.puts(ev_data)
      end
      f.puts(']')
      f.close
    end

    #===========================================================================
    # SYSTEM
    #===========================================================================
    def self.convert_system
      f = File.open(@destination_folder + "System.json", "w")
      system = $data_system
      sys_data = '{'

      sys_data += '"airship":' + get_vehicle(system.airship) + ','
      sys_data += '"armorTypes":' + system.armor_types.to_s.gsub(/, /){','} + ','
      sys_data += '"attackMotions":' + get_attack_motions + ','
      sys_data += '"battleBgm":' + get_audio(system.battle_bgm) + ','
      sys_data += '"battleBack1Name":"' + system.battleback1_name + '",'
      sys_data += '"battleBack2Name":"' + system.battleback2_name + '",'
      sys_data += '"battlerHue":' + system.battler_hue.to_s + ','
      sys_data += '"battlerName":"' + system.battler_name + '",'
      sys_data += '"boat":' + get_vehicle(system.boat) + ','
      sys_data += '"currencyUnit":"' + system.currency_unit + '",'
      sys_data += '"defeatMe":{"name":"Defeat1","pan":0,"pitch":100,"volume":90},'
      sys_data += '"editMapId":' + system.edit_map_id.to_s + ','
      sys_data += '"elements":' + system.elements.to_s.gsub(/, /){','} + ','
      sys_data += '"equipTypes":' + system.terms.etypes.unshift('').to_s.gsub(/, /){','} + ','
      sys_data += '"gameTitle":' + get_text(system.game_title) + ','
      sys_data += '"gameoverMe":' + get_audio(system.gameover_me) + ','
      sys_data += '"locale":"en_US",'
      sys_data += '"magicSkills":[1],'
      sys_data += '"menuCommands":[true,true,true,true,true,true],'
      sys_data += '"optDisplayTp":' + system.opt_display_tp.to_s + ','
      sys_data += '"optDrawTitle":' + system.opt_draw_title.to_s + ','
      sys_data += '"optExtraExp":' + system.opt_extra_exp.to_s + ','
      sys_data += '"optFloorDeath":' + system.opt_floor_death.to_s + ','
      sys_data += '"optFollowers":' + system.opt_followers.to_s + ','
      sys_data += '"optSideView":false,'
      sys_data += '"optSlipDeath":' + system.opt_slip_death.to_s + ','
      sys_data += '"optTransparent":' + system.opt_transparent.to_s + ','
      sys_data += '"partyMembers":' + system.party_members.to_s.gsub(/ /){''} + ','
      sys_data += '"ship":' + get_vehicle(system.ship) + ','
      sys_data += '"skillTypes":' + system.skill_types.to_s.gsub(/, /){','} + ','
      sys_data += '"sounds":' + get_system_sounds(system) + ','
      sys_data += '"startMapId":' + system.start_map_id.to_s + ','
      sys_data += '"startX":' + system.start_x.to_s + ','
      sys_data += '"startY":' + system.start_y.to_s + ','
      system.switches[0] = ''
      sys_data += '"switches":' + system.switches.to_s.gsub(/, /){','} + ','
      sys_data += '"terms":{"basic":' + (system.terms.basic + ['EXP','EXP']).to_s.gsub(/, /){','} + ','
      sys_data += '"commands":' + (system.terms.commands + ['','Buy','Sell']).to_s.gsub(/, /){','} + ','
      sys_data += '"params":' + (system.terms.params + ['Hit','Evasion']).to_s.gsub(/, /){','} + ','
      sys_data += '"messages":' + get_system_messages + '},'
      sys_data += '"testBattlers":' + get_test_battlers(system.test_battlers) + ','
      sys_data += '"testTroopId":' + system.test_troop_id.to_s + ','
      sys_data += '"title1Name":"' + system.title1_name + '",'
      sys_data += '"title2Name":"' + system.title2_name + '",'
      sys_data += '"titleBgm":' + get_audio(system.title_bgm) + ','
      system.variables[0] = ''
      sys_data += '"variables":' + system.variables.to_s.gsub(/, /){','} + ','
      sys_data += '"versionId":' + system.version_id.to_s + ','
      sys_data += '"victoryMe":' + get_audio(system.battle_end_me) + ','
      sys_data += '"weaponTypes":' + system.weapon_types.to_s.gsub(/, /){','} + ','
      sys_data += '"windowTone":' + get_tone(system.window_tone)

      sys_data += '}'
      f.puts(sys_data)
      f.close
    end

    def self.get_attack_motions
      res = '['
      res += '{"type":0,"weaponImageId":0},'
      res += '{"type":1,"weaponImageId":1},'
      res += '{"type":1,"weaponImageId":2},'
      res += '{"type":1,"weaponImageId":3},'
      res += '{"type":1,"weaponImageId":4},'
      res += '{"type":1,"weaponImageId":5},'
      res += '{"type":1,"weaponImageId":6},'
      res += '{"type":2,"weaponImageId":7},'
      res += '{"type":2,"weaponImageId":8},'
      res += '{"type":2,"weaponImageId":9},'
      res += '{"type":0,"weaponImageId":10},'
      res += '{"type":0,"weaponImageId":11},'
      res += '{"type":0,"weaponImageId":12}'
      res += ']'
      res
    end

    def self.get_vehicle(vehicle)
      res = '{"bgm":' + get_audio(vehicle.bgm) + ','
      res += '"characterIndex":' + vehicle.character_index.to_s + ','
      res += '"characterName":"' + vehicle.character_name + '",'
      res += '"startMapId":' + vehicle.start_map_id.to_s + ','
      res += '"startX":' + vehicle.start_x.to_s + ','
      res += '"startY":' + vehicle.start_y.to_s + '}'
      res
    end

    def self.get_system_sounds(system)
      res = '['
      for x in 0 ... system.sounds.size
        res += get_audio(system.sounds[x])
        res += ',' if x < system.sounds.size - 1
      end

      res += ']'
      res
    end

    def self.get_system_messages
      res = '{'
      res += '"actionFailure":"There was no effect on %1!",'
      res += '"actorDamage":"%1 took %2 damage!",'
      res += '"actorDrain":"%1 was drained of %2 %3!",'
      res += '"actorGain":"%1 gained %2 %3!",'
      res += '"actorLoss":"%1 lost %2 %3!",'
      res += '"actorNoDamage":"%1 took no damage!",'
      res += '"actorNoHit":"Miss! %1 took no damage!",'
      res += '"actorRecovery":"%1 recovered %2 %3!",'
      res += '"alwaysDash":"Always Dash",'
      res += '"bgmVolume":"BGM Volume",'
      res += '"bgsVolume":"BGS Volume",'
      res += '"buffAdd":"%1\'s %2 went up!",'
      res += '"buffRemove":"%1''s %2 returned to normal!",'
      res += '"commandRemember":"Command Remember",'
      res += '"counterAttack":"%1 counterattacked!",'
      res += '"criticalToActor":"A painful blow!!",'
      res += '"criticalToEnemy":"An excellent hit!!",'
      res += '"debuffAdd":"%1\'s %2 went down!",'
      res += '"defeat":"%1 was defeated.",'
      res += '"emerge":"%1 emerged!",'
      res += '"enemyDamage":"%1 took %2 damage!",'
      res += '"enemyDrain":"%1 was drained of %2 %3!",'
      res += '"enemyGain":"%1 gained %2 %3!",'
      res += '"enemyLoss":"%1 lost %2 %3!",'
      res += '"enemyNoDamage":"%1 took no damage!",'
      res += '"enemyNoHit":"Miss! %1 took no damage!",'
      res += '"enemyRecovery":"%1 recovered %2 %3!",'
      res += '"escapeFailure":"However, it was unable to escape!",'
      res += '"escapeStart":"%1 has started to escape!",'
      res += '"evasion":"%1 evaded the attack!",'
      res += '"expNext":"To Next %1",'
      res += '"expTotal":"Current %1",'
      res += '"file":"File",'
      res += '"levelUp":"%1 is now %2 %3!",'
      res += '"loadMessage":"Load which file?",'
      res += '"magicEvasion":"%1 nullified the magic!",'
      res += '"magicReflection":"%1 reflected the magic!",'
      res += '"meVolume":"ME Volume",'
      res += '"obtainExp":"%1 %2 received!",'
      res += '"obtainGold":"%1\\\\G found!",'
      res += '"obtainItem":"%1 found!",'
      res += '"obtainSkill":"%1 learned!",'
      res += '"partyName":"%1\'s Party",'
      res += '"possession":"Possession",'
      res += '"preemptive":"%1 got the upper hand!",'
      res += '"saveMessage":"Save to which file?",'
      res += '"seVolume":"SE Volume",'
      res += '"substitute":"%1 protected %2!",'
      res += '"surprise":"%1 was surprised!",'
      res += '"useItem":"%1 uses %2!",'
      res += '"victory":"%1 was victorious!"'
      res += '}'
      res
    end

    def self.get_test_battlers(battlers)
      res = '['
      for x in 0 ... battlers.size
        battler = battlers[x]
        res += '{'
        res += '"actorId":' + battler.actor_id.to_s + ','
        res += '"equips":' + battler.equips.to_s.gsub(/ /){''} + ','
        res += '"level":' + battler.level.to_s
        res += '}'
        res += ',' if x < battlers.size - 1
      end
      res += ']'
      res
    end

    #===========================================================================
    # MAPINFOS
    #===========================================================================
    def self.convert_mapinfos
      f = File.open(@destination_folder + "MapInfos.json", "w")
      f.puts('[')
      f.puts('null,')
      for x in 1 .. $data_mapinfos.size
        map = $data_mapinfos[x]
        map = RPG::MapInfo.new if !map
        map_data = '{'
        map_data += '"id":' + x.to_s + ','
        map_data += '"expanded":' + map.expanded.to_s + ','
        map_data += '"name":' + get_text(map.name) + ','
        map_data += '"order":' + map.order.to_s + ','
        map_data += '"parentId":' + map.parent_id.to_s + ','
        map_data += '"scrollX":' + map.scroll_x.to_s + ','
        map_data += '"scrollY":' + map.scroll_y.to_s

        map_data += '}'
        map_data += ',' if x < $data_mapinfos.size
        f.puts(map_data)
      end
      f.puts(']')
      f.close
    end

    #===========================================================================
    # MAPS
    #===========================================================================
    def self.convert_maps(map_files)
      map_files.each do |filename|
        convert_map(filename)
      end
    end

    def self.convert_map(filename)
      map = load_data(filename)
      f = File.open(@destination_folder + File.basename(filename).gsub(/yaml/){'json'}, "w")
      f.puts('{')
      mapid = 0

      #*************************************************************************
      log("Map " + filename + " (" + map.display_name + ")")
      filename.gsub!(/Map(\d+)\./) do
        mapid = $1.to_i
        @logmap = sprintf('Map %d %s', $1.to_i, $data_mapinfos[$1.to_i].name)
      end
      #*************************************************************************

      map_data = '"autoplayBgm":' + map.autoplay_bgm.to_s + ','
      map_data += '"autoplayBgs":' + map.autoplay_bgs.to_s + ','
      map_data += '"battleback1Name":"' + map.battleback1_name + '",'
      map_data += '"battleback2Name":"' + map.battleback2_name + '",'
      map_data += '"bgm":' + get_audio(map.bgm) + ','
      map_data += '"bgs":' + get_audio(map.bgs) + ','
      map_data += '"disableDashing":' + map.disable_dashing.to_s + ','
      map_data += '"displayName":' + get_text(map.display_name) + ','
      map_data += '"encounterList":' + get_encounter_list(map.encounter_list) + ','
      map_data += '"encounterStep":' + map.encounter_step.to_s + ','
      map_data += '"height":' + map.height.to_s + ','
      map_data += '"note":' + get_text(map.note) + ','
      map_data += '"parallaxLoopX":' + map.parallax_loop_x.to_s + ','
      map_data += '"parallaxLoopY":' + map.parallax_loop_y.to_s + ','
      map_data += '"parallaxName":"' + map.parallax_name + '",'
      map_data += '"parallaxShow":' + map.parallax_show.to_s + ','
      map_data += '"parallaxSx":' + map.parallax_sx.to_s + ','
      map_data += '"parallaxSy":' + map.parallax_sy.to_s + ','
      map_data += '"scrollType":' + map.scroll_type.to_s + ','
      map_data += '"specifyBattleback":' + map.specify_battleback.to_s + ','
      map_data += '"tilesetId":' + map.tileset_id.to_s + ','
      map_data += '"width":' + map.width.to_s + ','
      map_data += '"data":' + get_map_data(map.data, map.events).to_s.gsub(/ /){''} + ','
      map_data += '"events":' + get_map_events(map.events)

      p sprintf('Map %d (%s) is %d x %d', mapid, $data_mapinfos[mapid].name, map.width, map.height) if map.width < 25 or map.height < 19

      f.puts(map_data)

      f.puts('}')
      f.close
    end

    def self.get_encounter_list(list)
      res = '['
      for x in 0 ... list.size
        encounter = list[x]
        encounter = RPG::Map::Encounter.new if !encounter
        res += '{"regionSet":' + encounter.region_set.to_s.gsub(/ /){''} + ','
        res += '"troopId":' + encounter.troop_id.to_s + ','
        res += '"weight":' + encounter.weight.to_s
        res += '}'
        res += ',' if x < list.size - 1
      end
      res += ']'
      res
    end

    def self.get_map_data(data, events)
      res = []
      for z in 0 .. 1 # first 2 map layers
        for y in 0 ... data.ysize
          for x in 0 ... data.xsize
            res.push(data[x,y,z])
          end
        end
      end
      z = 2
      upper1 = []
      upper2 = []
      for y in 0 ... data.ysize # 3rd & new 4th map layer
        for x in 0 ... data.xsize
          tile_event = events.select{|id, evt| evt && evt.x == x && evt.y == y && is_tile_event?(evt) }
          if tile_event.size > 0
            key = tile_event.keys[0]
            upper1.push(data[x,y,z])
            upper2.push(events[key].pages[0].graphic.tile_id)
          else
            upper1.push(0)
            upper2.push(data[x,y,z])
          end
        end
      end
      res += upper1 + upper2
      z = data.zsize - 1 # shadow layer
      for y in 0 ... data.ysize
        for x in 0 ... data.xsize
          res.push(data[x,y,z])
        end
      end
      for y in 0 ... data.ysize # region layer
        for x in 0 ... data.xsize
          res.push(data[x,y,3] >> 8)
        end
      end
      res
    end

    def self.is_tile_event?(evt)
      return false if evt.pages.size > 1
      return false if evt.pages[0].list.size > 1
      return false if evt.pages[0].graphic.tile_id == 0
      c = evt.pages[0].condition
      return !(c.switch1_valid || c.switch2_valid || c.variable_valid ||
        c.self_switch_valid || c.item_valid || c.actor_valid)
    end

    def self.get_map_events(events)
      res = '['
      max_key = events.keys.max
      if max_key
        for x in 0 .. max_key
          if events.has_key?(x)
            event = events[x]
            if is_tile_event?(event)
              res += 'null'
            else
              res += get_event(event)
            end
          else
            res += 'null'
          end
          res += ',' if x < max_key
        end
      end
      res += ']'
      res
    end

    def self.get_event(event)
      #*************************************************************************
      log("  Event " + event.id.to_s + " (" + get_text(event.name) + " @ " + event.x.to_s + "," + event.y.to_s + ")")
      @logevent = sprintf('%s - Event %d %s (%d,%d)', @logmap, event.id, event.name, event.x, event.y)
      #*************************************************************************
      res = '{"id":' + event.id.to_s + ','
      res += '"name":' + get_text(event.name) + ','
      res += '"note":"",'
      res += '"pages":' + get_event_pages(event.pages) + ','
      res += '"x":' + event.x.to_s + ','
      res += '"y":' + event.y.to_s
      res += '}'
      res
    end

    def self.get_event_pages(pages)
      res = '['
      for x in 0 ... pages.size
        #***********************************************************************
        log("    Page " + (x+1).to_s)
        @logkey = sprintf('%s - Page %d', @logevent, x+1)
        #***********************************************************************
        page = pages[x]
        page = RPG::Event::Page.new if !page
        res += get_page(page)
        res += ',' if x < pages.size - 1
      end
      res += ']'
      res
    end

    def self.get_page(page)
      condition = page.condition
      res = '{"conditions":'
      res += '{"actorId":' + condition.actor_id.to_s + ','
      res += '"actorValid":' + condition.actor_valid.to_s + ','
      res += '"itemId":' + condition.item_id.to_s + ','
      res += '"itemValid":' + condition.item_valid.to_s + ','
      res += '"selfSwitchCh":"' + condition.self_switch_ch + '",'
      res += '"selfSwitchValid":' + condition.self_switch_valid.to_s + ','
      res += '"switch1Id":' + condition.switch1_id.to_s + ','
      res += '"switch1Valid":' + condition.switch1_valid.to_s + ','
      res += '"switch2Id":' + condition.switch2_id.to_s + ','
      res += '"switch2Valid":' + condition.switch2_valid.to_s + ','
      res += '"variableId":' + condition.variable_id.to_s + ','
      res += '"variableValid":' + condition.variable_valid.to_s + ','
      res += '"variableValue":' + condition.variable_value.to_s + '},'

      res += '"directionFix":' + page.direction_fix.to_s + ','

      graphic = page.graphic
      res += '"image":'
      res += '{"tileId":' + graphic.tile_id.to_s + ','
      res += '"characterName":"' + graphic.character_name + '",'
      res += '"direction":' + graphic.direction.to_s + ','
      res += '"pattern":' + graphic.pattern.to_s + ','
      res += '"characterIndex":' + graphic.character_index.to_s + '},'

      res += '"moveFrequency":' + page.move_frequency.to_s + ','
      res += '"moveRoute":' + get_move_route(page.move_route) + ','
      res += '"moveSpeed":' + page.move_speed.to_s + ','
      res += '"moveType":' + page.move_type.to_s + ','
      res += '"priorityType":' + page.priority_type.to_s + ','
      res += '"stepAnime":' + page.step_anime.to_s + ','
      res += '"through":' + page.through.to_s + ','
      res += '"trigger":' + page.trigger.to_s + ','
      res += '"walkAnime":' + page.walk_anime.to_s + ','
      res += '"list":' + get_command_list(page.list) + '}'

      res
    end

    #===========================================================================
    # SUPPORT OBJECTS FOR DATABASE
    #===========================================================================

    def self.get_traits(obj)
      res = '['
      count = 1
      max_count = obj.features.size
      obj.features.each do |feat|
        res += '{"code":' + feat.code.to_s + ','
        res += '"dataId":' + feat.data_id.to_s + ','
        res += '"value":' + feat.value.to_s + '}'
        res += ',' if count < max_count
        count += 1
      end
      res += ']'
      res
    end

    def self.get_effects(obj)
      res = '['
      count = 1
      max_count = obj.effects.size
      obj.effects.each do |effct|
        res += '{"code":' + effct.code.to_s + ','
        res += '"dataId":' + effct.data_id.to_s + ','
        res += '"value1":' + effct.value1.to_s + ','
        res += '"value2":' + effct.value2.to_s + '}'
        res += ',' if count < max_count
        count += 1
      end
      res += ']'
      res
    end

    def self.get_damage(obj)
      dmg = obj.damage

      if LOGSCRIPTS && obj.damage.formula.to_i.to_s != obj.damage.formula
        sl_data = sprintf('%s %d %s: Damage Formula: %s',
          (obj.is_a?(RPG::Skill) ? 'Skill' : 'Item'), obj.id, obj.name, dmg.formula)
        @scriptlog.puts(sl_data)
      end

      res = '{"critical":' + dmg.critical.to_s + ','
      res += '"elementId":' + dmg.element_id.to_s + ','
      res += '"formula":"' + dmg.formula + '",'
      res += '"type":' + dmg.type.to_s + ','
      res += '"variance":' + dmg.variance.to_s + '}'
      res
    end


    #===========================================================================
    #
    # EVENT COMMANDS
    #
    #===========================================================================

    #===========================================================================
    # COMMAND LISTS
    #===========================================================================

    def self.get_command_list(list)
      res = '['
      count = 1
      max_count = list.size
      list.each do |cmd|
        @loginfo = sprintf('%s Line %d: ', @logkey, count)

        case cmd.code
        when 102 # show choices
          cmd.parameters[1] -= 1 # disallow cancel
          cmd.parameters[1] = -2 if cmd.parameters[1] == 4 # branch on cancel
          cmd.parameters[2] = 0 # default
          cmd.parameters[3] = 2 # window position
          cmd.parameters[4] = 0 # window background
        when 104
          cmd.parameters[1] = 2 # key item
        when 108, 408 # comment
          log_comment(cmd.parameters[0])
        when 111
          if cmd.parameters[0] == 11 # Key Pressed
            # ASD buttons are not catered for in MV.  To use these, you will
            # have to add 41 (A), 43 (S) and 44 (D) to the Input.keyMapper hash
            # in rpg_core.js:
            # Input.keyMapper[41] = 'A'
            # Input.keyMapper[53] = 'S'
            # Input.keyMapper[44] = 'D'
            case cmd.parameters[1]
            when 14
              cmd.parameters = [12, "Input.isTriggered('A')"]
            when 15
              cmd.parameters = [12, "Input.isTriggered('S')"]
            when 16
              cmd.parameters = [12, "Input.isTriggered('D')"]
            else
              cmd.parameters[1] = ['', '', 'down', '', 'left', '', 'right', '', 'up',
                '', '', 'shift', 'cancel', 'ok', '', '', '', 'pageup', 'pagedown'][
                cmd.parameters[1]]
            end
          elsif cmd.parameters[0] == 12 # Script
            log_script('Conditional Branch script call', cmd.parameters[1])
          end
        when 122 # Control Variables
          if cmd.parameters[3] == 4 # Script
            log_script('Control Variables script call', cmd.parameters[4])
          end
        when 231 # show picture
          if cmd.parameters[9] == 2 # subtract
            params = cmd.parameters
            cmd.code = 355
            cmd.parameters = [sprintf('$gameScreen.showPicture(%d, "%s", %d, %s, %s, %d, %d, %d, %d)',
              params[0], params[1], params[2], (params[3] == 0 ? params[4].to_s : '$gameVariables.value(' + params[4].to_s + ')'),
              (params[3] == 0 ? params[5].to_s : '$gameVariables.value(' + params[5].to_s + ')'),
              params[6], params[7], params[8], params[9])]
          end
        when 232 # move picture
          cmd.parameters[1] = 0 # not used, but can't be blank in MV
          if cmd.parameters[9] == 2 # subtract
            params = cmd.parameters
            cmd.code = 355
            cmd.parameters = [sprintf('$gameScreen.movePicture(%d, %d, %s, %s, %d, %d, %d, %d, %d)%s',
              params[0], params[2], (params[3] == 0 ? params[4].to_s : '$gameVariables.value(' + params[4].to_s + ')'),
              (params[3] == 0 ? params[5].to_s : '$gameVariables.value(' + params[5].to_s + ')'),
              params[6], params[7], params[8], params[9], params[10], params[11] ? '; this.wait(' + params[10].to_s + ')' : '')]
          end
        when 285 # get location info
          cmd.parameters[1] = 6 if cmd.parameters[1] == 5 # region id now +1
        when 319 # change equipment
          cmd.parameters[1] += 1
        when 322 # change actor graphic
          cmd.parameters[4] = 0 # SV graphic
          cmd.parameters[5] = ''
        when 355, 655 # Script call
          log_script('Script call', cmd.parameters[0])
        when 505 # Move route
          mvrcmd = cmd.parameters[0]
          if mvrcmd.code == 45 # script
            log_script('Move Route Script call', mvrcmd.parameters[0])
          end
        end

        evt_cmd = '{"code":' + cmd.code.to_s + ','
        evt_cmd += '"indent":' + cmd.indent.to_s + ','
        evt_cmd += '"parameters":' + convert_parameters(cmd.parameters) + '}'

        #***********************************************************************
        log("      " + evt_cmd)
        #***********************************************************************

        res += evt_cmd
        res += ',' if count < max_count
        count += 1
      end
      res += ']'
      res
    end

    def self.get_move_route(mr)
      res = '{"list":['
      list = mr.list
      for x in 0 ... list.size
        cmd = list[x]

        case cmd.code
        when 43
          if cmd.parameters[0] == 2 then
            cmd.code = 45
            cmd.parameters = ["this.setBlendMode(2);"]
          end
        end

        mvr = '{"code":' + cmd.code.to_s + ','
        mvr += '"indent":null,'
        mvr += '"parameters":' + convert_parameters(cmd.parameters) + '}'

        #***********************************************************************
        log("        " + mvr)
        #***********************************************************************

        res += mvr
        res += ',' if x < list.size - 1
      end
      res += '],"repeat":' + mr.repeat.to_s + ','
      res += '"skippable":' + mr.skippable.to_s + ','
      res += '"wait":' + mr.wait.to_s + '}'
      res
    end

    def self.convert_parameters(params)
      res = '['
      for x in 0 ... params.size
        param = params[x]
        case param
        when RPG::MoveRoute
          param = get_move_route(param)
        when RPG::MoveCommand
          param = get_move_command(param)
        when RPG::AudioFile
          param = get_audio(param)
        when String
          param = get_text(param)
        when Symbol
          param = get_text(param.to_s)
        when Tone
          param = get_tone(param)
        when Color
          param = get_color(param)
        end

        if param.to_s.match(/^\s*#/)
          print param
          debugger
        end
        res += param.to_s
        res += ',' if x < params.size - 1
      end
      res += ']'
      res
    end


    #===========================================================================
    # COMMANDS
    #===========================================================================

    def self.get_move_command(param)
      res = '{"code":' + param.code.to_s + ','
      res += '"indent":null,'
      res += '"parameters":' + convert_parameters(param.parameters).to_s + '}'
      res
    end

    #===========================================================================
    # COMMON OBJECTS
    #===========================================================================

    def self.get_text(text)
      if text
        '"' + text.gsub(/\\/){'\\\\'}.gsub(/[\r\n]+/){'\\n'}.gsub(/"/){'\\"'} + '"'
      else
        '""'
      end
    end

    def self.get_audio(a)
      a = RPG::AudioFile.new if !a
      res = '{"name":"' + a.name + '",'
      res += '"pan":0,'
      res += '"pitch":' + a.pitch.to_s + ','
      res += '"volume":' + a.volume.to_s + '}'
      res
    end

    def self.get_color(color)
      res = '['
      res += color.red.to_s + ','
      res += color.green.to_s + ','
      res += color.blue.to_s + ','
      res += color.alpha.to_s
      res += ']'
      res
    end

    def self.get_tone(tone)
      res = '['
      res += tone.red.to_s + ','
      res += tone.green.to_s + ','
      res += tone.blue.to_s + ','
      res += tone.gray.to_s
      res += ']'
      res
    end

    def self.log(details)
      @log.puts(details) if LOGGING
    end

    def self.log_script(title, cmd)
      @scriptlog.puts(sprintf('%s - %s: %s', @loginfo, title, cmd))
    end

    def self.log_comment(comment)
      @commentlog.puts(sprintf('%s - Comment: %s', @loginfo, comment))
    end
  end
end

#=end
