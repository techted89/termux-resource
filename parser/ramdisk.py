import os
import subprocess

class Ramdisk:
    def __init__(self, path):
        self.path = path
        self.directory = None

    def unpack(self, output_dir):
        """
        Unpacks a CPIO archive.
        """
        self.directory = output_dir
        os.makedirs(self.directory, exist_ok=True)
        gunzip_proc = subprocess.Popen(['gunzip', '-c', self.path], stdout=subprocess.PIPE)
        cpio_proc = subprocess.Popen(['cpio', '-i', '-d'], stdin=gunzip_proc.stdout, cwd=self.directory)
        gunzip_proc.stdout.close()
        cpio_proc.wait()

    def repack(self, output_path):
        """
        Creates a CPIO archive of the given directory.
        """
        # Create a new cpio archive
        find_proc = subprocess.Popen(['find', '.', '-print0'], cwd=self.directory, stdout=subprocess.PIPE)
        cpio_proc = subprocess.Popen(
            ['cpio', '--create', '--format=newc', '--null'],
            stdin=find_proc.stdout,
            stdout=subprocess.PIPE,
            cwd=self.directory
        )
        # Gzip the archive
        gzip_proc = subprocess.Popen(['gzip', '-9'], stdin=cpio_proc.stdout, stdout=subprocess.PIPE)

        find_proc.stdout.close()
        cpio_proc.stdout.close()

        with open(output_path, 'wb') as f:
            f.write(gzip_proc.communicate()[0])
