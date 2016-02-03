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

import sys
import stat
import optparse

# Defaults
VERSION = 1.0
MD_VOL = "/dev/md127"
DEFAULT_VOLTYPE = 'instance'
DEFAULT_MOUNTPOINT = '/mnt'
DEFAULT_RAIDTYPE = 0
DEFAULT_FSTYPE = 'ext4'
DEFAULT_INSTANCE_VOL_LIST = ["/dev/sdb", "/dev/sdc", "/dev/sdd", "/dev/sde"]
DEFAULT_MOUNTOPTS = 'defaults,noatime,nodiratime,nobootwait'

# First handle all of the options passed to us
usage = "usage: %prog -a instance -m <mountpoint> -f <fstype> -r <raidlevel>"

parser = optparse.OptionParser(
    usage=usage, version=VERSION, add_help_option=True)
parser.set_defaults(verbose=True)
parser.add_option("-a", "--action", dest="action",
                  help="instance/ebs/remount-ebs")
parser.add_option("-m", "--mountpoint", dest="mountpoint",
                  help="where to mount the created volume")
parser.add_option("-f", "--fstype", dest="fstype", default=DEFAULT_FSTYPE,
                  help="(instance/ebs) filesystem type to format the volume")
parser.add_option("-r", "--raidlevel", dest="raidlevel", default=DEFAULT_RAIDTYPE,
                  help="(instance/ebs) raid level to use: 0, 1")
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
        print("INFO: (%s) checking if ephemeral vol is available..." %
              (potential_volume))
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
        print("INFO: (%s) is available, adding it to our list..." %
              (potential_volume))
        valid_volumes.append(potential_volume)

    # If we have less than two drives available, exit quietly.
    if valid_volumes.__len__() < 2:
        os.system("mount -a")
        print("INFO: Less than 2 volumes found -- exiting quietly.")
        sys.exit(0)

    # Return our valid volumes
    return valid_volumes


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
    if existing_vols.__len__() > 1:
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
    elif new_vols.__len__() > 1:
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
    if os.system("fsck -y" + vol + " 2>&1; mount " + vol + " " + mountpoint + " -o " + DEFAULT_MOUNTOPTS + " 2>&1") == 0:
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


# Now, figure out what options were passed to us and run them...
if options.action == "instance":
    # Ephemeral volumes are not adjustable, they just exist. Call out
    # to a function that finds the volumes, preps them for turning into a
    # raid volume, and then passes them back to us in an array.
    vols = get_ephemeral_volumes(DEFAULT_INSTANCE_VOL_LIST)


# Now that we have our volumes, and our mountpoint, lets create our raid volume
raid_vol = create_raid_volume(vols, options.raidlevel)
if False is raid_vol:
    print "ERROR: create_raid_volume(%s, %s) failed. exiting script." % \
        (str(vols), str(options.raidlevel))
    sys.exit(1)

# Once our volume is mounted, make sure that it gets remounted on
# subsequent bootups
update_fstab(raid_vol, options.fstype, options.mountpoint)
