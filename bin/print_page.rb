#!/usr/bin/env ruby

require 'json'
require 'fileutils'
require 'awesome_print'
require 'optparse'

if ARGV.length != 3
  puts "Usage: #{$0} map_file event_id page_id"
  exit 0
end

map_file = ARGV[0]
event_id = ARGV[1].to_i
page_id = ARGV[2].to_i

json = JSON.parse(File.read(map_file))

command_list = json['events'][event_id]['pages'][page_id]['list']
max_command_number_characters = command_list.length.to_s.length
command_number_format_string = "%0#{max_command_number_characters}d"
command_list.each_with_index do |command, index|
    puts "#{command_number_format_string % index} #{"    " * command['indent']} #{command.inspect}"
end
