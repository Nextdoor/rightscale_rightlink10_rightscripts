#! /usr/bin/sudo /usr/bin/python

# ---
# RightScript Name: nextdoor::puppet-install
# Description: 
# Packages: 
# ...
# 

import os, sys, yaml
from os import environ

sys.path.append('./lib/python')
from utils import detect_debug_mode, assert_command, validate_env, mkdir_p


#
#
#
def install_dependencies():
        debs = 'wget'
        blacklist_debs = 'puppet'
        pips = 'prettyprint'
                
        environ['DEBIAN_FRONTEND'] = 'noninteractive'
        environ['DEBCONF_INTERACTIVE_SEEN'] = 'true'

        assert_command('apt-get update', 'Unable to update APT cache!')
        assert_command('apt-get install -y ' + debs, 'Unable to install required .debs!')
        assert_command('apt-get remove --purge -y ' + blacklist_debs, 'Unable to uninstall blacklisted .debs!')
        assert_command('pip install ' + pips, 'Unable to install pip packages!')

        # now that we have PrettyPrint, let's load it
        from prettyprint import pp


#
#
#
def configure_puppet_external_facts():

        if 'PUPPET_CUSTOM_FACTS' in environ:
                # take the envvar apart and reconstitute as dict
                validate_env('PUPPET_CUSTOM_FACTS', '^\w+=.+(,\w+=.+)*$')
                fact_dict = {}
                facts = environ['PUPPET_CUSTOM_FACTS'].split(',')
                for fact in facts:
                        (key, value) = fact.split('=')
                        fact_dict[key] = value
                        
                # construct some YAML and dump it into external fact file
                try:
                        mkdir_p('/etc/puppetlabs/facter/facts.d')
                        with open('/etc/puppetlabs/facter/facts.d/nextdoor_from_rightscale_input.yaml', 'w') as outfile:
                                outfile.write(yaml.dump(fact_dict, explicit_start=True, default_flow_style=False))
                except IOError, e:
                        sys.exit("   *** {} :: {} :: {} ***   ".format(e.errno, e.filename, e.strerror))
                                

#
#
#
def bootstrap_puppet_config():
        dmc = '^.+$'
        fact_dict = {}
        for key, regex in {
                        'PUPPET_ENVIRONMENT_NAME': dmc,
                        'PUPPET_NODE_NAME_FACT': dmc,
                        'PUPPET_SERVER_HOSTNAME': dmc,
                        'PUPPET_CA_SERVER': dmc,
                        'PUPPET_ENABLE_REPORTS': '^(true|false)$',
        }.iteritems():
                validate_env(key, regex)

                
        for setting, value in {
                        'environment': environ['PUPPET_ENVIRONMENT_NAME'],
                        'node_name_fact': environ['PUPPET_NODE_NAME_FACT'],
                        'server': environ['PUPPET_SERVER_HOSTNAME'],
                        'ca_server': environ['PUPPET_CA_SERVER'],
                        'report': environ['PUPPET_ENABLE_REPORTS'],
        }.iteritems():
                assert_command('/opt/puppetlabs/puppet/bin/puppet config set {} {} --section agent'.format(setting, value),
                               'Failed to set \'{}\' to \'{}\' in puppet.conf!'.format(setting, value))
                
               
        
#
#
#
def configure_puppet():
        configure_puppet_external_facts()
        bootstrap_puppet_config()


#
#
#
def install_puppet():

        # use one of the supported Puppet Collection releases
        validate_env('PUPPET_COLLECTION_VERSION', '^PC\d+$')
        puppet_version = environ['PUPPET_COLLECTION_VERSION'].lower()
        puppet_repo_package = 'puppetlabs-release-{}-trusty.deb'.format(puppet_version)
        puppet_repo_package_url = 'https://apt.puppetlabs.com/' + puppet_repo_package

        assert_command("wget -c {}".format(puppet_repo_package_url), 'Failed to fetch Puppet repo package!', cwd='/tmp')
        assert_command("dpkg -i {}".format(puppet_repo_package), 'Failed to install Puppet repo package!', cwd='/tmp')
        assert_command('apt-get update', 'Failed to update APT package cache!')
        assert_command('apt-get install -y puppet-agent', 'Failed to install Puppet!')

        
#
#
#
def main():
    detect_debug_mode()
    install_dependencies()
    install_puppet()
    configure_puppet()

#
#
#
if "__main__" == __name__:
    main()
