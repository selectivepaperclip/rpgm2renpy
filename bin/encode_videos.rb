#!/usr/bin/env ruby

require 'json'
require 'fileutils'
require 'awesome_print'
require 'tmpdir'
require 'optparse'

if ENV['FFMPEG_PATH'] == nil
  puts "Need to set FFMPEG_PATH env variable before running!"
  exit 0
end

if ARGV.length < 1
  puts "Usage: #{$0} path/to/an/rpgmaker/xp/vx/or/vxace/game"
  exit 0
end

$options = {}
OptionParser.new do |opts|
  opts.on("-sSOURCE", "--source=SOURCE", "Where to look for animations") do |s|
    $options[:source] = s
  end
  opts.on("-eEXT", "--extension=EXT", "Force a file extension for intermediate files (for when renpy images are jpegs mislabeled as png)") do |ext|
    $options[:ext] = ext
  end
end.parse!

game_dir = File.expand_path(ARGV[0])
if File.exist?(File.join(game_dir, 'Graphics'))
    $pics_dir = File.join(game_dir, 'Graphics', 'Pictures')
    $movies_dir = File.join(game_dir, 'Graphics', 'Rpgm2RenpyMovies')
else
    $pics_dir = File.join(game_dir, 'www', 'img', 'pictures')
    $movies_dir = File.join(game_dir, 'www', 'Rpgm2RenpyMovies')
end
FileUtils.mkdir_p($movies_dir) if File.exist?($pics_dir)

def detect_animation(commands)
    animations = []
    queued_pictures = []
    last_indent = commands[0]['indent']
    faded_out = false
    commands.each_with_index do |command, command_index|
        code = command['code']
        indent = command['indent']
        if [101, 102, 103, 104, 301, 302, 303, 354].include?(code) || (indent != last_indent) || (command_index == commands.length - 1)
            if queued_pictures.length > 1
                animation = {}
                queued_pictures.each do |queued_picture|
                    if animation[queued_picture[:id]]
                        existing_frame = animation[queued_picture[:id]][-1]
                        if existing_frame.fetch(:delay, 0) > 0 && existing_frame[:image] != queued_picture[:image]
                            animation[queued_picture[:id]].push(queued_picture)
                        else
                            animation[queued_picture[:id]][-1] = queued_picture
                        end
                    else
                        animation[queued_picture[:id]] = [queued_picture]
                    end
                end

                animation.reject! do |k, v|
                    v.length < 2
                end

                animations.push(animation) if animation.length > 0
            end
            queued_pictures = []
        elsif [221].include?(code)
            faded_out = true
        elsif [222].include?(code)
            faded_out = false
        elsif [231].include?(code)
            picture_id = command['parameters'][0]
            picture_name = command['parameters'][1]
            queued_pictures.push({id: picture_id, delay: 0, image: picture_name, faded_out: faded_out})
        elsif [230].include?(code)
            if queued_pictures.length > 0
                queued_pictures.last[:delay] += command['parameters'][0]
            end
        end
        last_indent = indent
    end
    animations
end

real_animations = []

if $options[:source] == 'rpgm_data'
  maps = Dir[File.join(game_dir, 'JsonData', 'Map[0-9]*')]
  maps.each do |map_path|
      json = JSON.parse(File.read(map_path), symbolize_names: true)
      json['events'].compact.each do |event_json|
          event_json['pages'].each do |page_json|
              animations = detect_animation(page_json['list'])
              animations.each do |animation_group|
                  if animation_group and animation_group.length > 0
                      animation_group.each do |image_id, frames|
                          if frames && frames.length > 3
                              looks_like_animation = frames[-2][:image].gsub(/[\d]/, '') == frames[-1][:image].gsub(/[\d]/, '')
                              if looks_like_animation
                                  real_animations.push(animation_group)
                              else
                                  #puts "Maybe not animation: #{frames[-2][:image]} #{frames[-1][:image]}"
                              end
                          end
                      end
                  end
              end
          end
      end
  end
elsif $options[:source] == 'json_dump'
  jsons = Dir[File.join($movies_dir, '*.json')]
  jsons.each do |json_file_path|
    frame_content = File.read(json_file_path)
    frames_with_delay = JSON.parse(frame_content, symbolize_names: true)
    real_animations.push({
        File.basename(json_file_path) => frames_with_delay
    })
  end
end

def encode_video(real_animation_frames, outfile)
    Dir.mktmpdir do |dir|
        last_ext = nil
        real_animation_frames.each_with_index do |frame, frame_index|
            pic_file = Dir[File.join($pics_dir, frame[:image] + '.*')][0]
            unless pic_file
                print "COULD NOT FIND #{frame[:image]} in #{$pics_dir}"
                return
            end
            last_ext = $options[:ext] || File.extname(pic_file)
            FileUtils.cp(pic_file, File.join(dir, "frame_#{frame_index}#{last_ext}"))
        end

        pattern = File.join(dir, "frame_%d#{last_ext}")
        avg_delay = (real_animation_frames.map { |frame| frame[:delay] }).reduce(0, &:+) / real_animation_frames.length.to_f
        rate = (60.0 / avg_delay).round
        cmd = "#{ENV['FFMPEG_PATH']} -i #{pattern} -vcodec libvpx-vp9 -r #{rate} -crf 15 -b:v 0 -auto-alt-ref 0 \"#{outfile}\""
        puts cmd
        system(cmd)
    end
end

real_animations.each do |real_animation|
    real_animation.each do |picture_id, real_animation_frames|
        animation_name = "#{real_animation_frames[0][:image]}-#{real_animation_frames[-1][:image]}-#{real_animation_frames.length}frames"
        puts animation_name
        avg_waits = real_animation_frames.map { |f| f[:delay] }.reduce(&:+) / real_animation_frames.length.to_f
        if avg_waits != avg_waits.to_i
            print real_animation_frames.map { |f| f[:delay] }
        end
        outfile = File.join($movies_dir, "#{animation_name}.webm")
        if File.exists?(outfile)
            puts "... already exists!"
            next
        end
        if outfile =~ /^BH_Dodge/
            next
        end

        encode_video(real_animation_frames, outfile)
    end
end


#pic_groups = {}
#last_pic_path = nil
#sorted_pictures.each do |pic_path|
#  if last_pic_path
#      last_pic_parts = last_pic_path.match(/(.*?)(\d+)\.(.*)$/)
#      pic_parts = pic_path.match(/(.*?)(\d+)\.(.*)$/)
#      if last_pic_parts && pic_parts && last_pic_parts[1] == pic_parts[1] && last_pic_parts[2].to_i + 1 == pic_parts[2].to_i
#          pic_groups[pic_parts[1]] ||= {indices: [last_pic_parts[2]]}
#          pic_groups[pic_parts[1]][:indices].push(pic_parts[2])
#          pic_groups[pic_parts[1]][:ext] = pic_parts[3]
#      end
#  end
#  last_pic_path = pic_path
#end
#
#def file_indices_to_pattern(indices)
#    if indices[0][0] == "0"
#        "%0#{indices[0].length}d"
#    else
#        "%d"
#    end
#end
#
#pic_groups.each do |k, v|
#    puts k
#    pattern = "#{k}#{file_indices_to_pattern(v[:indices])}.#{v[:ext]}"
#    cmd = "#{ENV['FFMPEG_PATH']} -i #{pattern} -vcodec libvpx -r 60 -crf 15 -b:v 0 -auto-alt-ref 0 #{k.sub(/_$/, '')}.webm"
#    puts cmd
#    system(cmd)
#end_with
