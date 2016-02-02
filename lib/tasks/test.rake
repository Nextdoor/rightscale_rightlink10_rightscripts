require 'colorize'

desc 'Test All The Things!'
task :test => [:syntax, 'lint:check'] do
  puts "Executing task :test => ['syntax', 'lint:check']".green
end
