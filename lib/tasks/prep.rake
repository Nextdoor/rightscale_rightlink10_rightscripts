begin
  require 'colorize'
rescue LoadError
  abort("colorize gem not found!")
end

desc 'Install supporting tooling for syntax|lint|etc checks.'
task :prep do
  puts "Executing task 'prep'...".green

  unless Dir.chdir Rake.application.original_dir 
    abort "Failed setting cwd to location of Rakefile!".red
  end
    
  puts "Executing 'bundle install'...".green
  unless system('bundle install') 
    abort "Exit status: #{$?.exitstatus}".red
  end

  puts "Upgrading to reasonably modern version of pip..".green
  unless system("pip install --upgrade pip")
    abort("Failed while installing a reasonably modern version of pip!".red + \
          "Exit code: #{$?.exitstatus}".red)
  end
  
  puts "Executing 'pip install -r requirements.txt'...".green
  unless system('pip install -r requirements.txt')
    puts "Exit status: #{$?.exitstatus}".red
  end
end
