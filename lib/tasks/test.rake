require 'colorize'

desc 'Test All The Things!'
task :test => [:prep, :syntax, 'lint:check'] do
  puts "Executing task :test => ['prep', 'syntax', 'lint:check']".green
end
