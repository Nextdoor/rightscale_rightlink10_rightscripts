file { '/usr/local/bin/puppet':
  ensure => link,
  target => '/opt/puppetlabs/puppet/bin/puppet'm
}
