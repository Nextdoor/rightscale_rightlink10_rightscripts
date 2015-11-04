##
##
## Python utility functions for RightScale RightScript use.
##
## Author: Nathan Valentine <nathan@nextdoor.com>
##

import os
from os import environ
import sys
import json
from subprocess import check_output, PIPE, STDOUT, CalledProcessError
import re


def is_volumized():
    if os.path.exists('/etc/nextdoor/volumized'):
        return True
    else:
        return False
    

def assert_command(cmd, msg, shell=False):
    print "   *** Executing command: {} ***   ".format(cmd)
    
    try:
        print(check_output(cmd.split(), stderr=STDOUT, shell=shell))
        
    except CalledProcessError, e:
        print "   *** {0} ***   ".format(msg)
        print "retcode: {0} :: {1} :: {2}".format(e.errno, cmd, e.strerror)
        sys.exit(e.errno)

    return 0

        
def validate_env(envvar, regex):
    if not envvar in environ:
        print "   *** \'{0}\' not found in environment!  ***".format(envvar)
        sys.exit(-1)

    if None == re.match(regex, os.environ[envvar]):
        print "   *** \'{0}\'=\'{1}\' does not match RE \'{2}\'! ***".format(envvar, os.environ[envvar], regex)
        sys.exit(-1)
        
    else:
        return True
        
        
def volumize():
    assert_command('mkdir -p /etc/nextdoor/volumized', "Could not create Nextdoor's volumize lock file!")

        
def detect_debug_mode():
    if "DEBUG" in environ:
        dump_environment()

        
def dump_environment():
    print(
        json.dumps(environ.__dict__,
                   indent=4,
                   sort_keys=True))
