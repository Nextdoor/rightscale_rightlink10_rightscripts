# multi_validate_re

Provides a function, multi_validate_re(), which wraps puppetlabs/stdlib's
validate_re to allow passing of multiple arguments for matching against a regex. 

The primary motivation for development of this function is as a work-around
to the bug in Puppet < 4.x which prevents puppetlabs/stdlib's validate_string
from throwing a Puppet::ParseError when it encounters an undef.

# Example usage

This fails to catch the undef supplied as a class parameter:
```puppet
class foo( $bar ) { validate_string($bar) }
class { 'foo': bar => undef, }
```

This allows the caller to catch undef in multiple class parameters in a single
function call:
```puppet
class foo ( $bar, $baz ) { multi_validate_re($bar, $baz, '^.+$') }
class { 'foo': bar => 'hola!', baz => undef, }
```

## License

Apache License, Version 2.0

## Contact

Nathan Valentine - nrvale0@gmail.com|nathan@puppetlabs.com

## Support

Please log tickets and issues at the project's site.
