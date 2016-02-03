#!/usr/bin/python

# Before we do much, make sure that we have the right system tools
# installed. This is weird to do here, but this is a first-boot script
# so our requirements may not be installed.
import os
is_apt = os.system("which apt-get > /dev/null")
is_yum = os.system("which yum > /dev/null")

# Check if mdadm exists
if os.system("which mdadm > /dev/null") > 0:
    if is_apt == 0:
        os.system("apt-get install -y -f mdadm")
    if is_yum == 0:
        os.system("yum install -y mdadm")

import commands
import time
import sys
import socket
import stat
import optparse
import boto

# Defaults
VERSION = 1.0
DEFAULT_VOLTYPE = 'instance'
DEFAULT_MOUNTPOINT = '/mnt'
DEFAULT_RAIDTYPE = 0
DEFAULT_FSTYPE = 'ext4'

DEFAULT_INSTANCE_VOL_LIST = [
    "/dev/sdb", "/dev/sdc", "/dev/sdd", "/dev/sde", "/dev/xvdb",
    "/dev/xvdc", "/dev/xvdd", "/dev/xvde", "/dev/xvdba", "/dev/xvdbb",
    "/dev/xvdbc", "/dev/xvdbd", "/dev/xvdbe"
]
DEFAULT_EBS_DISK_NAMES_SD = [
    "/dev/sdf", "/dev/sdg", "/dev/sdh", "/dev/sdi", "/dev/sdj", "/dev/sdk",
    "/dev/sdl", "/dev/sdm", "/dev/sdn"
]

DEFAULT_EBS_DISK_NAMES_XVD = [
    "/dev/xvdf", "/dev/xvdg", "/dev/xvdh", "/dev/xvdj", "/dev/xvdk",
    "/dev/xvdl", "/dev/xvdm", "/dev/xvdn", "/dev/xvdba", "/dev/xvdbb",
    "/dev/xvdbc", "/dev/xvdbd", "/dev/xvdbe"
]

DEFAULT_EBS_COUNT = 4
DEFAULT_EBS_SIZE = 512
DEFAULT_MOUNTOPTS = 'defaults,noatime,nodiratime,nobootwait'

# First handle all of the options passed to us
usage = "\
usage: %prog -a instance -m <mountpoint> -f <fstype> -r <raidlevel> \n \
or \n \
usage: %prog -k <aws_key> -s <aws_secret> -a ebs -m <mountpoint> -f <fstype> -r <raidlevel> -c <vol count> -S <disksize> \n \
or \n \
usage: %prog -k <aws_key> -s <aws_secret> -a remount-ebs -m <mountpoint> -i <comma,separated,vol,id,list>"

parser = optparse.OptionParser(
    usage=usage, version=VERSION, add_help_option=True)
parser.set_defaults(verbose=True)
parser.add_option("-k", "--awskey", dest="awskey",
                  help="Amazon AWS Key")
parser.add_option("-s", "--awssecret", dest="awssecret",
                  help="Amazon AWS Secret Key")
parser.add_option("-a", "--action", dest="action",
                  help="instance/ebs/remount-ebs")
parser.add_option("-m", "--mountpoint", dest="mountpoint",
                  help="where to mount the created volume")
parser.add_option("-f", "--fstype", dest="fstype", default=DEFAULT_FSTYPE,
                  help="(instance/ebs) filesystem type to format the volume")
parser.add_option("-r", "--raidlevel", dest="raidlevel", default=DEFAULT_RAIDTYPE,
                  help="(instance/ebs) raid level to use: 0, 1")
parser.add_option("-c", "--volcount", dest="volcount", default=DEFAULT_EBS_COUNT,
                  help="(ebs) number of EBS volumes to create")
parser.add_option("-S", "--volsize", dest="volsize", default=DEFAULT_EBS_SIZE,
                  help="(ebs) total size of the EBS volume to create")
parser.add_option("-t", "--ebstype", dest="ebstype",
                  help="(ebs) type of EBS volume: standard, io1 or gp2")
parser.add_option("-i", "--ids", dest="volids",
                  help="(remount-ebs) comma separated list of existing vol-ids to mount")
(options, args) = parser.parse_args()

# Sanity check our input.
if not options.mountpoint:
    parser.error("must specify a mountpoint with -m/--mountpoint")

#### Functions go here ####


def get_ephemeral_volumes(instance_vol_list):
    """get_ephemeral_volumes() returns an array of volumes that are ready
    to be turned into an array. These volumes will be unmounted, and
    preped for use in an array. """

    # Define an array we'll pass back
    valid_volumes = []

    # Now, for every potential volume listed in the config, walk through it..
    for potential_volume in instance_vol_list:
        # Check if the volume exists...
        print("INFO: (%s) checking if ephemeral vol is available..." % (potential_volume))
        if not os.path.exists(potential_volume):
            continue
        if not stat.S_ISBLK(os.stat(potential_volume).st_mode):
            continue

        # If the volume exists, make sure its not mounted. If we cannot unmount it for some reason,
        # skip this drive
        cmd = "mount | grep '^" + potential_volume + \
            "' | awk '{print $3}' | xargs --no-run-if-empty umount -f"
        os.system(cmd)

        # We got through our checks... add this item to our array of valid
        # drives to use
        print("INFO: (%s) is available, adding it to our list..." % (potential_volume))
        valid_volumes.append(potential_volume)

    # If we have less than two drives available, exit quietly.
    if valid_volumes.__len__() < 1:
        print("INFO: Less than two ephemeral volumes detected. Punting...")
        os.system("mount -a")
        sys.exit(0)

    # Return our valid volumes
    return valid_volumes


def get_ebs_volumes(awskey, awssecret, ebs_vol_list, volcount, volsize,
                    volume_type='standard'):
    """Work with Amazon to create EBS volumes, tag them and attach them to the local host"""

    # How large will each volume be?
    individual_vol_size = int(volsize / volcount)

    # Some local instance ID info..
    zone = commands.getoutput(
        "wget -q -O - http://169.254.169.254/latest/meta-data/placement/availability-zone")
    region = zone[:-1]
    instanceid = commands.getoutput(
        "wget -q -O - http://169.254.169.254/latest/meta-data/instance-id")
    available_ebs_vol_list = []
    attached_ebs_vol_list = []

    # Open our EC2 connection
    print("INFO: Connecting to Amazon...")
    ec2 = boto.connect_ec2(aws_access_key_id=awskey,
                           aws_secret_access_key=awssecret)
    ec2 = boto.ec2.connect_to_region(
        region, aws_access_key_id=awskey, aws_secret_access_key=awssecret)

    # Make sure that the device list we got is good. If a device exists already,
    # remove it from the potential 'device targets'
    for potential_volume in ebs_vol_list:
        if os.path.exists(potential_volume):
            print "INFO: (%s) is already an attached EBS volume." % (potential_volume)
            attached_ebs_vol_list.append(potential_volume)
        else:
            print "INFO: (%s) is available as a disk target." % (potential_volume)
            available_ebs_vol_list.append(potential_volume)

    # Reverse our available_ebs_vol_list so that we can 'pop' from the
    # beginning
    available_ebs_vol_list.reverse()

    # If we have any EBS volumes already mapped, then just pass them back. Do not create new ones,
    # and do not do anything with them. This script does not support handling multiple sets of EBS
    # volumes.
    if attached_ebs_vol_list.__len__() > 0:
        print "WARNING: EBS volumes are already attached to this host. Passing them back and not touching them."
        return attached_ebs_vol_list

    # Make sure we have enough target devices available
    if volcount > available_ebs_vol_list.__len__():
        print "ERROR: Do not have enough local volume targets available to attach the drives."
        sys.exit(1)

    # For each volume..
    for i in range(0, volcount):
        print "INFO: Requesting EBS volume creation (%s gb)..." % (individual_vol_size)

        # 30:1 GB:IOP ratio, with a max of 4000
        iops = individual_vol_size * 30
        if iops > 4000:
            iops = 4000

        if volume_type == 'io1':
            print "INFO: Requesting %s provisioned IOPS..." % iops
            vol = ec2.create_volume(individual_vol_size, zone,
                                    volume_type=volume_type,
                                    iops=iops)
        else:
            vol = ec2.create_volume(individual_vol_size, zone,
                                    volume_type=volume_type)

        # Wait until the volume is 'available' before attaching
        while vol.status != u'available':
            time.sleep(1)
            print "INFO: Waiting for %s to become available..." % vol
            vol.update()

        print "INFO: Volume %s status is now: %s..." % (vol, vol.status)

        # Grab a volume off of our stack of available vols..
        dest = available_ebs_vol_list.pop()

        # Attach the volume and wait for it to fully attach
        print "INFO: (%s) Attaching EBS volume to our instance ID (%s) to %s" % (vol.id, instanceid, dest)
        try:
            vol.attach(instanceid, dest.replace('xvd', 'sd'))
        except:
            time.sleep(5)
            vol.attach(instanceid, dest.replace('xvd', 'sd'))

        while not hasattr(vol.attach_data, 'instance_id'):
            time.sleep(1)
            vol.update()
        while not str(vol.attach_data.instance_id) == instanceid \
                or True is not os.path.exists(dest):
            print "INFO: (%s) Volume attaching..." % (vol.id)
            time.sleep(1)
            vol.update()

        # SLeep a few more seconds just to make sure the OS has seen the volume
        time.sleep(1)

        # Add the volume to our list of volumes that were created
        attached_ebs_vol_list.append(dest)
        print "INFO: (%s) Volume attached!" % (vol.id)

        # Now, tag the volumes and move on
        tags = {}
        tags["Name"] = "%s:%s" % (socket.gethostname(), dest)
        print "INFO: (%s) Taggin EBS volume with these tags: %s" % (vol.id, tags)
        ec2.create_tags(str(vol.id), tags)

    # All done. Return whatever volumes were created and attached.
    return attached_ebs_vol_list


def find_ebs_volumes(awskey, awssecret, ebs_vol_list, ebs_volid_list):
    """Search Amazon for existing EBS Volume ids in our zone. If they exist,
    then mount them and return them. If they don't exist, we error out."""

    # Some local instance ID info..
    zone = commands.getoutput(
        "wget -q -O - http://169.254.169.254/latest/meta-data/placement/availability-zone")
    region = zone[:-1]
    instanceid = commands.getoutput(
        "wget -q -O - http://169.254.169.254/latest/meta-data/instance-id")
    available_ebs_vol_list = []
    attached_ebs_vol_list = []

    # Make sure that the device list we got is good. If a device exists already,
    # remove it from the potential 'device targets'
    for potential_volume in ebs_vol_list:
        if not os.path.exists(potential_volume):
            print "INFO: (%s) is available as a disk target." % (potential_volume)
            available_ebs_vol_list.append(potential_volume)

    # Reverse our available_ebs_vol_list so that we can 'pop' from the
    # beginning
    available_ebs_vol_list.reverse()

    # Make sure we have enough target devices available
    if available_ebs_vol_list <= ebs_volid_list.__len__():
        print "ERROR: Do not have enough local volume targets available to attach the drives. Erroring out."
        return False

    # Open our EC2 connection
    print "INFO: Connecting to Amazon..."
    ec2 = boto.connect_ec2(aws_access_key_id=awskey,
                           aws_secret_access_key=awssecret)
    ec2 = boto.ec2.connect_to_region(
        region, aws_access_key_id=awskey, aws_secret_access_key=awssecret)

    # For each volume..
    for ebs_volid in ebs_volid_list:
        print "INFO: (%s) Searching for EBS volume..." % (ebs_volid)
        vols = ec2.get_all_volumes(volume_ids=ebs_volid)
        vol = vols[0]

        # Check if the volume is attached. If it is, bail!
        if not str(vol.attach_data.status) == "None" \
                and not str(vol.attach_data.instance_id) == instanceid:
            print "ERROR: (%s) is attached to instance ID %s already. Exiting!" % (vol.id, vol.attach_data.instance_id)
            return False
        # If its attached, but to our host already then figure out
        # what device its attached to.
        elif not str(vol.attach_data.status) == "None" \
                and str(vol.attach_data.instance_id) == instanceid:
            print "WARNING: (%s) is already attached our instance ID at %s. Using that..." % (vol.id, vol.attach_data.device)
            dest = vol.attach_data.device
        else:
            # Grab a volume off of our stack of available vols..
            dest = available_ebs_vol_list.pop()
            # Attach the volume and wait for it to fully attach
            print "INFO: (%s) Attaching EBS volume to our instance ID (%s) to %s" % (vol.id, instanceid, dest)
            vol.attach(instanceid, dest.replace('xvd', 'sd'))
            while not hasattr(vol.attach_data, 'instance_id'):
                time.sleep(1)
                vol.update()
            while not str(vol.attach_data.instance_id) == instanceid \
                    or True is not os.path.exists(dest):
                print "INFO: (%s) Volume attaching..." % (vol.id)
                time.sleep(1)
                vol.update()
            # Sleep a few more seconds just to make sure the OS has seen the
            # volume
            time.sleep(1)

        # Check whether we are using /dev/xvd volumes or /dev/sd volumes. Amazon always returns a volume mount
        # point as '/dev/sdXXX' when sometimes its actually '/dev/xvdXXX'.
        if os.path.exists("/dev/xvda1"):
            dest = dest.replace('sd', 'xvd')
            print "INFO: (%s) Converting volume mount point to %s" % (vol.id, dest)

        # Add the volume to our list of volumes that were created
        attached_ebs_vol_list.append(dest)
        print "INFO: (%s) Volume attached!" % (vol.id)

        # Now, tag the volumes and move on
        tags = {}
        tags["Name"] = "%s-%s" % (socket.gethostname(), dest)
        print "INFO: (%s) Taggin EBS volume with these tags: %s" % (vol.id, tags)
        ec2.create_tags(str(vol.id), tags)

    # All done. Return whatever volumes were created and attached.
    return attached_ebs_vol_list


def create_raid_volume(vols, raid_type):
    """ create_raid_volume(vols) creates a mdadm raid volume from the volumes
    that are passed ot it in the 'vols' array. if the volumes already have
    an mdadm array, then we just sanity check it and move on. """

    # Check if the MD_VOL is taken or not. This script does not support a system with existing
    # md volumes, so if one exists, we exit quietly.

    # If the file exists, skip to the next one...
    if os.system("mdadm -D " + MD_VOL + " 2>&1") == 0:
        vol_list = '|'.join(vols)
        if os.system("mdadm -D " + MD_VOL + " 2>&1 | egrep '" + vol_list + "' 2>&1") == 0:
            print "WARNING: " + MD_VOL + " already exists and actually has our volumes in it, using that and passing it back."
            return MD_VOL
        else:
            print "ERROR: " + MD_VOL + " alredy exists, but does NOT have our existing volumes in it. Exiting badly."
            sys.exit(1)

    # Now, walk throu each of the volumes passed to us and figure out if they
    # are part of an array or not already.
    existing_vols = []
    new_vols = []
    for potential_volume in vols:
        if os.system("mdadm --examine " + potential_volume + " 2>&1") == 0:
            print "INFO: (%s) is already a member of an existing array... not overwriting." % \
                (potential_volume)
            existing_vols.append(potential_volume)
        else:
            print "INFO: (%s) is not a member of any existing array, so we will create a new array with it." % \
                (potential_volume)
            new_vols.append(potential_volume)

    # If we have more than 2 drives in existing_vols, assume thats correct
    if existing_vols.__len__() > 0:
        # Prep some variables
        vol_list = " ".join(existing_vols)
        cmd = "cat /proc/mdstat  | grep ^md | awk  '{print \"/dev/\"$1}' | xargs --no-run-if-empty -n 1 mdadm -S; mdadm --assemble %s %s 2>&1" % (
            MD_VOL, vol_list)
        # Run the command and return the outpu
        if os.system(cmd) == 0:
            print "INFO: (%s) assembled from vols %s" % (MD_VOL, vol_list)
        else:
            print "ERROR: (%s) failed. (%s) could not be created... skipping." % (cmd, MD_VOL)
            return False
    # If we have more than 2 drives in existing_vols, assume thats correct
    elif new_vols.__len__() > 0:
        # Prep some variables
        vol_list = " ".join(new_vols)
        cmd = "yes | mdadm --create --name=0 --force %s --level %s --raid-devices=%s %s 2>&1" %\
            (MD_VOL, str(raid_type), new_vols.__len__(), vol_list)

        # Run the command and return the outpu
        if os.system(cmd) == 0:
            print "INFO: %s created with vols %s" % (MD_VOL, vol_list)
        else:
            print "ERROR: (%s) failed. %s could not be created... skipping." % (cmd, MD_VOL)
            return False
    else:
        return False

    # Lastly, create our mdadm config file
    if os.path.exists("/etc/mdadm"):
        md_conf = "/etc/mdadm/mdadm.conf"
    else:
        md_conf = "/etc/mdadm.conf"

    # Back up the MDADM conf
    os.system("cp " + md_conf + " " + md_conf + ".bak")

    # Now format our volume
    if False is mount_raid_volume(MD_VOL, options.fstype, options.mountpoint):
        print "ERROR: mount_raid_volume(%s, %s, %s) failed. exiting script." % \
            (MD_VOL, options.fstype, options.mountpoint)
        sys.exit(1)

    # Get our UUID from the mdadm array
    # md_uuid = commands.getoutput("blkid " + MD_VOL + " | awk '{print $2}'")
    # flake8 reports this is dead code ^^

    # Grep out any old md configs form mdadm.conf
    os.system("cat " + md_conf + " | grep -v UUID > " + md_conf)
    os.system("cat " + md_conf + " | grep -v DEVICE > " + md_conf)
    os.system("mdadm --detail --scan >> " + md_conf)
    os.system("echo DEVICE " + vol_list + " >> " + md_conf)

    # Return the created/mounted md vols
    return MD_VOL


def mount_raid_volume(vol, fstype, mountpoint):
    """ prep_raid_volume(vol,fstype) checks if a volume is formatted already or not.
    if not, it formats it with the fstype requested """

    # Check if 'vol' exists
    if not stat.S_ISBLK(os.stat(vol).st_mode):
        return False

    # Make sure that the mountpoint is available and nothing else is mounted
    # there.
    cmd = "mount | grep '" + mountpoint + \
        "' | awk '{print $3}' | xargs --no-run-if-empty umount -f"
    os.system(cmd)

    # Sanity check our fstype. We may need to add options.
    if fstype == "xfs":
        fstype = "xfs -f"

    # Attempt to mount the filesystem... if it wont mount, then
    # assume its bad and try to format it.
    cmd = "(fsck -y {} 2>&1 ; mount {} {} -o {} 2>&1)".format(
        vol, vol, mountpoint, DEFAULT_MOUNTOPTS)
    if options.verbose:
        print "INFO: {}".format(cmd)
    if 0 == os.system(cmd):
        print "INFO: (%s) already has a filesystem on it... mounting." % (vol)
        return True
    else:
        # If theres no filesystem on the device, create the one we want
        print "INFO: Formatting %s with %s and mounting it to %s..." % \
            (vol, fstype, mountpoint)
        if os.system("mkfs." + fstype + " " + vol + " 2>&1; mount " + vol + " " + mountpoint + " -o " + DEFAULT_MOUNTOPTS + " 2>&1") == 0:
            return True
        else:
            return False


def update_fstab(vol, fstype, mountpoint):
    """ Now that our mount point is finished, update fstab """

    # Construct our fstab mount line
    mnt_line = "%s	%s	%s	%s	0 0\n" % (
        vol, mountpoint, fstype, DEFAULT_MOUNTOPTS)

    # Make sure that no existing mount line is in the fstab
    cmd = '/bin/sed -i \'\%s/d\' /etc/fstab' % mountpoint
    os.system(cmd)

    # Now add our line to the fstab
    with open('/etc/fstab', 'a') as f:
        f.write(mnt_line)

    return True


#### END FUNCTIONS ####

# Sanity check.. depending on our kernel, we use different volumes for
# EBS. Pick those here
if os.path.exists("/dev/sda1"):
    DEFAULT_EBS_DISK_NAMES = DEFAULT_EBS_DISK_NAMES_SD
    MD_VOL = "/dev/md0"
else:
    DEFAULT_EBS_DISK_NAMES = DEFAULT_EBS_DISK_NAMES_XVD
    MD_VOL = "/dev/md127"

# Now, figure out what options were passed to us and run them...
if options.action == "instance":
    # Ephemeral volumes are not adjustable, they just exist. Call out
    # to a function that finds the volumes, preps them for turning into a
    # raid volume, and then passes them back to us in an array.
    vols = get_ephemeral_volumes(DEFAULT_INSTANCE_VOL_LIST)
elif options.action == "ebs":
    # EBS volumes are created upon demand, mounted and raided. They will
    # be labeled appropriately so that they are easily trackable.
    if not options.awskey or not options.awssecret:
        parser.error("both awskey and awssecret must be supplied")
    vols = get_ebs_volumes(options.awskey, options.awssecret,
                           DEFAULT_EBS_DISK_NAMES, int(options.volcount),
                           int(options.volsize),
                           options.ebstype)
elif options.action == "remount-ebs":
    # In the event that EBS volumes already exist and we want to remount them
    # they can be supplied to us and we'll just search for, and mount them.
    if not options.awskey or not options.awssecret:
        parser.error("both awskey and awssecret must be supplied")
    if not options.volids:
        parser.error(
            "--volids/-i must be supplied with a comma-separated list of volume ids")
    volid_array = options.volids.split(',')
    vols = find_ebs_volumes(options.awskey, options.awssecret,
                            DEFAULT_EBS_DISK_NAMES, volid_array)

# Now that we have our volumes, and our mountpoint, lets create our raid volume
raid_vol = create_raid_volume(vols, options.raidlevel)
if False is raid_vol:
    print "ERROR: create_raid_volume(%s, %s) failed. exiting script." % \
        (str(vols), str(options.raidlevel))
    sys.exit(1)

# Once our volume is mounted, make sure that it gets remounted on
# subsequent bootups
update_fstab(raid_vol, options.fstype, options.mountpoint)
