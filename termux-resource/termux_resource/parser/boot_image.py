import os
from struct import unpack, pack
import subprocess

def create_cpio_archive(directory):
    """
    Creates a CPIO archive of the given directory.
    """
    # Create a new cpio archive
    find_proc = subprocess.Popen(['find', '.', '-print0'], cwd=directory, stdout=subprocess.PIPE)
    cpio_proc = subprocess.Popen(
        ['cpio', '--create', '--format=newc', '--null'],
        stdin=find_proc.stdout,
        stdout=subprocess.PIPE,
        cwd=directory
    )
    # Gzip the archive
    gzip_proc = subprocess.Popen(['gzip', '-9'], stdin=cpio_proc.stdout, stdout=subprocess.PIPE)

    find_proc.stdout.close()
    cpio_proc.stdout.close()

    output = gzip_proc.communicate()[0]

    return output

def unpack_ramdisk(ramdisk_path, output_dir):
    """
    Unpacks a CPIO archive.
    """
    gunzip_proc = subprocess.Popen(['gunzip', '-c', ramdisk_path], stdout=subprocess.PIPE)
    cpio_proc = subprocess.Popen(['cpio', '-i', '-d'], stdin=gunzip_proc.stdout, cwd=output_dir)
    gunzip_proc.stdout.close()
    cpio_proc.wait()

class BootImage:
    def __init__(self, path):
        self.path = path
        self.header = None
        self.kernel = None
        self.ramdisk = None
        self.second = None
        self.dtb = None
        self.recovery_dtbo = None

    def parse(self):
        with open(self.path, 'rb') as f:
            self.header = self.parse_header(f)
            self.extract_sections(f)

    def parse_header(self, f):
        header = {}
        header['magic'] = f.read(8)
        if header['magic'] != b'ANDROID!':
            raise ValueError('Not a valid boot image')

        header['kernel_size'] = unpack('I', f.read(4))[0]
        header['kernel_addr'] = unpack('I', f.read(4))[0]
        header['ramdisk_size'] = unpack('I', f.read(4))[0]
        header['ramdisk_addr'] = unpack('I', f.read(4))[0]
        header['second_size'] = unpack('I', f.read(4))[0]
        header['second_addr'] = unpack('I', f.read(4))[0]
        header['tags_addr'] = unpack('I', f.read(4))[0]
        header['page_size'] = unpack('I', f.read(4))[0]
        header['header_version'] = unpack('I', f.read(4))[0]
        header['os_version'] = unpack('I', f.read(4))[0]
        header['name'] = f.read(16).decode().strip('\x00')
        header['cmdline'] = f.read(512).decode().strip('\x00')
        header['sha'] = f.read(32)
        header['extra_cmdline'] = f.read(1024).decode().strip('\x00')

        if header['header_version'] > 0:
            header['recovery_dtbo_size'] = unpack('I', f.read(4))[0]
            header['recovery_dtbo_offset'] = unpack('Q', f.read(8))[0]
            header['boot_header_size'] = unpack('I', f.read(4))[0]

        if header['header_version'] > 1:
            header['dtb_size'] = unpack('I', f.read(4))[0]
            header['dtb_addr'] = unpack('Q', f.read(8))[0]

        return header

    def extract_sections(self, f):
        page_size = self.header['page_size']
        kernel_pages = (self.header['kernel_size'] + page_size - 1) // page_size
        ramdisk_pages = (self.header['ramdisk_size'] + page_size - 1) // page_size
        second_pages = (self.header['second_size'] + page_size - 1) // page_size

        kernel_offset = page_size
        f.seek(kernel_offset)
        self.kernel = f.read(self.header['kernel_size'])

        ramdisk_offset = kernel_offset + kernel_pages * page_size
        f.seek(ramdisk_offset)
        self.ramdisk = f.read(self.header['ramdisk_size'])

        if self.header['second_size'] > 0:
            second_offset = ramdisk_offset + ramdisk_pages * page_size
            f.seek(second_offset)
            self.second = f.read(self.header['second_size'])

        if self.header.get('dtb_size', 0) > 0:
            dtb_offset = ramdisk_offset + ramdisk_pages * page_size + second_pages * page_size
            f.seek(dtb_offset)
            self.dtb = f.read(self.header['dtb_size'])

        if self.header.get('recovery_dtbo_size', 0) > 0:
            f.seek(self.header['recovery_dtbo_offset'])
            self.recovery_dtbo = f.read(self.header['recovery_dtbo_size'])

    @staticmethod
    def repack(output_path, header, kernel, ramdisk, second=None, dtb=None, recovery_dtbo=None):
        with open(output_path, 'wb') as f:
            f.write(header['magic'])
            f.write(pack('I', header['kernel_size']))
            f.write(pack('I', header['kernel_addr']))
            f.write(pack('I', header['ramdisk_size']))
            f.write(pack('I', header['ramdisk_addr']))
            f.write(pack('I', header['second_size']))
            f.write(pack('I', header['second_addr']))
            f.write(pack('I', header['tags_addr']))
            f.write(pack('I', header['page_size']))
            f.write(pack('I', header['header_version']))
            f.write(pack('I', header['os_version']))
            f.write(header['name'].encode().ljust(16, b'\0'))
            f.write(header['cmdline'].encode().ljust(512, b'\0'))
            f.write(header['sha'])
            f.write(header['extra_cmdline'].encode().ljust(1024, b'\0'))

            if header['header_version'] > 0:
                f.write(pack('I', header['recovery_dtbo_size']))
                f.write(pack('Q', header['recovery_dtbo_offset']))
                f.write(pack('I', header['boot_header_size']))

            if header['header_version'] > 1:
                f.write(pack('I', header['dtb_size']))
                f.write(pack('Q', header['dtb_addr']))

            # Pad to page size
            f.seek(header['page_size'])

            f.write(kernel)
            # Pad to page size
            f.seek(header['page_size'] * (1 + (len(kernel) + header['page_size'] - 1) // header['page_size']))

            f.write(ramdisk)
            # Pad to page size
            f.seek(header['page_size'] * (1 + (len(kernel) + header['page_size'] - 1) // header['page_size'] + (len(ramdisk) + header['page_size'] - 1) // header['page_size']))

            if second:
                f.write(second)
                # Pad to page size
                f.seek(header['page_size'] * (1 + (len(kernel) + header['page_size'] - 1) // header['page_size'] + (len(ramdisk) + header['page_size'] - 1) // header['page_size'] + (len(second) + header['page_size'] - 1) // header['page_size']))

            if dtb:
                f.write(dtb)

            if recovery_dtbo:
                f.seek(header['recovery_dtbo_offset'])
                f.write(recovery_dtbo)
