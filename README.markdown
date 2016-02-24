[![Build Status](https://travis-ci.org/Nextdoor/rightscale_rightlink10_rightscripts.svg?branch=master)](https://travis-ci.org/Nextdoor/rightscale_rightlink10_rightscripts)

# rightscale_rightlink10_rightscripts

Various Boot and Operational scripts for use with RightScale RightLink10.

## Overview

The scripts in ./nextdoor are intended to run as Boot or Operatonal
RightScripts in the context of RightScale. In the general case, the scripts
expect to take inputs from environment variables (set as RightInputs in
RightScale). The scripts aggressively validate both the presense and the format
of the values in the expected envvars.

All scripts are written such that missing or invalidated inputs will result in
the script exiting immediately with no attempt to recover (Fail Fast!).

The scripts are also written to provide maximum visibility into their inner
workings. This manifests primarily in two ways:

1. Whenver a script shells out to a command-line tool it prints both the
command and the resulting input to both stdout and syslog.

1. Setting the environment variable 'DEBUG' to any value will result in
the script printing every available environment variable to both stdout and
syslog formatted as blob of JSON.

It should be noted that all environment variable inputs for a script are
documented in *both* the ./nextdoor/metadata.rb and in the comment headers
for each of the scripts.

## Runtime Requirements

* Python3 *and* Python 2.7 - the scripts in the ./nextdoor directory are
written to Python3 and actually have python3 encoded in their bin magic line.
Some of the scripts in the ./nextdoor/lib directory are written to Python 2.7.

## Usage

All inputs are environment variables / RightInputs. A 'DEBUG' is available
for debugging / verbose operation.

## Development Tooling

Various development tooling is embedded in the repo. *None* of which is
necessary for operation of the scripts in the context of RightScale/RightLink10.

### Installing the dev tooling

#### Recommended
The following tools are highly recommended though not strictly required
(I think...;):

* [anyenv](https://github.com/riywo/anyenv)
* [pyenv](https://github.com/yyuu/pyenv)
* [rbenv](https://github.com/rbenv/rbenv)

#### Required Basics

* Ruby 2.x
* Python 3.x


#### Installing Dev Tools

* To install the various dev tools libraries:

```ShellSession
$ pip install -r requirements && gem install bundler && \
bundle install
```

#### Available Dev Tools

##### Ruby's guard/Guardfile

It's quite time-consuming to push code, reload the RightScale Repository,
perhaps even Relaunch the RightScale server.

Ruby's guard gem will allow you to push the scripts to a live RightScript node's
/var/spool/rightlink/cookbooks/<uuid> directory so long as

1. you have the required ssh keypair in place on the remote node
1. you set the value of the envvar RIGHTLINK10_NODE to the address of the remote
server.
1. you set the value of the envvar RIGHTLINK10_COOKBOOKS_DIR to the has of the
RightLink spool directory.

For example:

```ShellSession
$ export RIGHTLINK10_NODE='10.x.x.x'
$ export RIGHTLINK10_COOKBOOKS_DIR='<hash from /var/spool/rightlink>'
$ bundle exec guard
```

And, yes, ideally there would have been a Python equivalent to Ruby's guard
and thus the environment could be simplified. I did not find such an analogue
in the Python community.

##### Python invoke

Python 'invoke' is a subproject of the Fabric project. For our purposes it fills
a similar slot to Ruby's Rake in that it can be used to run tests locally and
it is reference in the included 'circle.yaml' which is consumed by CircleCI.

The following invoke tasks are available:

```ShellSession
$ invoke -l

Available tasks:

  prep         Download and place external dependencies as a way to avoid
  syntax       Recursively syntax check various files.
  test         Run syntax + lint check.
  lint.check   Recursively lint check Python files in this project using flake8.
  lint.fix     Recursively lint check **and fix** Python files in this project using autopep8.
```

These tasks are defined in the 'tasks.py' file in the root of the repo.

###### Invoke tasks

* prep - This tasks populates the ./nextdoor/lib directories with external
dependencies like [Kingpin](https://github.com/nextdoor/kingpin) and the shell
scripts used for managing EBS mounts [storage-scripts](https://github.com/diranged/storage-scripts).
The 'prep' task consumes the 'external_depencies.yml' file in the root of the
repo. Think of this as lightweight way to:

1. ensure that all dependencies are part of this canonical repo for RigthLink10 scripts
1. avoid having to muck about with git submodules or subtrees

The task will blow away existing directories for dependencies,
re-clone from git repo, and then remove the .git directory of the dependency.

Nice, simple, self-contained...

Here's an example of the YAML for the dependency resolver:

```YAML
---
repos:

  kingpin:
    type: git
    source: https://github.com/nextdoor/kingpin
    ref: v0.2.6
    destination: ./nextdoor/lib/python/kingpin

  storage-scripts:
    type: git
    source: https://github.com/diranged/storage-scripts
    ref: 2a9da7ef98ae2b79053b7f04487f1e08a09331b5
    destination: ./nextdoor/lib/shell/storage-scripts
```

* syntax - Perform a syntax check of everything I can think to check: Python, Ruby,
YAML, etc.**
* lint.check - Perform a lint check of Python code.
* link.fix - The Python linter, autopep, can *fix* common issues like whitespace.
* test - Run syntax and lint checks; a convenience task used in CI configs.

** Note: Some of the code in dependencies in ./nextdoor/lib is either not Python3 or
doesn't pass Python lint check or both. These directories are specifically excluded from
checks via code in 'tasks.py'.

Here's an example of an 'invoke test' run:

```ShellSession
$ invoke test
Syntax checking of YAML files...
/home/nrvale0/workspace/rightscale_rightlink10_rightscripts/.travis.yml
/home/nrvale0/workspace/rightscale_rightlink10_rightscripts/external_dependencies.yml
/home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/lib/python/kingpin/.travis.yml
Syntax checking of Python files...
python -m py_compile /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/tasks.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/elb-connect.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/hostname.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/mounts.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/dump-env.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/elb-disconnect.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/puppet-install.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/lib/python/attic/volume.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/lib/python/attic/google_volume.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/lib/python/utils/__init__.py
Syntax checking of Ruby files...
ruby -c /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/metadata.rb
Syntax OK
Exit code: 0
Lint checking of Python files...
flake8 --count --statistics --show-source --show-pep8 --max-line-length=160 --ignore=E402,E266,F841 /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/tasks.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/elb-connect.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/hostname.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/mounts.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/dump-env.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/elb-disconnect.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/puppet-install.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/lib/python/attic/volume.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/lib/python/attic/google_volume.py /home/nrvale0/workspace/rightscale_rightlink10_rightscripts/nextdoor/lib/python/utils/__init__.py
Exit code: 0
```
