import os, sys
import fnmatch
from invoke import run, task, Collection
from colorama import init, Fore
import yaml

PEP8_IGNORE = 'E402,E266,F841'
init()


def find_files(pattern):
    """
    Recursive find of files matching pattern starting at location of this script.

    Args:
      pattern (str): filename pattern to match

    Returns:
      array: list of matching files
    """
    matches = []
    for root, dirnames, filenames in os.walk(os.path.dirname(__file__)):
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(os.path.join(root, filename))
    return matches


@task
def prep():
    """
    Download and place external dependencies as a way to avoid
    git submodules/subtrees. Would be nice if librarian could be leveraged...
    """

    newcwd = sys.path[0]
    if '' != newcwd:
        # I'm not sure this is absolutely necessary but to be careful...
        print(Fore.GREEN + "Changing cwd to {}".format(newcwd))
        os.chdir(sys.path[0])
    else:
        sys.exit("I am very confused about our sys.path[0] of ''!")

    deps = {}
    with open('external_dependencies.yml') as deps:
        try:
            deps = yaml.load(deps)
        except yaml.YAMLError as e:
            print(Fore.RED + str(e))
            sys.exit(-1)

    print(str(deps))
    # find deps file and load deps from YAML
    # for repo in repos:
    # cd to appropriate libdir
    # clone repo
    # checkout out branch/tag/commit


@task
def syntax():
    """
    Recursively syntax check various files.
    """

    print(Fore.GREEN + "Syntax checking of YAML files...")
    yaml_files = find_files('*.yaml') + find_files('*.yml')
    for yaml_file in yaml_files:
        with open(yaml_file, 'r') as f:
            print(Fore.WHITE + yaml_file)
            try:
                yaml.load(f)
            except yaml.YAMLError as e:
                print(Fore.RED + str(e))

    print(Fore.GREEN + "Syntax checking of Python files...")
    python_files = find_files('*.py')
    cmd = "python -m py_compile {}".format(' '.join(python_files))
    result = run(cmd, echo=True)

    print(Fore.GREEN + "Syntax checking of Ruby files...")
    ruby_files = find_files('*.rb')
    cmd = "ruby -c {}".format(' '.join(ruby_files))
    result = run(cmd, echo=True)

    # won't get here unless things run clean
    print(Fore.GREEN + "Exit code: {}".format(result.return_code))


@task
def lint_check():
    """
    Recursively lint check Python files in this project using flake8.
    """
    print(Fore.GREEN + "Lint checking of Python files...")

    python_files = find_files('*.py')
    cmd = """
flake8 --count --statistics --show-source --show-pep8 --max-line-length=160 \
--ignore={} {}""".format(PEP8_IGNORE, ' '.join(python_files))
    result = run(cmd, echo=True)

    # won't get here unless things run clean
    print(Fore.GREEN + "Exit code: {}".format(result.return_code))


@task
def lint_fix():
    """
    Recursively lint check **and fix** Python files in this project using autopep8.
    """
    print(Fore.GREEN + "Lint fixing Python files...")

    python_files = find_files('*.py')
    cmd = """
autopep8 -r --in-place --ignore={} {}
""".format(PEP8_IGNORE, ' '.join(python_files))
    result = run(cmd, echo=True)

    # won't get here unless things run clean
    print(Fore.GREEN + "Exit code: {}".format(result.return_code))


@task(syntax, lint_check)
def test():
    """
    Run syntax + lint check.
    """
    pass


ns = Collection('')

lint = Collection('lint')
lint.add_task(lint_check, 'check')
lint.add_task(lint_fix, 'fix')
ns.add_collection(lint)

ns.add_task(prep, 'prep')
ns.add_task(test, 'test')
ns.add_task(syntax, 'syntax')
