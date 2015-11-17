##
##
## Python utility functions for RightScale RightScript use.
##
## Author: Nathan Valentine <nathan@nextdoor.com>
##

import os, errno, sys, json, re, logging, logging.handlers
from os import environ
from subprocess import check_output, PIPE, STDOUT, CalledProcessError

logger = logging.getLogger(sys.argv)
logger.setLevel(logging.info)
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
    except OSError as exc: # Python >2.5
        if errno.EEXIST == exc.errno and os.path.isdir(path):
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
def log_and_stdout(msg):
    logger.info(msg)
    print msg
    
#
#
#
def assert_command(cmd, msg, shell=False, cwd=None, retries=1):
    
    log_and_stdout("   *** Executing command: {} ***   ".format(cmd))

    ret = 0
    attempts = 0
    output = ''
    
    while attempts < retries:
        attempts += 1
        try:
            output = check_output(cmd.split(), stderr=STDOUT, shell=shell, cwd=cwd)
            log_and_stdout(output)
            
        except CalledProcessError, e:
            log_and_stdout(output)
            log_and_stdout("   *** {0} ***   ".format(msg))
            log_and_stdout("retcode: {0} :: {1} :: {2}".format(e.returncode, cmd, e.output))
            ret = e.returncode

    if 0 != ret:
        if 1 != retries:
            msg = "Exceeded specified restries: {} :: {}".format(retries, msg)
            logging.error(msg)
            sys.exit(msg)
        else:
            sys.exit(msg)

    return True


#
#
#
def validate_env(envvar, regex):
    if not envvar in environ:
        msg = "   *** \'{0}\' not found in environment!  ***".format(envvar)
        logger.error(msg)
        sys.exit(msg)

    if None == re.match(regex, os.environ[envvar]):
        msg = "   *** \'{0}\'=\'{1}\' does not match RE \'{2}\'! ***".format(envvar, os.environ[envvar], regex)
        logger.error(msg)
        sys.exit(msg)
        
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
