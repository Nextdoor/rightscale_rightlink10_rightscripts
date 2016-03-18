guard 'remote-sync',
      :source       => 'nextdoor/',
      :cli_options  => "-vzrlptD --partial --progress ./nextdoor/ root@#{ENV['RIGHTLINK10_NODE']}:/var/spool/rightlink/cookbooks/#{ENV['RIGHTLINK10_COOKBOOKS_DIR']}/" do

  ['RIGHTLINK10_NODE', 'RIGHTLINK10_COOKBOOKS_DIR'].each do |envvar|
    raise "Failed to find \'%s\' in environment!" % envvar unless ENV.has_key?(envvar)
    raise "Please set a value for \'%s\' in environment!" % envvar unless '' != ENV['envvar']
  end 

  watch(%r{^.+\.(pp|sh|py|template)$})
  
end
