#! /usr/bin/sudo /usr/bin/python

# ---
# RightScript Name: nextdoor::elb-disconnect
# Description:
# Packages:
# ...
#

from os import environ
from tempfile import NamedTemporaryFile
from string import Template

import lib.python.utils as utils


#
#
#
def elb_disconnect():
    dmc = '^.+$'  # don't much care

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
            utils.validate_env(key, validation)

        # install disposable Kingpin
        utils.assert_command(
            'mkdir -p /tmp/kingpin', 'Failed to create directory for temporary Kingpin script!')
        utils.assert_command('unzip -o -u ./lib/kingpin/kingpin.zip -d /tmp/kingpin',
                             'Failed to unpack temporary Kingpin instance!')

        # create and execute the Kingpin script for ELB reg
        try:
            template_file = './lib/kingpin/templates/elb-disconnect.json.template'
            with NamedTemporaryFile() as kp_script:
                kp_script.write(
                    Template(open(template_file).read()).safe_substitute(environ))
                kp_script.flush()
                kp_script.seek(0)
                utils.log_and_stdout(
                    "   *** Kingpin ELB disconnect script : \n{}".format(kp_script.read()))
                environ['SKIP_DRY'] = "1"
                utils.assert_command(
                    "python /tmp/kingpin {}".format(kp_script.name), "Failed during Kingpin run!")

        except (IOError, KeyError), e:
            errno = -1
            if 'IOError' == type(e):
                errno = e.errno
                message = e.strerror
                utils.log_and_stdout(
                    "   *** Failed when creating Kingpin script! ***\{}\nerr: {}".format(message, errno))

        utils.assert_command('rm -rf /tmp/kingpin',
                             'Failed to remove temporary Kingpin instance!')

    else:
        utils.log_and_stdout(
            '   *** No ELB_NAME specified and thus no ELB membership. This is not an error! ***   ')

#
#
#


def main():
    utils.detect_debug_mode()
    elb_disconnect()


#
#
#
if '__main__' == __name__:
    main()
