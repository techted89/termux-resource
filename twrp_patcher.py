import os
import tempfile
import shutil
from parser.boot_image import BootImage, unpack_ramdisk, create_cpio_archive

class TwrpPatcher:
    def __init__(self, twrp_image_path, driver_manifest, missing_cmdline_args):
        self.twrp_image_path = twrp_image_path
        self.driver_manifest = driver_manifest
        self.missing_cmdline_args = missing_cmdline_args
        self.unpacked_twrp_dir = tempfile.mkdtemp()
        self.unpacked_ramdisk_dir = tempfile.mkdtemp()

    def patch_twrp(self):
        """
        Main orchestration method to patch the TWRP image.
        """
        self._unpack_twrp()
        self._inject_drivers()
        self._patch_init_rc()
        patched_image_path = self._repack_twrp()
        self._cleanup()
        return patched_image_path

    def _unpack_twrp(self):
        """
        Unpacks the TWRP image and its ramdisk to temporary directories.
        """
        print(f"Unpacking {self.twrp_image_path} to {self.unpacked_twrp_dir}...")
        boot_image = BootImage(self.twrp_image_path)
        boot_image.parse()
        # Save all parts of the boot image
        # Prepare header for JSON serialization
        header_serializable = boot_image.header.copy()
        for key, value in header_serializable.items():
            if isinstance(value, bytes):
                if key == 'sha':
                    header_serializable[key] = value.hex()
                else:
                    header_serializable[key] = value.decode(errors='ignore')

        with open(os.path.join(self.unpacked_twrp_dir, 'header.json'), 'w') as f:
            import json
            json.dump(header_serializable, f, indent=4)
        with open(os.path.join(self.unpacked_twrp_dir, 'kernel'), 'wb') as f:
            f.write(boot_image.kernel)
        ramdisk_path = os.path.join(self.unpacked_twrp_dir, 'ramdisk.cpio.gz')
        with open(ramdisk_path, 'wb') as f:
            f.write(boot_image.ramdisk)

        print(f"Unpacking ramdisk to {self.unpacked_ramdisk_dir}...")
        unpack_ramdisk(ramdisk_path, self.unpacked_ramdisk_dir)

    def _inject_drivers(self):
        """
        Injects the driver files into the ramdisk and sets their contexts.
        """
        print("Injecting drivers into ramdisk...")
        for driver in self.driver_manifest:
            dest_path = os.path.join(self.unpacked_ramdisk_dir, driver['relative_path'])
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy(driver['path'], dest_path)
            os.chmod(dest_path, 0o644)
            if driver['selinux_context']:
                try:
                    os.setxattr(dest_path, b'security.selinux', driver['selinux_context'].encode())
                except OSError as e:
                    print(f"Warning: Could not set SELinux context for {dest_path}: {e}")

    def _patch_init_rc(self):
        """
        Modifies an init.rc script to load the injected drivers.
        """
        print("Patching init.rc...")
        init_rc_path = None
        for root, _, files in os.walk(self.unpacked_ramdisk_dir):
            for file in files:
                if file.startswith('init.recovery.') and file.endswith('.rc'):
                    init_rc_path = os.path.join(root, file)
                    break
            if init_rc_path:
                break

        if not init_rc_path:
            print("Warning: Could not find a suitable init.rc file to patch.")
            return

        with open(init_rc_path, 'a') as f:
            f.write('\n\n# Injected by termux-resource for touchscreen drivers\n')
            for driver in self.driver_manifest:
                # The path for insmod should be absolute from the root of the ramdisk
                insmod_path = os.path.join('/', driver['relative_path'])
                f.write(f"insmod {insmod_path}\n")

    def _repack_twrp(self):
        """
        Repacks the ramdisk and the final TWRP image.
        """
        print("Repacking TWRP image...")
        new_ramdisk = create_cpio_archive(self.unpacked_ramdisk_dir)

        with open(os.path.join(self.unpacked_twrp_dir, 'header.json'), 'r') as f:
            import json
            header = json.load(f)

        # Convert necessary fields back to bytes
        header['magic'] = header['magic'].encode()
        header['sha'] = bytes.fromhex(header['sha'])
        if 'name' in header: header['name'] = header['name'].encode()
        if 'cmdline' in header: header['cmdline'] = header['cmdline'].encode()
        if 'extra_cmdline' in header: header['extra_cmdline'] = header['extra_cmdline'].encode()

        header['ramdisk_size'] = len(new_ramdisk)
        header['cmdline'] += (' ' + ' '.join(self.missing_cmdline_args)).encode()

        with open(os.path.join(self.unpacked_twrp_dir, 'kernel'), 'rb') as f:
            kernel = f.read()

        output_path = os.path.join(tempfile.gettempdir(), 'patched_twrp.img')
        BootImage.repack(output_path, header, kernel, new_ramdisk)

        return output_path

    def _cleanup(self):
        """
        Cleans up temporary directories.
        """
        print("Cleaning up...")
        shutil.rmtree(self.unpacked_twrp_dir)
        shutil.rmtree(self.unpacked_ramdisk_dir)
