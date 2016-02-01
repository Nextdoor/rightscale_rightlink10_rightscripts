require 'colorize'

desc 'Lint All The Things!'
task :lint do
  puts "Executing task 'lint'...".green

  puts "Linting Python files...".green
  python_files = FileList['**/*.{py}'].exclude(/bundle/)
  lint_cmd = "flake8 --count --statistics --show-source --show-pep8 --max-line-length=120"
  puts "#{lint_cmd} #{python_files}".light_blue
  unless system("#{lint_cmd} #{python_files}")
    abort("Lint check failed. Exit code: #{$?.exitstatus}").red
  end
end
