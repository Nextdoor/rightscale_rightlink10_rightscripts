#! /usr/bin/sudo /usr/bin/python

# ---
# RightScript Name: nextdoor::puppet-install
# Description: 
# Packages: 
# ...
# 

import os
from os import environ
import sys

sys.path.append('./lib/python')
from utils import detect_debug_mode, assert_command, validate_env, mkdir_p


#
#
#
def install_dependencies():
        debs = 'ohai wget python-yaml'
        blacklist_debs = 'puppet facter'
        pips = 'prettyprint'
                
        environ['DEBIAN_FRONTEND'] = 'noninteractive'
        environ['DEBCONF_INTERACTIVE_SEEN'] = 'true'

        assert_command('apt-get update', 'Unable to update APT cache!')
        assert_command('apt-get install -y ' + debs, 'Unable to install required .debs!')
        assert_command('apt-get remove --purge -y ' + blacklist_debs, 'Unable to uninstall blacklisted .debs!')
        assert_command('pip install ' + pips, 'Unable to install pip packages!')

        import yaml
        from prettyprint import pp
        

#
#
#
def configure_puppet_external_facts():

        if 'PUPPET_CUSTOM_FACTS' in os.environ:
                # take the envvar apart and reconstitute as dict
                validate_env('PUPPET_CUSTOM_FACTS', '^\w+=\w+(,\w+=\w+)$')
                fact_dict = {}
                facts = os.environ['PUPPET_CUSTOM_FACTS'].split(',')
                for fact in facts:
                        (key, value) = fact.split('=')
                        fact_dict[key] = value
                        
                        # construct some YAML and dump it into external fact file
                        try:
                                mkdir_p('/etc/puppetlabs/facter/facts.d')
                                with open('/etc/puppetlabs/facter/facts.d', 'w') as outfile:
                                        outfile.write(yaml.dump(fact_dict))
                        except IOError, e:
                                sys.exit("   *** {} :: {} :: {} ***   ".format(e.errno, e.filename, e.strerror))
                                
                pp(fact_dict)

#
#
#
def bootstrap_puppet_config():
        bootstrap_cmd = "/opt/puppetlabs/puppet/bin/puppet apply --modulepath=./lib/puppet/modules ./lib/puppet/manifests/site.pp --debug"
        assert_command(bootstrap_cmd, 'Failed during Puppet bootstrap run!')

        
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

        puppet_repo_package = 'puppetlabs-release-pc1-trusty.deb'
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
