file { '/usr/local/bin/puppet':
  ensure => link,
  target => '/opt/puppetlabs/puppet/bin/puppet',
}

if undef == $::nextdoor_puppet_agent_bootstrapped {

  notice("Facter says this node needs a Puppet bootstrap!")

  file { '/etc/puppetlabs/facter/facts.d/nextdoor_puppet_agent_bootstrapped.yaml':
    ensure => file,
    content => "---\nnextdoor_puppet_agent_bootstrapped: true",
  }

}
