##
##
# Python utility functions for RightScale RightScript use.
##
# Author: Nathan Valentine <nathan@nextdoor.com>
##

import os
import errno
import sys
import json
import re
import logging
import logging.handlers
import time
from os import environ
from subprocess import check_output, STDOUT, CalledProcessError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.handlers.SysLogHandler())


#
#
#
def normalize_hostname_to_rfc(mystr):
    # LOL!
    # 1. lower everthing
    # 2. delete anything which is not alphanumeric
    # 3 & 4 compress multiple '.' or '-'
    # 5 strip leading '-'s
    return re.sub('^[-]+', '', re.sub('[.]{2,}', '.', re.sub('[-]{2,}', '-', re.sub('[^a-z0-9-._]', '', mystr.lower()))))


#
#
#
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if errno.EEXIST == exc.errno and os.path.isdir(path):
            pass
        else:
            raise


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
def log_and_stdout(msg):
    logger.info(msg)
    print msg

#
#
#


def assert_command(cmd, msg, shell=False, cwd=None, retries=1):

    attempts = 0

    while attempts < retries:
        attempts += 1
        ret = 0
        output = ''

        try:
            progress = "   *** Executing command ({} of {} attempts): {} ***   ".format(
                attempts, retries, cmd)
            log_and_stdout(progress)
            output = check_output(
                cmd.split(), stderr=STDOUT, shell=shell, cwd=cwd)

        except CalledProcessError, e:
            ret = e.returncode
            output = e.output

        if 0 != ret:
            log_and_stdout(output)
            log_and_stdout("retcode: {} :: {}".format(ret, cmd))

            if attempts == retries:
                log_and_stdout(
                    "Exceeded specified retries: {} :: retcode: {} :: {}".format(retries, ret, msg))
                sys.exit(ret)
        else:
            log_and_stdout(output)
            break

    return True


#
#
#
def validate_env(envvar, regex):
    if envvar not in environ:
        msg = "   *** \'{0}\' not found in environment!  ***".format(envvar)
        log_and_stdout(msg)
        sys.exit(-1)

    if None is re.match(regex, os.environ[envvar]):
        msg = "   *** \'{0}\'=\'{1}\' does not match RE \'{2}\'! ***".format(
            envvar, os.environ[envvar], regex)
        log_and_stdout(msg)
        sys.exit(-1)

    else:
        return True


#
#
#
def volumize():
    assert_command('mkdir -p /etc/nextdoor/volumized',
                   "Could not create Nextdoor's volumize lock file!")


#
#
#
def detect_debug_mode():
    if "DEBUG" in environ:
        dump_environment(to_var=True)


#
#
#
def dump_environment(to_var=False):
    print(
        json.dumps(environ.__dict__,
                   indent=4,
                   sort_keys=True))
    if to_var:
        try:
            with open('env.sh', 'w') as env_log:
                env_log.write("# {}\n".format(time.strftime("%c")))
                for key, value in environ.iteritems():
                    env_log.write("export {}={}\n".format(key, value))
        except IOError:
            pass
