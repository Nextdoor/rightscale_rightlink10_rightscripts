#! /usr/bin/sudo /usr/bin/python

# ---
# RightScript Name: hostname
# Description:
# Packages:
# ...
#

import sys
import os
import re

import lib.python.utils as utils


#
#
#
def normalize_hostname(myservername, myinstanceid):
    myinstanceid = re.sub('[-]+', '', myinstanceid)
    return re.sub('\.', '', utils.normalize_hostname_to_rfc("{}-{}".format(myservername, myinstanceid)))

#
#
#


def set_hostname_w_fqdn():
    for key, regex in {
            'SERVER_NAME': '^.+$',
            'INSTANCE_ID': '^.+$',
            'DEFAULT_DOMAIN': '^.+\.nextdoor\.com'
    }.iteritems():
        utils.validate_env(key, regex)

    myhostname = normalize_hostname(
        os.environ['SERVER_NAME'],
        os.environ['INSTANCE_ID']
    )

    mydomain = normalize_domain(os.environ['DEFAULT_DOMAIN'])

    # Because RightScale appears to eat stdout. :\
#    utils.assert_command("echo {}.{} > /etc/hostname".format(myhostname, mydomain), "Could not modify /etc/hostname!")
    utils.assert_command("augtool set /files/etc/hostname/hostname {}.{}".format(
        myhostname, mydomain), "Could not modify /etc/hostname!")
    utils.assert_command("hostname -F /etc/hostname",
                         "Failed when executing 'hostname' command!")


#
#
#
def normalize_domain(mydomain):
    return utils.normalize_hostname_to_rfc(mydomain)


#
#
#


def install_dependencies():
    utils.assert_command('apt-get install -y augeas-tools',
                         'Failed to install Augeas!')


#
#
#


def main():
    utils.detect_debug_mode()
    utils.validate_env('RS_CLOUD_PROVIDER', '^(ec2|google)$')
    if not 'ec2' == os.environ['RS_CLOUD_PROVIDER']:
        sys.exit("RS_CLOUD_PROVIDER=\'{}\' not supported!".format(
            os.environ['RS_CLOUD_PROVIDER']))
    else:
        install_dependencies()
        set_hostname_w_fqdn()


if '__main__' == __name__:
    main()
