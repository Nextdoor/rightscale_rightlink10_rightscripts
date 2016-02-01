[![Build Status](https://travis-ci.org/Nextdoor/rightscale_rightlink10_rightscripts.svg?branch=master)](https://travis-ci.org/Nextdoor/rightscale_rightlink10_rightscripts)

# rightscale_rightlink10_rightscripts

Various Boot and Operational scripts for use with Rightlink10.

## Requirements

* Ruby (rbenv suggested)
* Rake
* Bundler

## Install and Usage

To setup the environment, including not only the Ruby deps but also the
Python deps:

```ShellSession
$ bundle exec rake prep
```

Additional Rake tasks are available:

```ShellSession
$ bundle exec rake -T
rake lint    # Lint All The Things!
rake prep    # Install supporting tooling for syntax|lint|etc checks
rake syntax  # Check All The Syntax!
rake test    # Test All The Things!
```
