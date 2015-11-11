$regex = '^.+$'

#multi_validate_re('1','2','3', $regex)
#multi_validate_re('foobar', $regex)
#multi_validate_re(undef, $regex)
#multi_validate_re('', $regex)
#multi_validate_re($regex)
#multi_validate_re({ 'foo' => 'bar' }, $regex)

class foo ( $bar, $baz ) { multi_validate_re($bar, $baz, '^.+$') }
#class { 'foo': bar => 'hola!', baz => 'vb!', }
class { 'foo': bar => 'hola!', baz => undef, }
