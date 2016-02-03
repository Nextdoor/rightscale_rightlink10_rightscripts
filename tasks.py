import os
import fnmatch
from invoke import run, task, Collection
from colorama import init, Fore

PEP8_IGNORE = 'E402,E266'
init()


def find_files(pattern):
    matches = []
    for root, dirnames, filenames in os.walk(os.path.dirname(__file__)):
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(os.path.join(root, filename))
    return matches


@task
def syntax():
    print(Fore.GREEN + "Syntax checking of Python files...")

    python_files = find_files('*.py')
    cmd = "pyflakes {}".format(' '.join(python_files))
    result = run(cmd, echo=True)

    # won't get here unless things run clean
    print(Fore.GREEN + "Exit code: {}".format(result.return_code))


@task
def lint_check():
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
    print(Fore.GREEN + "Lint fixing Python files...")

    python_files = find_files('*.py')
    cmd = """
autopep8 -r --in-place --ignore={} {}
""".format(PEP8_IGNORE, ' '.join(python_files))
    result = run(cmd, echo=True)

    # won't get here unless things run clean
    print(Fore.GREEN + "Exit code: {}".format(result.return_code))


@task(syntax, lint_check, lint_fix)
def test():
    pass


ns = Collection('')

lint = Collection('lint')
lint.add_task(lint_check, 'check')
lint.add_task(lint_fix, 'fix')
ns.add_collection(lint)

ns.add_task(test, 'test')
ns.add_task(syntax, 'syntax')
