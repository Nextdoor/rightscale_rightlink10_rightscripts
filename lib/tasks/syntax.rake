require 'yaml'
require 'json'
require 'colorize'

unless Dir.chdir Rake.application.original_dir 
  abort "Failed setting cwd to location of Rakefile!".red
end

desc 'Check All The Syntax!'
task :syntax do
  puts "Executing task 'syntax'...".green

  puts "Syntax checking YAML files...".green
  yaml_files = FileList['**/*.{yaml,yml}'].exclude(/bundle/)
  yaml_files.each do |yaml_file|
    puts "Checking #{yaml_file}...".green
    begin
      YAML.load_file(yaml_file)
    rescue Psych::SyntaxError => e
      abort e.to_s
    end
  end

  puts "Syntax checking JSON files...".green
  json_files = FileList['**/*.{json}'].exclude(/bundle/)
  json_files.each do |json_file|
    puts "Checking #{json_file}...".green
    begin
      JSON.parse(File.read(json_file))
    rescue JSON::ParserError => e
      abort e.to_s.red
    end
  end

  puts "Syntax checking Ruby files...".green
  ruby_files = FileList['**/*.rb'].exclude(/bundle/)
  ruby_files.each do |ruby_file|
    puts "Checking #{ruby_file}...".green
    %x{ruby -c #{ruby_file}}
  end

  puts "Syntax checking Python files...".green
 python_files = FileList['**/*.py'].exclude(/bundle/)
  puts "pyflakes #{python_files}".light_blue
  unless system("pyflakes #{python_files}")
    abort("Syntax check failed. Exit code: #{$?.exitstatus}".red)
  end
end
