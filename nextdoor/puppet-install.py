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
        blacklist_debs = 'puppet facter hiera'
        
        environ['DEBIAN_FRONTEND'] = 'noninteractive'
        environ['DEBCONF_INTERACTIVE_SEEN'] = 'true'

        assert_command('apt-get update', 'Unable to update APT cache!')
        assert_command('apt-get install -y ' + debs, 'Unable to install required .debs!')
        assert_command('apt-get remove --purge -y ' + debs, 'Unable to uninstall blacklisted .debs!')

#
#
#
def configure_puppet():
        print "FIXME: configure Puppet here!"

#
#
#
def install_puppet():

        puppet_repo_package = 'puppetlabs-release-pc1-trusty.deb'
        puppet_repo_package_url = 'https://apt.puppetlabs.com/' + puppet_repo_package

        assert_command("cd /tmp && wget -c {}".format(puppet_repo_package_url), "Failed to fetch Puppet repo package!", shell=True)
        assert_command("cd /tmp && dpkg -i {}".format(puppet_repo_package), "Failed to install Puppet repo package!", shell=True)
        assert_command('apt-get update && apt-get -y install puppet', 'Failed to install Puppet!', shell=True)

        configure_puppet()
#
#
#
def main():
    detect_debug_mode()
    install_dependencies()
    install_puppet()

#
#
#
if "__main__" == __name__:
    main()
