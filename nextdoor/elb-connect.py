#! /usr/bin/sudo /usr/bin/python

# ---
# RightScript Name: nextdoor::elb-connect
# Description: 
# Packages: 
# ...
#

import os
from os import environ
from tempfile import NamedTemporaryFile
from string import Template

sys.path.append('./lib/python')
from utils import detect_debug_mode, assert_command, validate_env, mkdir_p
from utils import log_and_stdout


#
#
#
def elb_connect():
    dmc = '^.+$' # don't much care

    if 'ELB_NAME' in environ:
        # FIXME: What are the validations for these things?
        for key, validation in {
                'ELB_NAME': dmc,
                'AWS_ACCESS_KEY_ID': dmc,
                'AWS_SECRET_ACCESS_KEY': dmc,
                'EC2_PLACEMENT_AVAILABILITY_ZONE': dmc,
                'EC2_INSTANCE_ID': dmc,
                'HOME': dmc,
        }.iteritems():
            validate_env(key, validation)

            
        try:
            template_file = './lib/kingpin/templates/elb-connect.json.template'
            with NamedTemporaryFile as kp_script:
                kp_script.write(Template(open(template_file).read()).safe_substitute(environ))
                kp_script.flush()
                kp_script.seek(0)
                log_and_stdout("   *** Kingpin ELB connect script : \n{}".format(kp_script.read()))
            
        except (IOError, KeyError), e:
            errno = -1
            if 'IOError' == type(e):
                errno = e.errno
            log_and_stdout("   *** Failed when creating Kingpin script! ***\{}\nerr: {}".format(message, errno))

#
#
#
def main():
    detect_debug_mode()
    elb_connect()
    

#
#
#
if '__main__' == __name__:
    main()
