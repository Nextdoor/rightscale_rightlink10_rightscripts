require 'colorize'

unless Dir.chdir Rake.application.original_dir 
  abort "Failed setting cwd to location of Rakefile!".red
end

python_files = FileList['**/*.{py}'].exclude(/bundle/)

namespace :lint do
  desc 'Lint All The Things!'
  task :check do
    puts "Executing task 'lint'...".green
    
    puts "Linting Python files...".green
    lint_cmd = "flake8 --count --statistics --show-source --show-pep8 --max-line-length=160"
    puts "#{lint_cmd} #{python_files}".light_blue
    unless system("#{lint_cmd} #{python_files}")
      abort("Lint check failed. Exit code: #{$?.exitstatus}".red)
    end
  end
  
  desc 'Attempt to auto-fix linting problems'
  task :fix do
    
    puts "Automagically fixing linting issues...".green
    lintfix_cmd = 'autopep8 --in-place'
    puts "#{lintfix_cmd} #{python_files}"
    unless system("#{lintfix_cmd} #{python_files}")
      abort("Failed with auto-fixing lint issues! Exit code: #{$?.exitstatus}".red)
    end
  end
  
end


