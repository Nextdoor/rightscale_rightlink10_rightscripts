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

* Whenver a script shells out to a command-line tool it prints both the
command and the resulting input to both stdout and syslog. Here's an example:

```ShellSession
   *** Executing command (1 of 1 attempts): apt-get install -y puppet-common=3.7.4-1puppetlabs1 puppet=3.7.4-1puppetlabs1 ***   
Reading package lists...
Building dependency tree...
Reading state information...
The following extra packages will be installed:
  debconf-utils facter hiera libaugeas-ruby libruby1.9.1 ruby ruby-augeas
  ruby-json ruby-shadow ruby1.9.1 virt-what
Suggested packages:
  puppet-el vim-puppet ruby-selinux libselinux-ruby1.8 librrd-ruby1.9.1
  librrd-ruby1.8 ri ruby-dev ruby1.9.1-examples ri1.9.1 graphviz ruby1.9.1-dev
  ruby-switch
Recommended packages:
  rdoc
The following NEW packages will be installed:
  debconf-utils facter hiera libaugeas-ruby libruby1.9.1 puppet puppet-common
  ruby ruby-augeas ruby-json ruby-shadow ruby1.9.1 virt-what
0 upgraded, 13 newly installed, 0 to remove and 88 not upgraded.
Need to get 4180 kB of archives.
After this operation, 21.8 MB of additional disk space will be used.
Get:1 http://us-west-2.ec2.archive.ubuntu.com/ubuntu/ trusty/main debconf-utils all 1.5.51ubuntu2 [57.4 kB]
Get:2 http://us-west-2.ec2.archive.ubuntu.com/ubuntu/ trusty-updates/main libruby1.9.1 amd64 1.9.3.484-2ubuntu1.2 [2645 kB]
Get:3 http://us-west-2.ec2.archive.ubuntu.com/ubuntu/ trusty-updates/main ruby1.9.1 amd64 1.9.3.484-2ubuntu1.2 [35.6 kB]
Get:4 http://us-west-2.ec2.archive.ubuntu.com/ubuntu/ trusty/main ruby all 1:1.9.3.4 [5334 B]
...
```

* Setting the environment variable 'DEBUG' to any value will result in
the script printing every available environment variable to both stdout and
syslog formatted as blob of JSON. Here's an example:

```ShellSession
********************************************************************************
*RS> Recipe: 'nextdoor::puppet-install' ***
*RS> Starting at 2016-02-25 18:58:07 UTC
STDERR>
{
    "DEBUG": "1",
    "HOME": "/home/rightlink",
    "LOGNAME": "root",
    "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    "PUPPET_AGENT_USE_CACHED_CATALOG": "false",
    "PUPPET_AGENT_VERSION": "3.7.4-1puppetlabs1",
    "PUPPET_CA_SERVER": "<redacted>",
    "PUPPET_CHALLENGE_PASSWORD": "<hidden credential>",
    "PUPPET_CUSTOM_FACTS": "fact1=value1,fact2=value2",
    "PUPPET_ENABLE_REPORTS": "true",
    "PUPPET_ENVIRONMENT_NAME": "production",
    "PUPPET_NODE_NAME": "facter",
    "PUPPET_NODE_NAME_FACT": "hostname",
    "PUPPET_SERVER_HOSTNAME": "<redacted>",
    "RS_SELF_HREF": "/api/clouds/6/instances/2DL46EUISCV08",
    "SHELL": "/bin/bash",
    "SUDO_COMMAND": "/usr/bin/python3 /var/spool/rightlink/cookbooks/0337c49dc2f1fc8100dc28a3e098d3de/puppet-install.py",
    "SUDO_GID": "1001",
    "SUDO_UID": "1001",
    "SUDO_USER": "rightlink",
    "TERM": "linux",
    "USER": "root",
    "USERNAME": "root",
    "account": "<redacted>",
    "api_hostname": "us-3.rightscale.com",
    "client_id": "<redacted>"
}
```

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
it is reference in the included '.travis.yaml' which is consumed by TravisCI.

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
