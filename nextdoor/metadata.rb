name        "nextdoor"
maintainer  "Nextdoor.com"
license     "see LICENSE file in repository root"
description "Base scripts for Nextdoor.com on Linux (RLL) to initialize basic functionality"
version     '0.1.0'

recipe      "nextdoor::dump-env", "Print environment variables for debugging purposes"
recipe      "nextdoor::mounts", "Configure /mnt"
recipe      "nextdoor::hostname", "Configure hostname + domain"
recipe      "nextdoor::puppet-install", "Install the Puppet agent"
recipe      "nextdoor::elb-connect", "Register to an ELB"
recipe      "nextdoor::elb-disconnect", "Deregister to an ELB"

attribute "RS_CLOUD_PROVIDER",
          :category => "CLOUD",
          :display_name => "RS_CLOUD_PROVIDER",
          :description => "In what cloud context are we running? <ec2|google>",
          :required => "optional",
          :type => "string",
          :choice => ['ec2', 'google'],
          :default => "ec2",
          :recipes => ['nextdoor::mounts', 'nextdoor::hostname']

attribute "STORAGE_RAID_LEVEL",
          :category => "STORAGE",
          :display_name => "STORAGE_RAID_LEVEL",
          :description => "RAID level to use (0, 1, 5 or 10)",
          :required => "optional",
          :type => "string",
          :default => "0",
          :choice => ['0', '1', '5', '10'],
          :recipes => ['nextdoor::mounts']

attribute "STORAGE_FSTYPE",
          :category => "STORAGE",
          :display_name => "STORAGE_FSTYPE",
          :description => "filesystem format for /mnt",
          :required => "optional",
          :type => "string",
          :choice => ['ext3', 'ext4', 'xfs'],
          :default => "xfs",
          :recipes => ['nextdoor::mounts']

attribute "STORAGE_VOLCOUNT",
          :category => "STORAGE",
          :display_name => "STORAGE_VOLCOUNT",
          :description => "IF STORAGE_TYPE == EBS: The number of volumes to create within EC2 and join to the RAID array.",
          :required => "optional",
          :type => "string",
          :default => "0",
          :choice => ['0', '4', '6', '8'],
          :recipes => ['nextdoor::mounts']

attribute "AWS_ACCESS_KEY_ID",
          :category => "CLOUD",
          :display_name => "AWS_ACCESS_KEY_ID",
          :description => ";)",
          :required => "required",
          :type => "string",
          :recipes => ['nextdoor::mounts', 'nextdoor::elb-connect', 'nextdoor::elb-disconnect']

attribute "AWS_SECRET_ACCESS_KEY",
          :category => "CLOUD",
          :display_name => "AWS_SECRET_ACCESS_KEY",
          :description => ";)",
          :required => "required",
          :type => "string",
          :recipes => ['nextdoor::mounts', 'nextdoor::elb-connect', 'nextdoor::elb-disconnect']

attribute "STORAGE_TYPE",
          :category => "STORAGE",
          :display_name => "STORAGE_TYPE",
          :description => "If storage type is 'instance', local normal storage is used. If type is 'ebs', a whole new set of EBS volumes will be created. If 'remount_ebs', we will re-mount EBS volumes supplied in the STORAGE_VOLIDLIST",
          :required => "optional",
          :type => "string",
          :default => "instance",
          :choice => ['instance', 'ebs', 'remount-ebs'],
          :recipes => ['nextdoor::mounts']

attribute "EBS_TYPE",
          :category => "STORAGE",
          :display_name => "EBS_TYPE",
          :description => "gp2 for General Purpose (SSD) volumes, io1 for Provisioned IOPS (SSD) volumes, or standard for Magnetic volumes. If you choose io1, you'll get 4000 IOPS.",
          :required => "optional",
          :type => "string",
          :default => "standard",
          :choice => ['standard', 'gp2', 'io1'],
          :recipes => ['nextdoor::mounts']

attribute "STORAGE_VOLIDLIST",
          :category => "STORAGE",
          :display_name => "STORAGE_VOLIDLIST",
          :description => "IF STORAGE_TYPE == remounte_ebs: Comma separated list of EBS Volume IDS to try to mount on boot up and re-join together as a RAID volume. This is used for recovery only.
",
          :required => "optional",
          :type => "array",
          :recipes => ['nextdoor::mounts']

attribute "STORAGE_SIZE",
          :category => "STORAGE",
          :display_name => "STORAGE_SIZE",
          :description => "IF STORAGE_TYPE == EBS: This is the total size of the array to create. (in GB)",
          :required => "optional",
          :type => "string",
          :default => "512",
          :choice => ['512', '1024', '2048'],
          :recipes => ['nextdoor::mounts']

attribute "STORAGE_MOUNTPOINT",
          :category => "STORAGE",
          :display_name => "STORAGE_MOUNTPOINT",
          :description => "Where is the mount volume created?",
          :required => "optional",
          :type => "string",
          :default => "/mnt",
          :recipes => ['nextdoor::mounts']
          
attribute "DEBUG",
          :category => "NEXTDOOR",
          :display_name => "DEBUG",
          :description => "** WARNING - debug mode may expose secrets!!! **",
          :require => "optional",
          :type => "string",
          :recipes => ['nextdoor::dump-env', 'nextdoor::mounts', 'nextdoor::hostname', 'nextdoor::puppet-install']

attribute "DEFAULT_DOMAIN",
          :category => "NEXTDOOR: HOSTNAME SETTINGS",
          :display_name => "DEFAULT_DOMAIN",
          :description => "Domain name to attach to the hostname (ie, mycompany.com)",
          :require => "optional",
          :default => "cloud.nextdoor.com",
          :type => "string",
          :recipes => ['nextdoor::dump-env', 'nextdoor::hostname']

attribute "INSTANCE_ID",
          :category => "NEXTDOOR: HOSTNAME SETTINGS",
          :display_name => "INSTANCE_ID",
          :description => "Cloud specific Instance ID (ie, i-12341234)",
          :require => "optional",
          :type => "string",
          :recipes => ['nextdoor::dump-env', 'nextdoor::hostname', 'nextdoor::elb-connect', 'nextdoor::elb-disconnect']

attribute "SERVER_NAME",
          :category => "NEXTDOOR: HOSTNAME SETTINGS",
          :display_name => "SERVER_NAME",
          :description => "Human Readable Server Name (ie 'my web server 1')",
          :require => "optional",
          :type => "string",
          :recipes => ['nextdoor:dump-env', 'nextdoor::hostname']

attribute "PUPPET_AGENT_VERSION",
          :display_name => "PUPPET_AGENT_VERSION",
          :description  => "The Puppet agent version to install. ex: 'PC1', '3.8.1-1puppetlabs1'",
          :required     => "optional",
          :default      => "3.7.4-1puppetlabs1",
          :category     => "NEXTDOOR: PUPPET SETTINGS",
          :recipes      => [ "nextdoor::puppet-install"]

attribute "PUPPET_CUSTOM_FACTS",
          :display_name => "PUPPET_CUSTOM_FACTS",
          :description  =>
          "A list of key=value custom puppet facts that will be stored in /etc/facter/facts.d/nd-puppet.txt and available to Puppet as facts for your manifest compilation. eg: my_cname=foobar",
          :required     => "optional",
          :type         => "array",
          :default      => '',
          :category     => "NEXTDOOR: PUPPET SETTINGS",
          :recipes      => [ "nextdoor::puppet-install" ]

attribute "PUPPET_NODE",
          :display_name => "PUPPET_NODE",
          :description  => "If specified along with PUPPET_NODE_FACT='puppet_node', set the Puppet node name to this value.",
          :required     => "recommended",
          :category     => "NEXTDOOR: PUPPET SETTINGS",
          :recipes      => [ "nextdoor::puppet-install" ]

attribute "PUPPET_NODE_NAME",
          :display_name => "PUPPET_NODE_NAME",
          :description  => "Override Puppet node name specified in PUPPET_NODE via specified method: <cert|facter>. If 'facter', use the value returned by execution of PUPPET_NODE_FACT.",
          :default      => "facter",
          :choice       => [ "facter", "cert" ],
          :required     => "optional",
          :category     => "NEXTDOOR: PUPPET SETTINGS",
          :recipes      => [ "nextdoor::puppet-install" ]

attribute "PUPPET_ENABLE_REPORTS",
          :display_name => "PUPPET_ENABLE_REPORTS",
          :description  =>
          "Whether or not to send back Puppet Reports. Requires that your Puppet server is configured to accept reports and handle them.",
          :default      => "true",
          :choice       => [ "true", "false" ],
          :required     => "optional",
          :category     => "NEXTDOOR: PUPPET SETTINGS",
          :recipes      => [ "nextdoor::puppet-install" ]

attribute "PUPPET_NODE_NAME_FACT",
          :display_name => "PUPPET_NODE_NAME_FACT",
          :description  => "PUPPET_NODE_NAME will be generated via the specified Facter fact.",
          :required     => "optional",
          :default      => "hostname",
          :category     => "NEXTDOOR: PUPPET SETTINGS",
          :recipes      => [ "nextdoor::puppet-install" ]

attribute "PUPPET_CHALLENGE_PASSWORD",
          :display_name => "PUPPET_CHALLENGE_PASSWORD",
          :description  =>
          "Puppet 3.4+ supports the ability to pass data to the Puppet Master through the CSR itself. If this option is supplied, the csr_attributes.yml file is created and the challengePassword option is embedded into the CSR.",
          :required     => "recommended",
          :category     => "NEXTDOOR: PUPPET SETTINGS",
          :recipes      => [ "nextdoor::puppet-install" ]

attribute "PUPPET_CA_SERVER",
          :display_name => "PUPPET_CA_SERVER",
          :description  => "Puppet server to use for certificate requests.",
          :required     => "recommended",
          :default      => "puppetca.nextdoor.com",
          :category     => "NEXTDOOR: PUPPET SETTINGS",
          :recipes      => [ "nextdoor::puppet-install" ]

attribute "PUPPET_SERVER_HOSTNAME",
          :display_name => "PUPPET_SERVER_HOSTNAME",
          :description  =>
          "Puppet server to use for manifest compilation.",
          :default      => "puppet.nextdoor.com",
          :required     => "recommended",
          :category     => "NEXTDOOR: PUPPET SETTINGS",
          :recipes      => [ "nextdoor::puppet-install" ]

attribute "PUPPET_ENVIRONMENT_NAME",
          :display_name => "PUPPET_ENVIRONMENT_NAME",
          :description  => "Puppet environment to request",
          :default      => "production",
          :required     => "recommended",
          :category     => "NEXTDOOR: PUPPET SETTINGS",
          :recipes      => [ "nextdoor::puppet-install" ]

attribute "ELB_NAME",
          :category => "LOAD_BALANCER",
          :display_name => "ELB_NAME",
          :description => "The is the name of the ELB you gave in RightScale or the Amazon AWS console. Note: This is the short name and *not* the FQDN.",
          :required => "optional",
          :type => "string",
          :recipes => ['nextdoor::elb-connect', 'nextdoor::elb-disconnect']

attribute "EC2_PLACEMENT_AVAILABILITY_ZONE",
          :category => "LOAD_BALANCER",
          :display_name => "EC2_PLACEMENT_AVAILABILITY_ZONE",
          :description => "??",
          :required => "optional",
          :style => "string",
          :recipes => ['nextdoor::elb-connect', 'nextdoor::elb-disconnect']
