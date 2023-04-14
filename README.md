# Using Ubuntu Live-Server to automate Desktop installation

## Abstract
This document describes the procedure to perform an automated install of Ubuntu 22.04.x LTS Desktop.  This is implemented by using the Ubuntu 22.04.x LTS Server ISO, installing Desktop on top, and removing unneeded default Server packages.

## Introduction
The Ubuntu 22.04 LTS live-server ISO uses Subiquity, which means that the
Subiquity Autoinstall format is used for automation.

This document was written for, and is up to date with, Ubuntu 22.04.1.

As a quick introduction to Autoinstall, it is a YAML format where the installer
has default values for almost all of the configuration.  As such, simple
Autoinstalls can be very short, if the default configuration is acceptable.

This document covers just enough Autoinstall to get a Desktop experience.  It's
highly likely that the Autoinstall will need further configuration to meet
practical installation requirements.

All sample configuration files and scripts can be found in this git repository.

For more information on Autoinstall, please see:
* [Automated Server Installs](https://ubuntu.com/server/docs/install/autoinstall)
* [Automated Server Install Quickstart](https://ubuntu.com/server/docs/install/autoinstall-quickstart)
* [Automated Server Installs Config File Reference](https://ubuntu.com/server/docs/install/autoinstall-reference)

## Autoinstall
Below is an almost-ready-to-use autoinstall.yaml. Please adjust the `identity` section to set a password hash and confirm the desired user information.
```yaml
#cloud-config
autoinstall:
  # version is an Autoinstall required field.
  version: 1

  # This adds the default ubuntu-desktop packages to the system.
  # Any desired additional packages may also be listed here.
  packages:
    - ubuntu-desktop

  # This adds the default snaps found on a 22.04 Ubuntu Desktop system.
  # Any desired additional snaps may also be listed here.
  snaps:
    - name: firefox
    - name: gnome-3-38-2004
    - name: gtk-common-themes
    - name: snap-store
    - name: snapd-desktop-integration

  # User creation can occur in one of 3 ways:
  # 1. Create a user using this `identity` section.
  # 2. Create users as documented in cloud-init inside the user-data section,
  #    which means this single-user identity section may be removed.
  # 3. Prompt for user configuration on first boot.  Remove this identity
  #    section and see the "Installation without a default user" section.
  identity:
    realname: ''
    username: ubuntu
    # A password hash is needed. `mkpasswd --method=SHA-512` can help.
    # mkpasswd can be found in the package 'whois'
    password: '<password hash>'
    hostname: ubuntu-desktop

  # Subiquity will, by default, configure a partition layout using LVM.
  # The 'direct' layout method shown here will produce a non-LVM result.
  storage:
    layout:
      name: direct

  # Ubuntu Desktop uses the hwe flavor kernel by default.
  early-commands:
    - echo 'linux-generic-hwe-22.04' > /run/kernel-meta-package

  # The live-server ISO does not contain some of the required packages,
  # such as ubuntu-desktop or the hwe kernel (or most of their depdendencies).
  # The system being installed will need some sort of apt access.
  # proxy: http://192.168.0.1:3142

  late-commands:
    # Enable the boot splash
    - >-
      curtin in-target --
      sed -i /etc/default/grub -e
      's/GRUB_CMDLINE_LINUX_DEFAULT=".*/GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"/'
    - curtin in-target -- update-grub

    # Let NetworkManager handle network
    - rm /target/etc/netplan/00-installer-config*yaml
    - >-
      printf "network:\n  version: 2\n  renderer: NetworkManager"
      > /target/etc/netplan/01-network-manager-all.yaml

    # Remove default filesystem and related tools not used with the suggested
    # 'direct' storage layout.  These may yet be required if different
    # partitioning schemes are used.
    - >-
      curtin in-target -- apt-get remove -y
      btrfs-progs cryptsetup* lvm2 xfsprogs

    # Remove other packages present by default in Ubuntu Server but not
    # normally present in Ubuntu Desktop.
    - >-
      curtin in-target -- apt-get remove -y
      ubuntu-server ubuntu-server-minimal
      binutils byobu curl dmeventd finalrd gawk
      kpartx mdadm ncurses-term needrestart open-iscsi openssh-server
      sg3-utils ssh-import-id sssd thin-provisioning-tools vim tmux
      sosreport screen open-vm-tools motd-news-config lxd-agent-loader
      landscape-common htop git fonts-ubuntu-console ethtool

    # Keep cloud-init, as it performs some of the installation on first boot.
    - curtin in-target -- apt-get install -y cloud-init

    # Finally, remove things only installed as dependencies of other things
    # we have already removed.
    - curtin in-target -- apt-get autoremove -y

    # A postinstall script may optionally be used for further install
    # customization. Deploy this postinstall.sh script on the webserver.
    # - wget -O /target/postinstall.sh http://192.168.0.2/postinstall.sh
    # - curtin in-target -- bash /postinstall.sh
    # - rm /target/postinstall.sh

  # Additional cloud-init configuration affecting the target
  # system can be supplied underneath a user-data section inside of
  # autoinstall.
  # user-data:
  #   …
```

### Postinstall script
At the end of the sample autoinstall.yaml is an example of downloading and calling an external postinstall script.  Here is one such example script, replicating the default language pack installation found on Ubuntu Desktop.
```sh
#!/bin/sh

# Install language packs for English
apt install -y $(check-language-support -l en)
```

### Installation without a default user
It is possible to install the system without a default user. In this situation on first boot of the system, Gnome Initial Setup will start and ask to create a user, its regional settings and a few default options.

To do so, entirely remove the "identity" section from the seed file and add to the end an empty "users" entry in a user-data section as follows:
```yaml
  # This inhibits user creation, which for Desktop images means that
  # gnome-initial-setup will prompt for user creation on first boot.
  user-data:
    users: ['']
```

### Registration with Landscape
To register the installed system with Landscape, cloud-init’s [Landscape](https://cloudinit.readthedocs.io/en/latest/topics/modules.html#landscape) support can be used.  Please ensure that a user-data section is present in the autoinstall data, and supply the appropriate values.  See also [`man landscape-config`](https://manpages.ubuntu.com/manpages/jammy/en/man1/landscape-config.1.html).
```yaml
  user-data:
    landscape:
      client:
        url: "https://landscape.canonical.com/message-system"
        ping_url: "http://landscape.canonical.com/ping"
        …
```

## Netboot
The procedure for netboot is equivalent to what is documented in the ["Netbooting the live server installer"](https://discourse.ubuntu.com/t/netbooting-the-live-server-installer/14510) document. That procedure has been updated for Ubuntu 22.04.x and adjusted to deliver the Autoinstall to the install environment.

### dnsmasq
Assuming dnsmasq will be used to serve the netboot binaries:

1. `apt install dnsmasq`
2. Configure `/etc/dnsmasq.d/pxe.conf`.  Adjust as appropriate for the installation network:
```
interface=<your interface>,lo
bind-interfaces
dhcp-range=<your interface>,192.168.0.100,192.168.0.200
dhcp-boot=pxelinux.0
enable-tftp
tftp-root=/srv/tftp
```
3. Ensure that the `/srv/tftp` directory exists
`mkdir -p /srv/tftp`
4. `systemctl restart dnsmasq.service`

### Hosting the Autoinstall and the ISO
We need to host the Autoinstall YAML somewhere the netboot can get to it.  This is a good opportunity to host the ISO, which should reduce the download time for the largest component.


1. Download the [22.04.1 Live Server ISO](https://releases.ubuntu.com/22.04.1/ubuntu-22.04.1-live-server-amd64.iso)
2. Install a web server.
3. Copy the configured autoinstall.yaml and the Live Server ISO to the  appropriate directory being served by the web server.

### PXE Configuration
1. Download pxelinux.0 and put it into place:
```
wget http://archive.ubuntu.com/ubuntu/dists/focal/main/installer-amd64/current/legacy-images/netboot/pxelinux.0
mv pxelinux.0 /srv/tftp/
```

2. Mount the Live Server ISO.
```
mount ubuntu-22.04.1-live-server-amd64.iso /mnt
```

3. Copy the kernel, initrd, and ldlinux.c32 to where the dnsmasq serves tftp from:
```
cp /mnt/casper/{vmlinuz,initrd} /srv/tftp/
apt install syslinux-common
cp /usr/lib/syslinux/modules/bios/ldlinux.c32 /srv/tftp/
```

4. Create /srv/tftp/pxelinux.cfg/default as below.  Note that the APPEND and all following items should be on a single line, and that the configured URLs should point to the previous setup http server.
```
DEFAULT install
LABEL install
 KERNEL vmlinuz
 INITRD initrd
 APPEND root=/dev/ram0 ramdisk_size=1500000 ip=dhcp cloud-config-url=http://192.168.0.2/autoinstall.yaml url=http://192.168.0.2/ubuntu-22.04.1-live-server-amd64.iso autoinstall
```

# Install
At this point everything needed should be in place.  Boot the target system.  It will perform the PXE netboot, download the ISO, use the Autoinstall configuration, and finally reboot to the installed environment.
