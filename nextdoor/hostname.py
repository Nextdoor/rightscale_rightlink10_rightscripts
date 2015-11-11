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

sys.path.append('./lib/python')
from utils import detect_debug_mode, assert_command, validate_env


#
#
#
def normalize_to_rfc(mystr):
    # LOL!
    # 1. lower everthing
    # 2. delete anything which is not alphanumeric
    # 3 & 4 compress multiple '.' or '-'
    # 5 strip leading '-'s
    return re.sub('^[-]+', '', re.sub('[.]{2,}', '.', re.sub('[-]{2,}', '-', re.sub('[^a-z0-9-._]', '', mystr.lower()))))
    
    

#
#
#
def normalize_hostname(myservername, myinstanceid):
    myinstanceid = re.sub('[-]+', '', myinstanceid)
    return re.sub('\.', '', normalize_to_rfc("{}-{}".format(myservername, myinstanceid)))

#
#
#
def set_hostname_w_fqdn():
    for key, regex in {
            'SERVER_NAME': '^.+$',
            'INSTANCE_ID': '^.+$',
            'DEFAULT_DOMAIN': '^.+\.nextdoor\.com'
    }.iteritems():
        validate_env(key, regex)

    myhostname = normalize_hostname(
        os.environ['SERVER_NAME'],
        os.environ['INSTANCE_ID']
    )

    mydomain = normalize_domain(os.environ['DEFAULT_DOMAIN'])

    # Because RightScale appears to eat stdout. :\
#    assert_command("echo {}.{} > /etc/hostname".format(myhostname, mydomain), "Could not modify /etc/hostname!")
    assert_command("augtool set /files/etc/hostname/hostname {}.{}".format(myhostname, mydomain), "Could not modify /etc/hostname!")
    assert_command("hostname -F /etc/hostname", "Failed when executing 'hostname' command!")


#
#
#
def normalize_domain(mydomain):
    return normalize_to_rfc(mydomain)

#
#
#
def install_dependencies():
    assert_command('apt-get install -y augeas-tools', 'Failed to install Augeas!')
    
#
#
#
def main():
    detect_debug_mode()
    validate_env('RS_CLOUD_PROVIDER', '^(ec2|google)$')
    if not 'ec2' == os.environ['RS_CLOUD_PROVIDER']:
        sys.exit("RS_CLOUD_PROVIDER=\'{}\' not supported!".format(os.environ['RS_CLOUD_PROVIDER']))
    else:
        install_dependencies()
        set_hostname_w_fqdn()

        
if '__main__' == __name__:
    main()

        
