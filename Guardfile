guard 'remote-sync',
      :ssh => true,
      :source => 'nextdoor/',
      :destination => '/var/spool/rightlink/cookbooks/09ad8999c30f9cb61d52bf714f7b9cf1/',
      :user => 'root',
      :remote_address => 'ec2-50-18-232-48.us-west-1.compute.amazonaws.com' do

  watch(%r{^.+\.(pp|sh|py)$})
  
end
