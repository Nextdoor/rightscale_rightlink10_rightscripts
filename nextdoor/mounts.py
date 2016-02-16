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
#   - DEBUG
#

import os
from os import environ
import sys

from lib.python import utils


def install_dependencies():
    """
    Instal some utilities we are goig to need to bootstrap Pupppet.
    """
    debs = 'python-pip xfsprogs'
    blacklist_debs = 'python-boto'
    pip_packages = 'boto'

    environ['DEBIAN_FRONTEND'] = 'noninteractive'
    environ['DEBCONF_INTERACTIVE_SEEN'] = 'true'

    assert_command('apt-get update', 'Unable to update APT cache!')
    assert_command('apt-get install -y ' + debs,
                   'Unable to install required .debs!')
    assert_command('apt-get remove --purge -y ' + blacklist_debs,
                   'Unable to remove blacklisted .deb!')
    assert_command('pip install ' + pip_packages,
                   'Unable to install a pip package!')

    return True


def ec2_mount():
    """
    Perform a mount of the EBS volumes.
    """
    mount_command = "python ./lib/python/volume.py -k {} -s {} -a {} -m {} -t {} {} {} {} {} {}"

    for key, regex in {
        'AWS_ACCESS_KEY_ID': '^.+$',
        'AWS_SECRET_ACCESS_KEY': '^.+$',
        'STORAGE_TYPE': '^(instance|ebs|remount-ebs)$',
        'EBS_TYPE': '^(standard|gp2|io1)$',
    }.iteritems():
        validate_env(key, regex)

    if not 'instance' == os.environ['STORAGE_TYPE']:
        validate_env('STORAGE_VOLIDLIST', '^.+$')
    else:
        os.environ['STORAGE_VOLIDLIST'] = ''

    mount_command = mount_command.format(
        os.environ['AWS_ACCESS_KEY_ID'],
        os.environ['AWS_SECRET_ACCESS_KEY'],
        os.environ['STORAGE_TYPE'],
        os.environ['STORAGE_MOUNTPOINT'],
        os.environ['EBS_TYPE'],
        os.environ['STORAGE_RAID_LEVEL'],
        os.environ['STORAGE_VOLCOUNT'],
        os.environ['STORAGE_VOLIDLIST'],
        os.environ['STORAGE_FSTYPE'],
        os.environ['STORAGE_SIZE']
    )

    assert_command(mount_command, 'Unable to mount the cloud storage!') and \
        volumize()


def google_mount():
    """
    Mount a Google volume.
    """
    mount_command = "python ./lib/python/google_volume.py -a instance -m {} {} -f {}"

    mount_command = mount_command.format(
        os.environ['STORAGE_MOUNTPOINT'],
        os.environ['STORAGE_RAID_LEVEL'],
        os.environ['STORAGE_FSTYPE']
    )

    assert_command(mount_command, 'Unable to mount the cloud storage!') and \
        volumize()


def mount_volumes():
    """
    Mount all configured storage volumes.
    """

    if not is_volumized():

        # validate the things which are common to all clouds
        for key, regex in {
                'RS_CLOUD_PROVIDER': '^(ec2|google)$',
                'STORAGE_VOLCOUNT': '^(0|2|4|6)$',
                'STORAGE_MOUNTPOINT': '^\/.+$',
                'STORAGE_RAID_LEVEL': '^(0|1|5|10)',
                'STORAGE_FSTYPE': '^(xfs|ext3|ext4)$'
        }.iteritems():
            validate_env(key, regex)

        if 0 < os.environ['STORAGE_VOLCOUNT']:
            if 'ec2' == os.environ['RS_CLOUD_PROVIDER']:
                ec2_mount()
            else:
                google_mount()

    else:
        print("   *** System is already Nextdoor volumized! ***   ")


def main():
    """
    The Fun Starts Here.
    """
    detect_debug_mode()
    install_dependencies()
    mount_volumes()

if "__main__" == __name__:
    main()
