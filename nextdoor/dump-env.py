#! /usr/bin/sudo /usr/bin/python

# ---
# RightScript Name: dump-env
# Description:
#   Dump the shell environment for debugging purposes iff the shell environment
#   has 'DEBUG' set to any value.
# Parameters:
#   - DEBUG
#

from lib.python import utils

utils.dump_environment()
