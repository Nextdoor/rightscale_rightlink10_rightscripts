require 'yaml'
require 'json'

desc 'Check All The Syntax!'
task :syntax do
  puts "Executing task 'syntax'..."

  puts "Syntax checking YAML files..."
  yaml_files = FileList['**/*.{yaml,yml}'].exclude(/bundle/)
  yaml_files.each do |yaml_file|
    puts "Checking #{yaml_file}..."
    begin
      YAML.load_file(yaml_file)
    rescue Psych::SyntaxError => e
      abort e.to_s
    end
  end

  puts "Syntax checking JSON files..."
  json_files = FileList['**/*.{json}'].exclude(/bundle/)
  json_files.each do |json_file|
    puts "Checking #{json_file}..."
    begin
      JSON.parse(File.read(json_file))
    rescue JSON::ParserError => e
      abort e.to_s
    end
  end

  puts "Syntax checking Ruby files..."
  ruby_files = FileList['**/*.rb'].exclude(/bundle/)
  ruby_files.each do |ruby_file|
    puts "Checking #{ruby_file}..."
    %x{ruby -c #{ruby_file}}
  end

  puts "Syntax checking Python files..."
  python_files = FileList['**/*.py'].exclude(/bundle/)
  python_files.each do |python_file|
    puts "Checking #{python_file}..."
    %x{python -m py_compile #{python_file}}
  end

end
