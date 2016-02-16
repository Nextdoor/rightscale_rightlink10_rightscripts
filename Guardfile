guard 'remote-sync',
      :ssh => true,
      :source => 'nextdoor/',
      :destination => "/var/spool/rightlink/cookbooks/#{ENV['RIGHTLINK10_COOKBOOKS_DIR']}/",
      :user => 'root',
      :remote_address => ENV['RIGHTLINK10_NODE'] do

  watch(%r{^.+\.(pp|sh|py|template)$})
  
end
