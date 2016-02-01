desc 'Install supporting tooling for syntax|lint|etc checks.'
task :prep do
  puts "Executing task 'prep'..."

  unless Dir.chdir Rake.application.original_dir 
    abort "Failed setting cwd to location of Rakefile!"
  end
    
  puts "Executing 'bundle install'..."
  system('bundle install')
  puts "Exit status: #{$?.exitstatus}"

  puts ""
  
  puts "Executing 'pip install -r requirements.txt'..."
  system('pip install -r requirements.txt')
  puts "Exit status: #{$?.exitstatus}"
end
