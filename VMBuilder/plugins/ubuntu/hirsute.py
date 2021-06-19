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
from VMBuilder.plugins.ubuntu.focal import Focal
from   VMBuilder.util import run_cmd
import tempfile
import re
import logging

class Hirsute(Focal):
    valid_flavours = { 'i386' :  ['386', 'generic', 'generic-pae', 'virtual'],
                       'amd64' : ['generic', 'server', 'virtual'],
                       'lpia'  : ['lpia'] }

    preferred_filesystem = 'ext4'


    def install_grub(self, chroot_dir, devmapfile, root_dev, kclfile):
        logging.info("BEG of install_grub =====================================================")
        self.install_from_template('/etc/kernel-img.conf', 'kernelimg', { 'updategrub' : self.updategrub })

        # installing the kernel that is in tmplinux, if lkif (linux kernel image file)
        lkif = self.context.get_setting('lkif')
        lkmf = self.context.get_setting('lkmf')
        print('lkif=%s' % lkif)
        print('lkmf=%s' % lkmf)
        if lkif:
            self.run_in_target('apt-get', '-y', 'install', 'linux-base', 'initramfs-tools', env={ 'DEBIAN_FRONTEND' : 'noninteractive' })
            self.run_in_target('rm', '-f', '/boot/{config*,initrd*,System-map*,vmlinuz*}')
            self.run_in_target('mkdir', '/linux')
            self.run_in_target('chmod', '+rx', '/linux')
            tmplinux = self.context.get_setting('tmplinux')
            if lkif:
                run_cmd('rsync', '-a', lkif, '%s/linux' % chroot_dir)
            if lkmf:
                run_cmd('rsync', '-a', lkmf, '%s/linux' % chroot_dir)
            kll = run_cmd('ls', '%s/linux/' % chroot_dir).split('\n')
            r=re.compile('linux-image.*')
            kfnl = list(filter(r.match,kll))
            if len(kfnl) > 0:
                # extract the linux version number from the filename
                kfn = kfnl[0]
                kvn = re.search(r'[0-9][^-]*-[0-9]*',kfn).group()
                self.run_in_target('ls', '-la', '/linux/')
                self.run_in_target('bash', '-c', 'dpkg -i --force-all /linux/*')
                self.run_in_target('apt', '--fix-broken', 'install')
                self.run_in_target('update-initramfs', '-c', '-k', kvn)
                self.run_in_target('apt-mark', 'hold', 'linux-image-generic', 'linux-headers-generic')
            run_cmd('rm', '-rf', tmplinux)

        # select grub architecture-dependent files
        arch = self.context.get_setting('arch')
        arch = 'i386' # forcing an i386 target for grub
        if arch == 'amd64':
            target  = 'x86_64-efi'
            grubpkg = 'grub-efi-amd64'
            grubpk2 = 'efibootmgr'
        else:
            target  = 'i386-pc'
            grubpkg = 'grub-pc'
            grubpk2 = ''

        self.run_in_target('apt-get', '-y', 'install', 'grub2-common', grubpkg, 'fdisk', grubpk2, env={ 'DEBIAN_FRONTEND' : 'noninteractive' })
        self.run_in_target('dpkg-reconfigure', grubpkg, env={ 'UCF_FORCE_CONFFMISS' : 'Yes', 'DEBIAN_FRONTEND' : 'noninteractive' })
        run_cmd('rsync', '-a', '%s%s/%s/' % (chroot_dir, self.grubroot, target), '%s/boot/grub/' % chroot_dir)

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

##        run_cmd('mount', '--bind', '/dev', '%s/dev' % chroot_dir)
#        run_cmd('mount', '--bind', '/proc', '%s/proc' % chroot_dir)
#        run_cmd('mount', '--bind', '/sys', '%s/sys' % chroot_dir)

#        run_cmd('grub-install', '--boot-directory=%s/boot' % chroot_dir, '--root-directory=%s' % chroot_dir, '/dev/%s' % mydrv)
##        run_cmd('grub-install', '--boot-directory=%s/boot' % chroot_dir, '--root-directory=%s' % chroot_dir, '--target=i386-pc', '/dev/%s' % mydrv)
#        run_cmd('grub-install', '--boot-directory=%s/boot' % chroot_dir, '--root-directory=%s' % chroot_dir, '--target=%s' % target, '/dev/%s' % mydrv, '--no-uefi-secure-boot')
#        run_cmd('mkdir', '%s/boot/efi' % chroot_dir)
#        run_cmd('mount', '')
        run_cmd('grub-install', '--boot-directory=%s/boot' % chroot_dir, '--root-directory=%s' % chroot_dir, '--target=%s' % target, '/dev/%s' % mydrv, '--no-uefi-secure-boot', '--efi-directory=%s/boot/efi' % chroot_dir)


        run_cmd('mount', '--bind', '/dev', '%s/dev' % chroot_dir)
##        run_cmd('mount', '--bind', '/proc', '%s/proc' % chroot_dir)
##        run_cmd('mount', '--bind', '/sys', '%s/sys' % chroot_dir)
        self.run_in_target('touch', '/boot/grub/menu.lst')

        self.run_in_target('grub-editenv', '-', 'unset', 'recordfail')
        self.run_in_target('bash', '-c', 'grep -qxF \"GRUB_RECORDFAIL_TIMEOUT\" /etc/default/grub || echo \"GRUB_RECORDFAIL_TIMEOUT=0\" >> /etc/default/grub')
        self.run_in_target('bash', '-c', 'grep -qxF \"GRUB_HIDDEN_TIMEOUT\" /etc/default/grub || echo \"GRUB_HIDDEN_TIMEOUT=0\" >> /etc/default/grub')
        self.run_in_target('sed', '-ie', 's/\(GRUB_RECORDFAIL_TIMEOUT=\).*/\\1\"5\"/', '/etc/default/grub')
        self.run_in_target('sed', '-ie', 's/\(GRUB_HIDDEN_TIMEOUT=0=\).*/\\1\"0\"/', '/etc/default/grub')

        # Shut down a couple of failing daemons at boot time
        self.run_in_target('systemctl', 'disable', 'systemd-timesyncd.service')
        self.run_in_target(*'systemctl disable systemd-resolved.service'.split(' '))

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
        self.run_in_target('sed', '-ie', '/GRUB_TIMEOUT=/s/=.*/=\"2\"/', '/etc/default/grub')
        self.run_in_target('sed', '-ie', '/GRUB_TIMEOUT_STYLE=/s/=.*/=\"menu\"/', '/etc/default/grub')
        self.run_in_target('sed', '-ie', 's/splash//', '/etc/default/grub')
        self.run_in_target('cat', '/etc/default/grub')
#        self.run_in_target('grub-mkconfig', '-o', '/boot/grub/grub.cfg') # same as self.run_in_target(self.updategrub)
        self.run_in_target('update-grub') # same as self.run_in_target(self.updategrub)
        self.run_in_target('sync')
        self.run_in_target('sync')
#        exit();

#        try:
#            run_cmd('umount', '%s/sys' % destdir)
#            run_cmd('umount', '%s/proc' % destdir)
#        except:
#            pass

        logging.info("END of install_grub =====================================================")

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
            lkif = self.context.get_setting('lkif')
            if not lkif: # if an image was not installed before
#              run_cmd('chroot', destdir, 'apt-get', '--force-yes', '-y', 'install', self.kernel_name(), env={ 'DEBIAN_FRONTEND' : 'noninteractive' }) #deprecated
                run_cmd('chroot', destdir, 'apt-get', '-y', 'install', self.kernel_name(), env={ 'DEBIAN_FRONTEND' : 'noninteractive' })
        finally:
            self.run_in_target('umount', '/proc')
#        run_cmd('umount', '%s/sys' % destdir)
        run_cmd('umount', '%s/dev' % destdir)
#        run_cmd('umount', '%s/proc' % destdir)

    def uses_grub2(self):
        return True

    def install_extras(self):
        seedfile = self.context.get_setting('seedfile')
        if seedfile:
            self.seed(seedfile)

        addpkg = self.context.get_setting('addpkg')
        removepkg = self.context.get_setting('removepkg')
        if not addpkg and not removepkg:
            return

#        cmd = ['apt-get', 'install', '-y', '--force-yes'] #deprecated
        cmd = ['apt-get', 'install', '-y']
        cmd += addpkg or []
        cmd += ['%s-' % pkg for pkg in removepkg or []]
        self.run_in_target(env={ 'DEBIAN_FRONTEND' : 'noninteractive' }, *cmd)

    def update(self):
#        self.run_in_target('apt-get', '-y', '--force-yes', 'update',   #deprecated
#                           env={ 'DEBIAN_FRONTEND' : 'noninteractive' })
        self.run_in_target('apt-get', '-y', 'update',
                           env={ 'DEBIAN_FRONTEND' : 'noninteractive' })
