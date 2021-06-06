#
#    Uncomplicated VM Builder
#    Copyright (C) 2010-2015 Canonical Ltd.
#
#    See AUTHORS for list of contributors
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 3, as
#    published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import time
from VMBuilder.plugins.ubuntu.xenial import Xenial
from   VMBuilder.util import run_cmd
import tempfile
import re
import logging

class Bionic(Xenial):

    def install_grub(self, chroot_dir, devmapfile, root_dev, kclfile):
        self.install_from_template('/etc/kernel-img.conf', 'kernelimg', { 'updategrub' : self.updategrub })
        arch = self.context.get_setting('arch')
        self.run_in_target('apt-get', '-y', 'install', 'grub2-common', 'grub-pc', env={ 'DEBIAN_FRONTEND' : 'noninteractive' })
        self.run_in_target('dpkg-reconfigure', 'grub-pc', env={ 'UCF_FORCE_CONFFMISS' : 'Yes', 'DEBIAN_FRONTEND' : 'noninteractive' })
#        run_cmd('rsync', '-a', '%s%s/%s/' % (chroot_dir, self.grubroot, arch == 'amd64' and 'x86_64-pc' or 'i386-pc'), '%s/boot/grub/' % chroot_dir)
        run_cmd('rsync', '-a', '%s%s/%s/' % (chroot_dir, self.grubroot, 'i386-pc'), '%s/boot/grub/' % chroot_dir)
        self.run_in_target('echo', '\"%s\"' % devmapfile)
        self.run_in_target('cat', '/tmp/vmbuilder-grub/device.map')
        self.run_in_target('ls', '-l', '/tmp/vmbuilder-grub/')
        self.run_in_target('echo', '\"---\"')
        self.run_in_target('echo', '\"%s\"' % root_dev)
        dfoutput=run_cmd('df')
        run_cmd('losetup', '-a')
        run_cmd('ls', '-l', '/dev/mapper/')
        for line in dfoutput.split('\n'):
            if line.endswith(chroot_dir):
                myloopdev = line.split(' ')[0]
        self.run_in_target('ls', '-l', '/dev')
        self.run_in_target('ls', '-l', '/boot')
        self.run_in_target('ls', '-l', '/etc/default')
        self.run_in_target('cat', '/etc/fstab')
        mydrv = re.search(r'loop[0-9]+',myloopdev).group()
#        run_cmd('grub-install', '--boot-directory=%s/boot' % chroot_dir, '--root-directory=%s' % chroot_dir, '/dev/%s' % mydrv)
        run_cmd('grub-install', '--boot-directory=%s/boot' % chroot_dir, '--root-directory=%s' % chroot_dir, '--target=i386-pc', '/dev/%s' % mydrv)
        run_cmd('mount', '--bind', '/dev', '%s/dev' % chroot_dir)
#        run_cmd('mount', '--bind', '/proc', '%s/proc' % chroot_dir)
#        run_cmd('mount', '--bind', '/sys', '%s/sys' % chroot_dir)
        self.run_in_target('touch', '/boot/grub/menu.lst')
	self.run_in_target('bash', '-c', 'grep -qxF \"GRUB_RECORDFAIL_TIMEOUT\" /etc/default/grub || echo \"GRUB_RECORDFAIL_TIMEOUT=0\" >> /etc/default/grub')
	self.run_in_target('bash', '-c', 'grep -qxF \"GRUB_HIDDEN_TIMEOUT\" /etc/default/grub || echo \"GRUB_HIDDEN_TIMEOUT=0\" >> /etc/default/grub')
	self.run_in_target('sed', '-ie', 's/\(GRUB_RECORDFAIL_TIMEOUT=\).*/\\1\"0\"/', '/etc/default/grub')
	self.run_in_target('sed', '-ie', 's/\(GRUB_HIDDEN_TIMEOUT=0=\).*/\\1\"0\"/', '/etc/default/grub')

        # reading the kernel command line string to be added from the kclfile
        mycl = ""
        if (kclfile):
            myfh = open(kclfile, "r")
            if myfh:
                mycl = myfh.readline()
                myfh.close()
        logging.debug('mycl=%s' % mycl)
        mycl=mycl.rstrip("\n")

        # updating /etc/default/grub
	self.run_in_target('sed', '-ie', '/GRUB_CMDLINE_LINUX_DEFAULT/s/quiet\(.*\)/%s \\1/' % mycl, '/etc/default/grub')
	self.run_in_target('sed', '-ie', '/GRUB_TIMEOUT=/s/=.*/=\"0\"/', '/etc/default/grub')
	self.run_in_target('sed', '-ie', '/GRUB_TIMEOUT_STYLE=/s/=.*/=\"menu\"/', '/etc/default/grub')
	self.run_in_target('sed', '-ie', 's/splash//', '/etc/default/grub')
	self.run_in_target('cat', '/etc/default/grub')
#        self.run_in_target('grub-mkconfig', '-o', '/boot/grub/grub.cfg') # same as self.run_in_target(self.updategrub)
        self.run_in_target('update-grub') # same as self.run_in_target(self.updategrub)

    def install_menu_lst(self, disks):
#        self.run_in_target(self.updategrub, '-y') # deprecated
        self.run_in_target(self.updategrub)
        self.mangle_grub_menu_lst(disks)
        self.run_in_target(self.updategrub)
        self.run_in_target('grub-set-default', '0')
        pass

    def install_kernel(self, destdir):
        try:
            self.run_in_target('mount', '-t', 'proc', 'proc', '/proc')
#            run_cmd('chroot', destdir, 'apt-get', '--force-yes', '-y', 'install', self.kernel_name(), env={ 'DEBIAN_FRONTEND' : 'noninteractive' }) #deprecated
            run_cmd('chroot', destdir, 'apt-get', '-y', 'install', self.kernel_name(), env={ 'DEBIAN_FRONTEND' : 'noninteractive' })
        finally:
            self.run_in_target('umount', '/proc')
#        run_cmd('umount', '%s/sys' % destdir)
        run_cmd('umount', '%s/dev' % destdir)
#        run_cmd('umount', '%s/proc' % destdir)

    def uses_grub2(self):
        return True
