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

    args = parser.parse_args()

    if args.command == 'unpack':
        from termux_resource.parser.boot_image import BootImage
        import os
        boot_image = BootImage(args.image)
        boot_image.parse()
        os.makedirs(args.output_dir, exist_ok=True)
        # Save header to JSON file
        import json
        header_serializable = {k: v.decode() if isinstance(v, bytes) else v for k, v in boot_image.header.items()}
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
        ramdisk = create_cpio_archive(os.path.join(args.input_dir, 'ramdisk'))
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
        import subprocess
        import os
        os.makedirs(args.output_dir, exist_ok=True)
        subprocess.run(['python3', 'third_party/lpunpack.py', args.image, args.output_dir], check=True)
        print(f"Unpacked {args.image} to {args.output_dir}")
    elif args.command == 'sign_vbmeta':
        from termux_resource.signer.avb import sign_vbmeta
        sign_vbmeta(args.image, args.key, args.algorithm, args.output_file, args.include_images)
        print(f"Signed {args.image} to {args.output_file}")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
