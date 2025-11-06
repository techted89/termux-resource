from .parser.boot_image import BootImage, create_cpio_archive, unpack_ramdisk
from .parser.super_image import SuperImage
from .parser.identifier import identify_image
from .signer.avb import add_hash_footer, sign_vbmeta
from .device_analyzer import DeviceAnalyzer
from .driver_finder import DriverFinder
from .twrp_patcher import TwrpPatcher
import os
import json
import subprocess

def unpack_image(image_path, output_dir):
    boot_image = BootImage(image_path)
    boot_image.parse()
    os.makedirs(output_dir, exist_ok=True)
    header_serializable = {}
    for k, v in boot_image.header.items():
        if isinstance(v, bytes):
            if k in ['name', 'cmdline', 'extra_cmdline']:
                header_serializable[k] = v.decode().strip('\x00')
            else:
                header_serializable[k] = v.hex()
        else:
            header_serializable[k] = v
    with open(os.path.join(output_dir, 'header.json'), 'w') as f:
        json.dump(header_serializable, f, indent=4)
    with open(os.path.join(output_dir, 'kernel'), 'wb') as f:
        f.write(boot_image.kernel)
    with open(os.path.join(output_dir, 'ramdisk.cpio.gz'), 'wb') as f:
        f.write(boot_image.ramdisk)
    if boot_image.second:
        with open(os.path.join(output_dir, 'second'), 'wb') as f:
            f.write(boot_image.second)
    if boot_image.dtb:
        with open(os.path.join(output_dir, 'dtb'), 'wb') as f:
            f.write(boot_image.dtb)
    if boot_image.recovery_dtbo:
        with open(os.path.join(output_dir, 'recovery_dtbo'), 'wb') as f:
            f.write(boot_image.recovery_dtbo)
    print(f"Unpacked {image_path} to {output_dir}")

def repack_image(input_dir, output_file, no_sign, key, algorithm, partition_name):
    with open(os.path.join(input_dir, 'header.json'), 'r') as f:
        header = json.load(f)
    with open(os.path.join(input_dir, 'kernel'), 'rb') as f:
        kernel = f.read()

    ramdisk_unpacked_path = os.path.join(input_dir, 'ramdisk')
    ramdisk_cpio_path = os.path.join(input_dir, 'ramdisk.cpio.gz')

    if os.path.isdir(ramdisk_unpacked_path):
        ramdisk = create_cpio_archive(ramdisk_unpacked_path)
    elif os.path.exists(ramdisk_cpio_path):
        with open(ramdisk_cpio_path, 'rb') as f:
            ramdisk = f.read()
    else:
        raise FileNotFoundError("Could not find 'ramdisk' directory or 'ramdisk.cpio.gz' in the input directory.")

    second = None
    if os.path.exists(os.path.join(input_dir, 'second')):
        with open(os.path.join(input_dir, 'second'), 'rb') as f:
            second = f.read()
    dtb = None
    if os.path.exists(os.path.join(input_dir, 'dtb')):
        with open(os.path.join(input_dir, 'dtb'), 'rb') as f:
            dtb = f.read()
    recovery_dtbo = None
    if os.path.exists(os.path.join(input_dir, 'recovery_dtbo')):
        with open(os.path.join(input_dir, 'recovery_dtbo'), 'rb') as f:
            recovery_dtbo = f.read()

    # Convert header fields back to bytes
    header['magic'] = header['magic'].encode()
    header['sha'] = bytes.fromhex(header['sha'])
    if 'name' in header: header['name'] = header['name'].encode()
    if 'cmdline' in header: header['cmdline'] = header['cmdline'].encode()
    if 'extra_cmdline' in header: header['extra_cmdline'] = header['extra_cmdline'].encode()

    BootImage.repack(output_file, header, kernel, ramdisk, second, dtb, recovery_dtbo)
    if not no_sign:
        add_hash_footer(output_file, partition_name, os.path.getsize(output_file), key, algorithm, output_file)
    print(f"Repacked {input_dir} to {output_file}")

def analyze_device(output_dir):
    analyzer = DeviceAnalyzer(output_dir)
    analyzer.analyze()

def inject_twrp_drivers(stock_image, twrp_image, output_image, key, algorithm, analysis_dir):
    finder = DriverFinder(stock_image, twrp_image, analysis_dir)
    driver_manifest, missing_cmdline_args = finder.find_drivers()

    if not driver_manifest:
        print("No touchscreen drivers found. Aborting.")
        return

    patcher = TwrpPatcher(twrp_image, driver_manifest, missing_cmdline_args)
    patched_image_path = patcher.patch_twrp()

    if key and algorithm:
        print(f"Signing {patched_image_path}...")
        add_hash_footer(patched_image_path, "boot", os.path.getsize(patched_image_path), key, algorithm, patched_image_path)
    else:
        print("Skipping signing as no key and algorithm were provided.")

    os.rename(patched_image_path, output_image)
    print(f"Patched TWRP image saved to {output_image}")
