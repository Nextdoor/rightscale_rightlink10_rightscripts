#! /usr/bin/sudo /usr/bin/python3

# ---
# RightScript Name: nextdoor::elb-disconnect
# Description: Disconnect the instance to specified ELB.
# Parameters:
#   - AWS_ACCESS_KEY_ID
#   - AWS_SECRET_ACCESS_KEY
#   - INSTANCE_ID
#   - ELB_NAME
#   - EC2_INSTANCE_ID
#   - EC2_PLACEMENT_AVAILABILITY_ZONE
#

import sys
from os import environ
from tempfile import NamedTemporaryFile
from string import Template

from lib.python import utils
from lib.python.utils import assert_command, apt_get_update, log_and_stdout


def elb_disconnect():
    """
    Wire the node into ELB using RightInputs as parameters.
    """

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
        }.items():
            utils.validate_env(key, validation)

        # Extract a temp copy of Kingpin into /tmp before doing the ELB reg.
        # This *should* be possible to do without extracting Kingpin from the
        # zip *EXCEPT* boto has problems referencing some templates within
        # a zip file which it does not have if the files live in the filesystem.
        apt_get_update()
        assert_command('apt-get install -y unzip', 'Failed to install unzip utility!')
        assert_command('mkdir -p /tmp/kingpin',
                       'Failed to create temporary directorty for Kingping!')
        assert_command('unzip -o -u ./lib/python/kingpin.zip -d /tmp/kingpin',
                       'Failed to unzip temporary Kingpin instance!')

        # Note: this dereferences envvars and plugs them into the JSON.
        # Kingpin can handle this dereferencing as well butI do it here for \
        # transparency in that I also validate and print the resulting template
        # when in DEBUG mode.
        try:
            template_file = './lib/templates/elb-disconnect.json.template'
            with NamedTemporaryFile() as kp_script:

                log_and_stdout(
                    "Kingpin script temporary file is {}".format(
                        kp_script.name))

                kp_template = Template(
                    open(template_file, 'r').read()).safe_substitute(environ)

                log_and_stdout("Content of Kingpin script is:\n{}".format(kp_template))

                kp_script.write(kp_template.encode('utf-8'))
                kp_script.flush()
                kp_script.seek(0)

                log_and_stdout("Kingpin script created.".format(kp_template))

                environ['SKIP_DRY'] = "1"
                cmd = "python2.7 /tmp/kingpin --debug -j {}".format(kp_script.name)
                assert_command(cmd, "Failed during Kingpin run!")

        except KeyError as e:
            log_and_stdout(str(e))
            sys.exit(-1)

        except IOError as e:
            log_and_stdout("Output: {}".format(e.strerror))
            log_and_stdout("Exit code: {}".format(e.errno))
            log_and_stdout("Failed when creating Kingpin script!")
            sys.exit(str(e.errno))

        assert_command('rm -rf /tmp/kingpin',
                       'Failed to remove temporary Kingpin instance!')

    else:
        log_and_stdout(
            '   *** No ELB_NAME specified and thus no ELB membership. This is not an error! ***   ')


def main():
    """
    All the fun starts here!
    """
    utils.detect_debug_mode()
    elb_disconnect()


if '__main__' == __name__:
    main()
