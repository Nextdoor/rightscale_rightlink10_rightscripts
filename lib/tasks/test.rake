desc 'Test All The Things!'
task :test => [:syntax, :lint] do
  puts "Executing task 'test'..."
end
