
#
#
# Python utility functions for RightScale RightScript use.
#
# Author: Nathan Valentine <nathan@nextdoor.com>
#

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
logger.addHandler(logging.handlers.SysLogHandler('/dev/log'))

# sneaky way to make debconf stay out of the way ;)
environ['DEBIAN_FRONTEND'] = 'noninteractive'
environ['DEBCONF_NONINTERACTIVE_SEEN'] = 'true'


def normalize_hostname_to_rfc(mystr):
    """
    Given a hostname, normalize to Nextdoor hostname standard

    Args:
      mystr (str): hostname to normalize

    Returns:
      normalized hostname

    Details:
      * lower everthing
      * delete anything which is not alphanumeric
      * compress multiple '.' or '-'
      * strip leading '-'s
    """
    return re.sub('^[-]+', '', re.sub('[.]{2,}', '.', re.sub('[-]{2,}', '-', re.sub('[^a-z0-9-._]', '', mystr.lower()))))


def mkdir_p(path):
    """
    Emulate UNIX 'mkdir -p'.

    Args:
      path (str): filesystem path to create

    Returns:
      nothing on success; OSError on fail
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if errno.EEXIST == exc.errno and os.path.isdir(path):
            pass
        else:
            raise


def is_volumized():
    """
    Return boolean indicating if the system has been previsously 'volumized'.

    Returns:
      boolean

    Details:
      Presence of /etc/nextdoor/volumized is used to indicate the system has
      previously had volumes initialized into a RAID array.
    """
    if os.path.exists('/etc/nextdoor/volumized'):
        return True
    else:
        return False


def log_and_stdout(msg):
    """
    Send msg to to both stdout and syslog.

    Args:
      msg (str): message to send to stdout and syslog

    Returns:
      nothing
    """

    if not isinstance(msg, (str, bytes, bytearray)):
        log_and_stdout("   *** Should never get here! Something passed was not"
                       " a str, bytes, or a bytearray!")

    if isinstance(msg, (bytes, bytearray)):
        msg = msg.decode('utf-8', errors='replace')

    logger.info(msg)
    print(msg)


def assert_command(cmd, msg, shell=False, cwd=None, retries=1):
    """
    Execute the passsed command w/ optional cwd and retries.

    Args:
      cmd (str): command to execute
      msg (str): message to log to stdout and syslog upon execution
      shell (boolean) : optionally use shell instead of system()
      cwd (str): optionally set the cwd for the command
      retries: optionally retry the command some number of times

    Returns:
      boolean True on success; sys.exit upon failure

    Details:
      If 'retries' is specified, the command will be retried until it succeeds
      or the number of retries is exhausted. A single success run will return
      boolean True regardless of previous failures.
    """

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

        except CalledProcessError as e:
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


def validate_env(envvar, regex):
    """
    Check for presence of env variable and validate its value against regex.

    Args:
      envvar(str): the env var to check
      regex: the regex used for validation

    Returns:
      boolean true if validation passes; sys.exit if not present or does not
      validate
    """
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


def volumize():
    """
    Set the 'volumized' lock file.

    Details:
    This lock file is used to indicate the system has previously had volumes
    inititialized and RAIDed.
    """
    assert_command('mkdir -p /etc/nextdoor/volumized',
                   "Could not create Nextdoor's volumize lock file!")


def detect_debug_mode():
    """
    If the shell's env variables include 'DEBUG' print all env vars to stdout.
    """
    if "DEBUG" in environ:
        dump_environment(to_var=True)


def dump_environment(to_var=False):
    """
    Dump the shell's env vars to stdout as JSON document.

    Args:
      to_var (boolean): also dump the env vars to /var?
    """
    print(
        json.dumps({k: os.environ[k] for k in os.environ.keys()},
                   indent=4,
                   sort_keys=True))

    if to_var:
        try:
            with open('env.sh', 'w') as env_log:
                env_log.write("# {}\n".format(time.strftime("%c")))
                for key, value in environ.items():
                    env_log.write('export {}="{}"\n'.format(key, value))
        except IOError as e:
            log_and_stdout(str(e))
            log_and_stdout("Failed to create env.sh in cookbook dir...")


def apt_get_update(refresh_interval_mins=30):
    """
    Run apt-get update if it has not been run within specified minutes.
    """

    refresh_interval = refresh_interval_mins * 60
    time_stamp_file = '/var/run/nextdoor_apt_get_update.lock'
    run_cmd = False  # shall we run the apt-get

    if not os.path.exists(time_stamp_file):
        open(time_stamp_file, 'w').close()
        run_cmd = True
    else:
        try:
            mtime = os.path.getmtime(time_stamp_file)
            if time.time() - mtime > refresh_interval:
                open(time_stamp_file, 'w').close()
                run_cmd = True
            else:
                log_and_stdout("   *** apt-get update run < {} minutes ago."
                               " Not re-running. ***   ".format(
                                   str(refresh_interval_mins)))

        except OSError as e:
            run_cmd = True

    if True is run_cmd:
        assert_command('apt-get update', 'Failed to update package cache!',
                       retries=5)
