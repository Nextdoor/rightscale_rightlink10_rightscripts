##
##
## Python utility functions for RightScale RightScript use.
##
## Author: Nathan Valentine <nathan@nextdoor.com>
##

import os, errno, sys, json, re
from os import environ
from subprocess import check_output, PIPE, STDOUT, CalledProcessError


#
#
#
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


#
#
#
def is_volumized():
    if os.path.exists('/etc/nextdoor/volumized'):
        return True
    else:
        return False
    

#
#
#
def assert_command(cmd, msg, shell=False, cwd=None):
    print "   *** Executing command: {} ***   ".format(cmd)
    
    try:
        print(check_output(cmd.split(), stderr=STDOUT, shell=shell, cwd=cwd))
        
    except CalledProcessError, e:
        print "   *** {0} ***   ".format(msg)
        print "retcode: {0} :: {1} :: {2}".format(e.returncode, cmd, e.output)
        sys.exit(e.returncode)

    return 0

#
#
#
def validate_env(envvar, regex):
    if not envvar in environ:
        print "   *** \'{0}\' not found in environment!  ***".format(envvar)
        sys.exit(-1)

    if None == re.match(regex, os.environ[envvar]):
        print "   *** \'{0}\'=\'{1}\' does not match RE \'{2}\'! ***".format(envvar, os.environ[envvar], regex)
        sys.exit(-1)
        
    else:
        return True


#
#
#
def volumize():
    assert_command('mkdir -p /etc/nextdoor/volumized', "Could not create Nextdoor's volumize lock file!")


#
#
#
def detect_debug_mode():
    if "DEBUG" in environ:
        dump_environment()


#
#
#
def dump_environment():
    print(
        json.dumps(environ.__dict__,
                   indent=4,
                   sort_keys=True))
