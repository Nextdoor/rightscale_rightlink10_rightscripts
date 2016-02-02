require 'colorize'

desc 'Test All The Things!'
task :test => [:prep, :syntax, 'lint:check'] do
  unless system("pip install --upgrade pip")
    abort("Failed while installing a reasonably modern version of pip!".red + \
          "Exit code: #{$?.exitstatus}".red)
  end
  puts "Executing task :test => ['prep', 'syntax', 'lint:check']".green
end
