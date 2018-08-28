#!/usr/bin/env ruby

require 'json'
require 'fileutils'
require_relative 'rpgmaker_fakes'

if ARGV.length < 2
  puts "Usage: #{$0} path/to/an/rpgmaker/xp/vx/or/vxace/game last_quest_id"
  exit 0
end

game_dir = File.expand_path(ARGV[0])
last_quest_id = ARGV[1].to_i

load "#{game_dir}/Scripts/Quest_Log.rb"

$game_party = Game_Party.new
$game_system = Game_System.new

quest_data = (1..last_quest_id).map do |n|
  data = QuestData.setup_quest(n)
  data[:id] = n
  if data[:layout] == false
    data.delete(:layout)
  end
  data
end.reject do |quest|
  quest[:name] == nil
end
puts JSON.pretty_generate(quest_data)
