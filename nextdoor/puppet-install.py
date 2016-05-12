#! /usr/bin/sudo /usr/bin/python3

# ---
# RightScript Name: nextdoor::puppet-install
# Description:
# Parameters:
#   - DEBUG
#   - PUPPET_AGENT_USE_CACHED_CATALOG
#   - PUPPET_AGENT_VERSION
#   - PUPPET_CUSTOM_FACTS
#   - PUPPET_NODE
#   - PUPPET_NODE_NAME
#   - PUPPET_ENABLE_REPORTS
#   - PUPPET_NODE_NAME_FACT
#   - PUPPET_CHALLENGE_PASSWORD
#   - PUPPET_CA_SERVER
#   - PUPPET_SERVER_HOSTNAME
#   - PUPPET_ENVIRONMENT_NAME
#

import os
import sys
import string
import random
from os import environ
from socket import getfqdn

from lib.python.utils import detect_debug_mode, assert_command, validate_env
from lib.python.utils import mkdir_p
from lib.python.utils import log_and_stdout, apt_get_update

# Oh my oh my...this is so nasty. Better way/place to handle this?
apt_get_update()
assert_command("apt-get install -y python3-pip",
               "Failed to install Python3 pip!")
assert_command("pip3 install PyYAML==3.11", "Failed to install PyYAML!")
import yaml


def install_dependencies():
    """
    Install some tooling which may be needed to bootstrap Puppet.
    """
    debs = 'wget'
    blacklist_debs = 'puppet'

    environ['DEBIAN_FRONTEND'] = 'noninteractive'
    environ['DEBCONF_INTERACTIVE_SEEN'] = 'true'

    apt_get_update()
    assert_command('apt-get install -y ' + debs,
                   'Unable to install required .debs!')
    assert_command('apt-get remove --purge -y ' + blacklist_debs,
                   'Unable to uninstall blacklisted .debs!')


def configure_puppet_external_facts():
    """
    Create external Facts from misc RightInputs.
    """

    if 'PUPPET_CUSTOM_FACTS' in environ:
        # take the envvar apart and reconstitute as dict
        validate_env('PUPPET_CUSTOM_FACTS', '^\w+=.+(,\w+=.+)*$')
        fact_dict = {}
        facts = environ['PUPPET_CUSTOM_FACTS'].split(',')
        for fact in facts:
            log_and_stdout("fact: {}".format(str(fact)))
            (key, value) = fact.split('=', 1)
            fact_dict[key] = value

        # construct some YAML and dump it into external fact file
        try:
            mkdir_p('/etc/facter/facts.d')
            with open('/etc/facter/facts.d/nextdoor_misc_rightscale_inputs.yaml', 'w') as outfile:
                outfile.write(
                    yaml.dump(fact_dict, explicit_start=True, default_flow_style=False))
        except IOError as e:
            sys.exit("   *** {} :: {} :: {} ***   ".format(e.errno,
                                                           e.filename, e.strerror))


def bootstrap_puppet_agent_config():
    """
    Adjust various settings in puppet.conf and create an external Facts file
    for Puppet-specific stuff.
    """
    dmc = '^.+$'

    for key, regex in {
        'PUPPET_ENVIRONMENT_NAME': dmc,
        'PUPPET_SERVER_HOSTNAME': dmc,
        'PUPPET_CA_SERVER': dmc,
        'PUPPET_ENABLE_REPORTS': '^(true|false)$',
        'PUPPET_NODE_NAME': '^(cert|facter)$',
        'PUPPET_NODE_NAME_FACT': dmc
    }.items():
        validate_env(key, regex)

    #
    # The logic around how a node is identified based on:
    #
    #  * puppet_node_name
    #  * puppet_node_name_fact
    #  * puppet_node_name_value
    #
    # is fairly ridiculous. I think the easiest way to document
    # the madness which follows is to draw a table.
    #
    # Those familiar with paleo-Puppet node classification techniques will
    # note that the above variables are just puppet.conf settings prefixed
    # with 'puppet_'.
    #
    # | puppet_node_name | puppet_node_name_fact | puppet_node_name_value |
    # |-------------------------------------------------------------------|
    # | cert             |  $ facter hostname    |     not referenced     |
    # |-------------------------------------------------------------------|
    # | facter           |    if 'puppet_node'   |  ^.+$ aka not nuthin'  |
    # |                  |------------------------------------------------|
    # |                  |   if ! 'puppet_node'  |     not referenced     |
    # ---------------------------------------------------------------------
    #

    puppet_node_name = environ['PUPPET_NODE_NAME']
    puppet_node_name_fact = environ['PUPPET_NODE_NAME_FACT']
    puppet_node_name_value = ''

    log_and_stdout(
        "Puppet node name resolution:: puppet_node_name: {}".format(puppet_node_name))

    if 'cert' == puppet_node_name:

        if 'hostname' != puppet_node_name_fact:
            log_and_stdout(
                "{} => {} forced to {} => {}".format(
                    'node_name_fact', puppet_node_name,
                    'node_name_fact', 'hostname'))
            puppet_node_name_fact = 'hostname'

    if 'facter' == puppet_node_name:

        if 'puppet_node' == puppet_node_name_fact:
            validate_env('PUPPET_NODE_NAME_VALUE', dmc)
            puppet_node_name_value = environ['PUPPET_NODE_NAME_VALUE']
            log_and_stdout(
                "puppet_node => {}".format(puppet_node_name_value))

        else:
            if '' != puppet_node_name_value:
                log_and_stdout(
                    "Ignoring PUPPET_NODE_NAME_VALUE because PUPPET_NAME_FACT != 'puppet_node'")

    #
    # If all of the validations and fiddling about with puppet_node has
    # worked out then let's update the puppet.conf and some external facts.
    #

    # puppet.conf settings
    puppet_settings = {
        'environment': environ['PUPPET_ENVIRONMENT_NAME'],
        'server': environ['PUPPET_SERVER_HOSTNAME'],
        'ca_server': environ['PUPPET_CA_SERVER'],
        'report': environ['PUPPET_ENABLE_REPORTS'],
        'node_name': puppet_node_name,
        'node_name_fact': puppet_node_name_fact,
    }

    external_facts = {
        'puppet_environment': environ['PUPPET_ENVIRONMENT_NAME'],
        'puppet_server': environ['PUPPET_SERVER_HOSTNAME'],
        'puppet_ca_server': environ['PUPPET_CA_SERVER'],
    }

    if 'cert' == puppet_node_name:
        pass  # just here for completeness and transparency

    elif 'facter' == puppet_node_name:
        if 'puppet_node' == puppet_node_name_fact:
            # This could live in puppet.conf as node_name_value but this
            # makes it visible via 'facter puppet_node'.
            external_facts['puppet_node'] = "{}|{}".format(
                puppet_node_name_value, getfqdn())
        else:
            pass  # this here for completeness and transparency

    for setting, value in puppet_settings.items():
        assert_command(
            '/usr/bin/puppet config set {} {} --section agent'.format(
                setting, value),
            'Failed to set \'{}\' to \'{}\' in puppet.conf!'.format(setting, value))

    # Drop some external Facts for Puppet settings
    try:
        mkdir_p('/etc/facter/facts.d')
        with open('/etc/facter/facts.d/nextdoor_puppet.yaml', 'w') as outfile:
            outfile.write(
                yaml.dump(external_facts,
                          explicit_start=True,
                          default_flow_style=False))
    except IOError as e:
        sys.exit("   *** {} :: {} :: {} ***   ".format(
            e.errno,
            e.filename,
            e.strerr))


def install_puppet_agent():
    """
    Install the Puppet agent repo and packages.
    """

    validate_env('PUPPET_AGENT_VERSION', '^([\w\.\-]+|PC\d+)$')
    puppet_version = environ['PUPPET_AGENT_VERSION'].lower()
    puppet_repo_package = 'puppetlabs-release-trusty.deb'
    puppet_repo_package_url = 'https://apt.puppetlabs.com/' + puppet_repo_package

    assert_command("wget -c {}".format(puppet_repo_package_url),
                   'Failed to fetch Puppet repo package!', cwd='/tmp')
    assert_command("dpkg -i {}".format(puppet_repo_package),
                   'Failed to install Puppet repo package!', cwd='/tmp')
    assert_command('apt-get update', 'Failed to update APT package cache!')
    assert_command("apt-get install -y puppet-common={} puppet={}".format(
        puppet_version, puppet_version), 'Failed to install Puppet!')


def puppet_agent_bootstrapped():
    """
    Predicate to detect if Puppet has already been installed.

    Returns: boolean True or False
    """
    classification_data = '/var/lib/puppet/state/catalog.txt'

    # classes.txt only gets dropped on a successful Puppet run.
    if (os.path.exists(classification_data)):
        return True
    else:
        return False


def create_rightscale_puppet_tags(secret):
    """
    Create the RightScale tags used for Puppet master auto-signing.
    """
    validate_env('RS_SELF_HREF', '^.+$')

    for tag in ['nd:puppet_state=waiting', "nd:puppet_secret={}".format(secret)]:
        cmd = "rsc --rl10 cm15 multi_add /api/tags/multi_add resource_hrefs[]={} tags[]={}".format(
            environ['RS_SELF_HREF'], tag)
        assert_command(
            cmd, "Failed to register RightScale tag \'{}\' for Puppet policy-base signing!".format(tag))


def create_puppet_agent_cert():
    """
    Embed Nextdoor information into the Puppet agent CSR/cert.
    """
    challenge_password = False
    preshared_key = ''.join(random.choice(
        string.ascii_letters + string.digits) for _ in range(36))

    if "PUPPET_CHALLENGE_PASSWORD" in environ:
        validate_env('PUPPET_CHALLENGE_PASSWORD', '^.+$')
        challenge_password = environ['PUPPET_CHALLENGE_PASSWORD']

    csr_attrs = {'extension_requests': {'pp_preshared_key': preshared_key}}

    if challenge_password:
        csr_attrs['custom_attributes'] = {
            '1.2.840.113549.1.9.7': challenge_password}

    try:
        with open('/etc/puppet/csr_attributes.yaml', 'wb') as outfile:
            outfile.write(
                yaml.dump(csr_attrs, explicit_start=True,
                          default_flow_style=False, encoding='utf-8'))
        os.chmod('/etc/puppet/csr_attributes.yaml', 0o644)

    except (IOError, OSError) as e:
        sys.exit("   *** {} :: {} :: {} ***   ".format(e.errno,
                                                       e.filename, e.strerror))

    create_rightscale_puppet_tags(preshared_key)


def run_puppet_agent():
    """
    Kick off a Puppet agent run. With retries to cover eventual convergence.
    """

    cmd = "/usr/bin/puppet agent -t --detailed-exitcodes --waitforcert 15"

    # These are likely set in puppet.conf before the Puppet agent run however
    # its entirely possible that a run will change the contents of puppet.conf
    # but not represent a complete convergence. On follow-up runs we thus cannot
    # rely on the values specified in puppet.conf. FIXME: make sure all node profiles
    # converge on first run. ;)

    dmc = '^.+$'  # don't much care

    for key, value in {
        'PUPPET_ENVIRONMENT_NAME': 'environment',
        'PUPPET_SERVER_HOSTNAME': 'server',
        'PUPPET_CA_SERVER': 'ca_server',
        'PUPPET_AGENT_USE_CACHED_CATALOG': 'use_cached_catalog',
    }.items():
        if key in environ:
            validate_env(key, dmc)
            cmd = ''.join((cmd, " --{} {}".format(value, environ[key])))

    assert_command(cmd, 'Puppet run failed!', retries=5)


def configure_puppet_agent():
    """
    Encode various settings in puppet.conf and setup Nextdoor external Facts.
    """
    configure_puppet_external_facts()
    bootstrap_puppet_agent_config()


def main():
    """
    The Fun Starts Here.
    """
    detect_debug_mode()
    if not puppet_agent_bootstrapped():
        install_dependencies()
        install_puppet_agent()
        configure_puppet_agent()
        create_puppet_agent_cert()
        run_puppet_agent()
    else:
        log_and_stdout(
            "   *** Puppet probably bootstrapped previously. Exiting... ***   ")


if '__main__' == __name__:
    main()
