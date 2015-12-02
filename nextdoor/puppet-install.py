#! /usr/bin/sudo /usr/bin/python

# ---
# RightScript Name: nextdoor::puppet-install
# Description: 
# Packages: 
# ...
# 

import os, sys, yaml, string, random
from os import environ

sys.path.append('./lib/python')
from utils import detect_debug_mode, assert_command, validate_env, mkdir_p, normalize_hostname_to_rfc
from utils import log_and_stdout



#
#
#
def install_dependencies():
        debs = 'wget'
        blacklist_debs = 'puppet'
                
        environ['DEBIAN_FRONTEND'] = 'noninteractive'
        environ['DEBCONF_INTERACTIVE_SEEN'] = 'true'

        assert_command('apt-get update', 'Unable to update APT cache!')
        assert_command('apt-get install -y ' + debs, 'Unable to install required .debs!')
        assert_command('apt-get remove --purge -y ' + blacklist_debs, 'Unable to uninstall blacklisted .debs!')


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
                        mkdir_p('/etc/puppet/facter/facts.d')
                        with open('/etc/puppet/facter/facts.d/nextdoor_from_rightscale_input.yaml', 'w') as outfile:
                                outfile.write(yaml.dump(fact_dict, explicit_start=True, default_flow_style=False))
                except IOError, e:
                        sys.exit("   *** {} :: {} :: {} ***   ".format(e.errno, e.filename, e.strerror))


#
#
#
def resolve_puppet_node_name():

        validate_env('PUPPET_NODE_NAME', '^(facter|cert)$')
        validate_env('PUPPET_NODE_NAME_FACT', '^.+$')
        puppet_node_name = environ['PUPPET_NODE_NAME']
        puppet_node_name_fact = environ['PUPPET_NODE_NAME_FACT']
        puppet_node = ''

        # if we want the node name to come from PUPPET_NODE value...
        if 'facter' == puppet_node_name and \
           'puppet_node' == puppet_node_name:
                validate_env('PUPPET_NODE', '^.+$')
                puppet_node = normalize_hostname_to_rfc(environ['PUPPET_NODE'])

        # otherwise we'll let the defaults in metadata.rb handle it
        
        return puppet_node              


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

        external_facts = {
                        'environment': environ['PUPPET_ENVIRONMENT_NAME'],
                        'node_name_fact': environ['PUPPET_NODE_NAME_FACT'],
                        'server': environ['PUPPET_SERVER_HOSTNAME'],
                        'ca_server': environ['PUPPET_CA_SERVER'],
                        'report': environ['PUPPET_ENABLE_REPORTS']
        }
                 
        puppet_node_name = resolve_puppet_node_name()
        if '' != puppet_node_name:
                external_facts = external_facts.update( { 'node': puppet_node } )

        for setting, value in external_facts.iteritems():
                assert_command('/usr/bin/puppet config set {} {} --section agent'.format(setting, value),
                               'Failed to set \'{}\' to \'{}\' in puppet.conf!'.format(setting, value))
                
        
#
#
#
def install_puppet_agent():

        validate_env('PUPPET_AGENT_VERSION', '^([\w\.\-]+|PC\d+)$')
        puppet_version = environ['PUPPET_AGENT_VERSION'].lower()
        puppet_repo_package = 'puppetlabs-release-trusty.deb'
        puppet_repo_package_url = 'https://apt.puppetlabs.com/' + puppet_repo_package

        assert_command("wget -c {}".format(puppet_repo_package_url), 'Failed to fetch Puppet repo package!', cwd='/tmp')
        assert_command("dpkg -i {}".format(puppet_repo_package), 'Failed to install Puppet repo package!', cwd='/tmp')
        assert_command('apt-get update', 'Failed to update APT package cache!')
        assert_command("apt-get install -y puppet-common={} puppet={}".format(puppet_version, puppet_version), 'Failed to install Puppet!')


#
#
#
def puppet_bootstrapped():
        classification_data = '/var/lib/puppet/state/catalog.txt'

        # classes.txt only gets dropped on a successful Puppet run.
        if ( os.path.exists('/var/lib/puppet/state/classes.txt') ):
                return True
        else:
                return False


#
#
#
def create_rightscale_puppet_tags(secret):
        validate_env('RS_SELF_HREF', '^.+$')

        for tag in ['nd:puppet_state=waiting', "nd:puppet_secret={}".format(secret)]:
                cmd = "rsc --rl10 cm15 multi_add /api/tags/multi_add resource_hrefs[]={} tags[]={}".format(environ['RS_SELF_HREF'], tag)
                assert_command(cmd, "Failed to register RightScale tag \'{}\' for Puppet policy-base signing!".format(tag))


#
#
#
def create_puppet_agent_cert():
        challenge_password = False
        preshared_key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(36))
        
        if "PUPPET_CHALLENGE_PASSWORD" in environ:
                validate_env('PUPPET_CHALLENGE_PASSWORD', '^.+$')
                challenge_password = environ['PUPPET_CHALLENGE_PASSWORD']

        csr_attrs = { 'extension_requests' : { 'pp_preshared_key': preshared_key } }

        if challenge_password:
                csr_attrs['custom_attributes'] = { '1.2.840.113549.1.9.7' : challenge_password }

        try:
                with open('/etc/puppet/csr_attributes.yaml', 'wb') as outfile:
                        outfile.write(yaml.dump(csr_attrs, explicit_start=True, default_flow_style=False))
                os.chmod('/etc/puppet/csr_attributes.yaml', 0644)
                
                
        except (IOError, OSError) as e:
                sys.exit("   *** {} :: {} :: {} ***   ".format(e.errno, e.filename, e.strerror))

        create_rightscale_puppet_tags(preshared_key)


#
#
#
def run_puppet_agent():

        cmd = "/usr/bin/puppet agent -t --detailed-exitcodes --waitforcert 15"
        
        # These are likely set in puppet.conf before the Puppet agent run however
        # its entirely possible that a run will change the contents of puppet.conf
        # but not represent a complete convergence. On follow-up runs we thus cannot
        # rely on the values specified in puppet.conf. FIXME: make sure all node profiles
        # converge on first run. ;)
        
        dmc = '^.+$' # don't much care
        
        for key, value in {
                        'PUPPET_ENVIRONMENT_NAME': 'environment',
                        'PUPPET_SERVER_HOSTNAME': 'server',
                        'PUPPET_CA_SERVER': 'ca_server',
        }.iteritems():
                if key in environ:
                        validate_env(key, dmc)
                        cmd = ''.join((cmd, " --{} {}".format(value, environ[key])))

        assert_command(cmd, 'Puppet run failed!', retries=5)


#
#
#
def main():
    detect_debug_mode()
    if not puppet_bootstrapped():
            install_dependencies()
            install_puppet_agent()
            configure_puppet_external_facts()
            bootstrap_puppet_config()
            create_puppet_agent_cert()
            run_puppet_agent()
    else:
            log_and_stdout("   *** Puppet probably bootstrapped previously. Exiting... ***   ")

    
#
#
#
if '__main__' == __name__:
    main()
