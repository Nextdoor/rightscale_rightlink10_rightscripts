module Puppet::Parser::Functions
  newfunction(:multi_validate_re, :doc => <<-'ENDHEREDOC') do |args|
    All that is great about validate_re but with the ability to
    validate multiple arguments in a single function call.

    The last argument to multi_validate_re() is the stringified
    regex. All preceeding arguments are strings to test.
    
    ENDHEREDOC

    if 2 > args.length then
      raise Puppet::ParseError, ("multi_validate_re() requires at least 2 args. #{args.length} args passed")
    end

    regex = args.pop
    argcount = 0
    args.each do |arg|
      argcount += 1
      Puppet::Parser::Functions.autoloader.loadall
        begin
          function_validate_re([arg, regex])
        rescue Puppet::ParseError => pe
          raise Puppet::ParseError, ("At arg #{argcount} of multi_validate_re(), #{pe.message}")
        end
    end
  end
end
