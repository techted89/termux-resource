#!/usr/bin/env python3

import argparse

def main():
    parser = argparse.ArgumentParser(description='All-in-one Android image manipulation tool.')
    subparsers = parser.add_subparsers(dest='command')

    # Unpack command
    unpack_parser = subparsers.add_parser('unpack', help='Unpack an image file.')
    unpack_parser.add_argument('image', help='Path to the image file.')
    unpack_parser.add_argument('output_dir', help='Path to the output directory.')

    # Repack command
    repack_parser = subparsers.add_parser('repack', help='Repack a directory.')
    repack_parser.add_argument('input_dir', help='Path to the input directory.')
    repack_parser.add_argument('output_file', help='Path to the output file.')
    repack_parser.add_argument('--no-sign', action='store_true', help='Do not sign the repacked image.')
    repack_parser.add_argument('--key', help='Path to the key file for signing.')
    repack_parser.add_argument('--algorithm', help='Algorithm to use for signing (e.g., SHA256_RSA4096).')
    repack_parser.add_argument('--partition_name', help='Name of the partition for signing.')

    # Unpack ramdisk command
    unpack_ramdisk_parser = subparsers.add_parser('unpack_ramdisk', help='Unpack a ramdisk file.')
    unpack_ramdisk_parser.add_argument('ramdisk', help='Path to the ramdisk file.')
    unpack_ramdisk_parser.add_argument('output_dir', help='Path to the output directory.')

    # Mount command
    mount_parser = subparsers.add_parser('mount', help='Mount an image file.')
    mount_parser.add_argument('image', help='Path to the image file.')
    mount_parser.add_argument('mount_point', help='Path to the mount point.')

    # Unmount command
    unmount_parser = subparsers.add_parser('unmount', help='Unmount an image file.')
    unmount_parser.add_argument('mount_point', help='Path to the mount point.')

    # Identify command
    identify_parser = subparsers.add_parser('identify', help='Identify an image file.')
    identify_parser.add_argument('image', help='Path to the image file.')

    # Unpack super command
    unpack_super_parser = subparsers.add_parser('unpack_super', help='Unpack a super.img file.')
    unpack_super_parser.add_argument('image', help='Path to the super.img file.')
    unpack_super_parser.add_argument('output_dir', help='Path to the output directory.')

    # Sign vbmeta command
    sign_vbmeta_parser = subparsers.add_parser('sign_vbmeta', help='Sign a vbmeta.img file.')
    sign_vbmeta_parser.add_argument('image', help='Path to the vbmeta.img file.')
    sign_vbmeta_parser.add_argument('key', help='Path to the key file.')
    sign_vbmeta_parser.add_argument('algorithm', help='Algorithm to use (e.g., SHA256_RSA4096).')
    sign_vbmeta_parser.add_argument('output_file', help='Path to the output file.')
    sign_vbmeta_parser.add_argument('--include_images', nargs='+', help='Images to include in the vbmeta image.')

    # Detect slot command
    detect_slot_parser = subparsers.add_parser('detect_slot', help='Detect the current slot of a device.')

    # unsparse command
    unsparse_parser = subparsers.add_parser('unsparse', help='Unsparse a sparse image file.')
    unsparse_parser.add_argument('image', help='Path to the sparse image file.')
    unsparse_parser.add_argument('output_file', help='Path to the output file.')

    # fsverity command
    fsverity_parser = subparsers.add_parser('fsverity', help='Enable fs-verity on a file.')
    fsverity_parser.add_argument('file', help='Path to the file.')
    fsverity_parser.add_argument('--signature', help='Path to the signature file.')
    fsverity_parser.add_argument('--key', help='Path to the key file.')
    fsverity_parser.add_argument('--cert', help='Path to the certificate file.')

    # Patch ramdisk command
    patch_ramdisk_parser = subparsers.add_parser('patch_ramdisk', help='Patch a ramdisk file.')
    patch_ramdisk_parser.add_argument('ramdisk', help='Path to the ramdisk file.')
    patch_ramdisk_parser.add_argument('--fstab', help='Path to the new fstab file.')
    patch_ramdisk_parser.add_argument('--init_rc', help='Path to a directory with custom init.rc files.')
    patch_ramdisk_parser.add_argument('--output_file', help='Path to the output file.')

    # TWRP command
    twrp_parser = subparsers.add_parser('twrp', help='Automated features for TWRP.')
    twrp_subparsers = twrp_parser.add_subparsers(dest='twrp_command')

    # TWRP ramdisk command
    twrp_ramdisk_parser = twrp_subparsers.add_parser('ramdisk', help='TWRP ramdisk customization.')
    twrp_ramdisk_parser.add_argument('ramdisk', help='Path to the ramdisk file.')
    twrp_ramdisk_parser.add_argument('--inject', nargs='+', help='Files to inject into the ramdisk (e.g., magisk_bootctl.bin:/sbin/bootctl).')
    twrp_ramdisk_parser.add_argument('--fix-ab', action='store_true', help='Patch the ramdisk for A/B slot support.')
    twrp_ramdisk_parser.add_argument('--disable-verity', action='store_true', help='Disable dm-verity and verification.')
    twrp_ramdisk_parser.add_argument('--output_file', help='Path to the output file.')

    # TWRP inject-drivers command
    twrp_inject_drivers_parser = twrp_subparsers.add_parser('inject-drivers', help='Inject touchscreen drivers into a TWRP image.')
    twrp_inject_drivers_parser.add_argument('stock_image', help='Path to the stock firmware image (e.g., super.img, vendor.img).')
    twrp_inject_drivers_parser.add_argument('twrp_image', help='Path to the TWRP image to patch.')
    twrp_inject_drivers_parser.add_argument('output_image', help='Path to the output patched TWRP image.')
    twrp_inject_drivers_parser.add_argument('--key', help='Path to the key file for signing.')
    twrp_inject_drivers_parser.add_argument('--algorithm', help='Algorithm to use for signing (e.g., SHA256_RSA4096).')

    args = parser.parse_args()

    if args.command == 'unpack':
        from termux_resource.parser.boot_image import BootImage
        import os
        boot_image = BootImage(args.image)
        boot_image.parse()
        os.makedirs(args.output_dir, exist_ok=True)
        # Save header to JSON file
        import json
        header_serializable = {}
        for k, v in boot_image.header.items():
            if isinstance(v, bytes):
                if k in ['name', 'cmdline', 'extra_cmdline']:
                    header_serializable[k] = v.decode().strip('\x00')
                else:
                    header_serializable[k] = v.hex()
            else:
                header_serializable[k] = v
        with open(os.path.join(args.output_dir, 'header.json'), 'w') as f:
            json.dump(header_serializable, f, indent=4)
        with open(os.path.join(args.output_dir, 'kernel'), 'wb') as f:
            f.write(boot_image.kernel)
        with open(os.path.join(args.output_dir, 'ramdisk.cpio.gz'), 'wb') as f:
            f.write(boot_image.ramdisk)
        if boot_image.second:
            with open(os.path.join(args.output_dir, 'second'), 'wb') as f:
                f.write(boot_image.second)
        if boot_image.dtb:
            with open(os.path.join(args.output_dir, 'dtb'), 'wb') as f:
                f.write(boot_image.dtb)
        if boot_image.recovery_dtbo:
            with open(os.path.join(args.output_dir, 'recovery_dtbo'), 'wb') as f:
                f.write(boot_image.recovery_dtbo)
        print(f"Unpacked {args.image} to {args.output_dir}")
    elif args.command == 'repack':
        from termux_resource.parser.boot_image import BootImage, create_cpio_archive
        import json
        import os
        with open(os.path.join(args.input_dir, 'header.json'), 'r') as f:
            header = json.load(f)
        with open(os.path.join(args.input_dir, 'kernel'), 'rb') as f:
            kernel = f.read()

        ramdisk_unpacked_path = os.path.join(args.input_dir, 'ramdisk')
        ramdisk_cpio_path = os.path.join(args.input_dir, 'ramdisk.cpio.gz')

        if os.path.isdir(ramdisk_unpacked_path):
            print(f"Found unpacked ramdisk at {ramdisk_unpacked_path}, creating new CPIO archive.")
            ramdisk = create_cpio_archive(ramdisk_unpacked_path)
        elif os.path.exists(ramdisk_cpio_path):
            print(f"Found ramdisk archive at {ramdisk_cpio_path}, using it directly.")
            with open(ramdisk_cpio_path, 'rb') as f:
                ramdisk = f.read()
        else:
            raise FileNotFoundError("Could not find 'ramdisk' directory or 'ramdisk.cpio.gz' in the input directory.")

        second = None
        if os.path.exists(os.path.join(args.input_dir, 'second')):
            with open(os.path.join(args.input_dir, 'second'), 'rb') as f:
                second = f.read()
        dtb = None
        if os.path.exists(os.path.join(args.input_dir, 'dtb')):
            with open(os.path.join(args.input_dir, 'dtb'), 'rb') as f:
                dtb = f.read()
        recovery_dtbo = None
        if os.path.exists(os.path.join(args.input_dir, 'recovery_dtbo')):
            with open(os.path.join(args.input_dir, 'recovery_dtbo'), 'rb') as f:
                recovery_dtbo = f.read()
        BootImage.repack(args.output_file, header, kernel, ramdisk, second, dtb, recovery_dtbo)
        if not args.no_sign:
            from termux_resource.signer.avb import add_hash_footer
            add_hash_footer(args.output_file, args.partition_name, os.path.getsize(args.output_file), args.key, args.algorithm, args.output_file)
        print(f"Repacked {args.input_dir} to {args.output_file}")
    elif args.command == 'mount':
        import subprocess
        loop_device = subprocess.run(['sudo', 'losetup', '-f', '--show', args.image], capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(['sudo', 'mount', loop_device, args.mount_point], check=True)
        print(f"Mounted {args.image} to {args.mount_point} on {loop_device}")
    elif args.command == 'unmount':
        import subprocess
        subprocess.run(['sudo', 'umount', args.mount_point], check=True)
        print(f"Unmounted {args.mount_point}")
    elif args.command == 'identify':
        from termux_resource.parser.identifier import identify_image
        image_type = identify_image(args.image)
        print(f"Image type: {image_type}")
    elif args.command == 'unpack_super':
        from termux_resource.parser.super_image import SuperImage
        import os
        os.makedirs(args.output_dir, exist_ok=True)
        super_image = SuperImage(args.image)
        super_image.unpack(args.output_dir)
        print(f"Unpacked {args.image} to {args.output_dir}")
    elif args.command == 'sign_vbmeta':
        from termux_resource.signer.avb import sign_vbmeta
        sign_vbmeta(args.image, args.key, args.algorithm, args.output_file, args.include_images)
        print(f"Signed {args.image} to {args.output_file}")
    elif args.command == 'unpack_ramdisk':
        from termux_resource.parser.boot_image import unpack_ramdisk
        import os
        os.makedirs(args.output_dir, exist_ok=True)
        unpack_ramdisk(args.ramdisk, args.output_dir)
        print(f"Unpacked {args.ramdisk} to {args.output_dir}")
    elif args.command == 'detect_slot':
        import subprocess
        try:
            result = subprocess.run(['bootctl', 'get-current-slot'], capture_output=True, text=True, check=True)
            print(f"Current slot: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Could not determine current slot. Ensure you are running on a device with bootctl and A/B partitions.")
    elif args.command == 'fsverity':
        import subprocess
        cmd = ['firmware/tools/fsverity-utils/fsverity', 'enable', args.file]
        if args.signature:
            cmd.extend(['--signature', args.signature])
        if args.key:
            cmd.extend(['--key', args.key])
        if args.cert:
            cmd.extend(['--cert', args.cert])
        subprocess.run(cmd, check=True)
        print(f"Enabled fs-verity on {args.file}")
    elif args.command == 'patch_ramdisk':
        from termux_resource.parser.ramdisk import Ramdisk
        import tempfile
        import shutil
        with tempfile.TemporaryDirectory() as tmpdir:
            ramdisk = Ramdisk(args.ramdisk)
            ramdisk.unpack(tmpdir)
            if args.fstab:
                shutil.copy(args.fstab, os.path.join(tmpdir, 'etc', 'fstab'))
            if args.init_rc:
                for f in os.listdir(args.init_rc):
                    shutil.copy(os.path.join(args.init_rc, f), os.path.join(tmpdir, 'etc', 'init', 'hw'))
            ramdisk.repack(args.output_file)
        print(f"Patched {args.ramdisk} to {args.output_file}")
    elif args.command == 'unsparse':
        from termux_resource.parser.simg2img import SparseImage
        image = SparseImage(args.image)
        image.parse()
        image.unsparse(args.output_file)
        print(f"Unsparsed {args.image} to {args.output_file}")
    elif args.command == 'twrp':
        if args.twrp_command == 'ramdisk':
            print("TWRP ramdisk customization is not yet implemented.")
        elif args.twrp_command == 'inject-drivers':
            from termux_resource.driver_finder import DriverFinder
            from termux_resource.twrp_patcher import TwrpPatcher
            from termux_resource.signer.avb import add_hash_footer
            import os

            finder = DriverFinder(args.stock_image, args.twrp_image)
            driver_manifest, missing_cmdline_args = finder.find_drivers()

            if not driver_manifest:
                print("No touchscreen drivers found. Aborting.")
                return

            patcher = TwrpPatcher(args.twrp_image, driver_manifest, missing_cmdline_args)
            patched_image_path = patcher.patch_twrp()

            # Re-sign the image
            if args.key and args.algorithm:
                print(f"Signing {patched_image_path}...")
                add_hash_footer(patched_image_path, "boot", os.path.getsize(patched_image_path), args.key, args.algorithm, patched_image_path)
            else:
                print("Skipping signing as no key and algorithm were provided.")

            os.rename(patched_image_path, args.output_image)
            print(f"Patched TWRP image saved to {args.output_image}")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
