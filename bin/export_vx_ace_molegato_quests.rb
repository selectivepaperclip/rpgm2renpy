#!/usr/bin/env ruby

require 'json'
require 'fileutils'
require_relative 'rpgmaker_fakes'

if ARGV.length < 1
  puts "Usage: #{$0} path/to/an/rpgmaker/xp/vx/or/vxace/game"
  exit 0
end

game_dir = File.expand_path(ARGV[0])

load "#{game_dir}/Scripts/QuestLog.rb"

quest_data = MOLEGATO_QUESTS::QUEST_DATA.map do |quest|
  {
    name: quest[0],
    var: quest[1],
    icon: quest[2],
    image: quest[3],
    description: quest[4],
    long_text: quest[5]
  }
end
puts JSON.pretty_generate(quest_data)
