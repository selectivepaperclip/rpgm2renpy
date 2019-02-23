#!/usr/bin/env ruby

require 'json'
require 'fileutils'
require 'awesome_print'

if ARGV.length < 1
  puts "Usage: #{$0} path/to/an/rpgmaker/xp/vx/or/vxace/game"
  exit 0
end

game_dir = File.expand_path(ARGV[0])

def data_dir(game_dir)
    ace_path = File.join(game_dir, 'JsonData')
    mv_path = File.join(game_dir, 'www', 'data')
    if File.exist?(ace_path)
        ace_path
    elsif File.exist?(mv_path)
        mv_path
    end
end

script_strings = []
plugin_strings = []

maps = Dir[File.join(data_dir(game_dir), 'Map[0-9]*')]
maps.each do |map_path|
    json = begin
        JSON.parse(File.read(map_path))
    rescue
        puts "Could not parse: #{map_path}"
        next
    end
    json['events'].compact.each do |event_json|
        event_json['pages'].each do |page_json|
            commands = page_json['list']
            commands.each do |command|
                if command['code'] == 111 and command['parameters'][0] == 12
                    script_strings.push(command['parameters'][1])
                elsif command['code'] == 355
                    script_strings.push(command['parameters'][0])
                elsif command['code'] == 655
                    script_strings[-1] = "#{script_strings[-1]}\n#{command['parameters'][0]}"
                elsif command['code'] == 205
                    event_id, route = command['parameters']
                    route['list'].each do |route_part|
                        if route_part['code'] == 45
                            script_strings.push("[ROUTE]: #{route_part['parameters'][0]}")
                        end
                    end
                elsif command['code'] == 356
                    split_params = command['parameters'][0].split(' ')
                    plugin_strings << split_params[0]
                end
            end
        end
    end
end

if script_strings.length > 0
    puts
    puts "Script Strings:"
    puts script_strings.map(&:strip).uniq.sort
end

if plugin_strings.length > 0
    puts
    puts "Plugin Strings:"
    puts plugin_strings.map(&:strip).uniq.sort
end