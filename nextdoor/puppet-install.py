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
from subprocess import call

sys.path.append('./lib')
from utils import detect_debug_mode, assert_command, validate_env


#
#
#
def install_dependencies():
        debs = 'ohai wget'
        blacklist_debs = 'puppet* facter'
        
        environ['DEBIAN_FRONTEND'] = 'noninteractive'
        environ['DEBCONF_INTERACTIVE_SEEN'] = 'true'

        assert_command('apt-get update', 'Unable to update APT cache!')
        assert_command('apt-get install -y ' + debs, 'Unable to install required .debs!')
        assert_command('apt-get remove --purge -y ' + blacklist_debs, 'Unable to uninstall blacklisted .debs!')

#
#
#
def configure_puppet():
        assert_command('ln -s /opt/puppetlabs/bin/puppet /usr/local/bin/puppet', 'Failed to create symlink to /opt/puppetlabs/bin/puppet!')
        print "FIXME: configure Puppet here!"

#
#
#
def install_puppet():

        puppet_repo_package = 'puppetlabs-release-pc1-trusty.deb'
        puppet_repo_package_url = 'https://apt.puppetlabs.com/' + puppet_repo_package

        assert_command("wget -c {}".format(puppet_repo_package_url), 'Failed to fetch Puppet repo package!')
        assert_command("dpkg -i {}".format(puppet_repo_package), 'Failed to install Puppet repo package!')
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
