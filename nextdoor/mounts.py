#! /usr/bin/sudo /usr/bin/python3

# ---
# RightScript Name: mounts
# Description:
# Parameters:
#   - RS_CLOUD_PROVIDER
#   - STORAGE_RAID_LEVEL
#   - STORAGE_FSTYPE
#   - STORAGE_VOLCOUNT
#   - AWS_ACCESS_KEY_ID
#   - AWS_SECRET_ACCESS_KEY
#   - STORAGE_TYPE
#   - EBS_TYPE
#   - STORAGE_VOLIDLIST
#   - STORAGE_SIZE
#   - STORAGE_MOUNTPOINT
#   - STORAGE_BLOCK_SIZE
#   - STORAGE_MOUNTPOINT
#   - MOUNT_OPTS
#   - STORAGE_NO_PARTITIONS_EXIT_CODE
#   - EXCLUDED_PARTITIONS
#   - ENABLE_BCACHE
#   - BCACHE_MODE
#   - DEBUG
#
import os
from os import environ

from lib.python.utils import detect_debug_mode, assert_command, log_and_stdout


def main():
    """
    The Fun Starts Here.
    """
    detect_debug_mode()

    # Shell out to the oddball storage script from external deps.
    # See the external_dependencies.yml for details.

    # By default, put the storage script in "Big Hammer" mode.
    os.environ['VERBOSE'] = '1'
    os.environ['FORCE'] = '1'
    os.environ['DRY'] = '0'

    # The new storage script does not consistently honor all of the names
    # dumped in the environment by previous iterations of the RightScripts
    # so we're going to have to do a dirty little translation.

    translated = {
        'STORAGE_MOUNTPOINT': 'MOUNT_POINT',
    }
    for key, val in translated.items():
        if key in environ:
            log_and_stdout("   *** Translating {}={} into {}={} for mount"
                           " script ***   ".format(
                               key,
                               environ.get(key),
                               val,
                               environ.get(key)))
            os.environ[val] = os.environ.get(key)

    assert_command("chmod +x ./setup.sh ./setup_aws.sh ./common.sh"
                   " ./addons/bcache.sh",
                   'Failed to mark storage scripts executable!',
                   cwd='./lib/shell/storage-scripts')

    assert_command('./setup.sh',
                   'Storage/Volume setup failed!',
                   cwd='./lib/shell/storage-scripts')

if "__main__" == __name__:
    main()
