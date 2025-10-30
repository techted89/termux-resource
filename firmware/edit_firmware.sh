#!/bin/bash

# This script provides a menu-driven interface for unpacking, repacking, and
# mounting Android firmware image files.

set -e

# --- Configuration ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TOOLS_DIR="$SCRIPT_DIR/tools"
AIK_DIR="$TOOLS_DIR/Android-Image-Kitchen"
OUTPUT_DIR="$SCRIPT_DIR/output"

# --- Functions ---
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

usage() {
    echo "Usage: $0"
    echo "This script provides a menu-driven interface for working with Android firmware images."
    exit 1
}

# --- Main Logic ---
main_menu() {
    clear
    echo "----------------------------------------"
    echo " Android Firmware Image Tool"
    echo "----------------------------------------"
    echo "1. Unpack an image file"
    echo "2. Repack a directory"
    echo "3. Mount an image file"
    echo "4. Unmount an image file"
    echo "5. View vbmeta info"
    echo "6. Resign vbmeta"
    echo "7. Create vbmeta"
    echo "8. Auto-detect image type (magic)"
    echo "9. Auto-detect image type (blkid)"
    echo "10. Unpack super.img"
    echo "11. Read data from file"
    echo "12. Write data to file"
    echo "13. Exit"
    echo "----------------------------------------"
    read -p "Enter your choice: " choice

    case $choice in
        1) unpack_menu ;;
        2) repack_menu ;;
        3) mount_menu ;;
        4) unmount_menu ;;
        5) view_vbmeta_info_menu ;;
        6) resign_vbmeta_menu ;;
        7) create_vbmeta_menu ;;
        8) auto_detect_menu ;;
        9) blkid_menu ;;
        10) unpack_super_menu ;;
        11) read_data_menu ;;
        12) write_data_menu ;;
        13) exit 0 ;;
        *) main_menu ;;
    esac
}

write_data_menu() {
    clear
    echo "----------------------------------------"
    echo " Write data to file"
    echo "----------------------------------------"
    read -p "Enter the path to the file: " file
    if [ ! -f "$file" ]; then
        log "ERROR: File not found: $file"
        read -p "Press Enter to continue..."
        main_menu
        return
    fi
    read -p "Enter the offset: " offset
    read -p "Enter the data in hex (e.g., 414243): " data
    python3 -c "import sys; f = open('$file', 'rb+'); f.seek($offset); f.write(bytearray.fromhex('$data')); f.close()"
    log "Wrote successfully."
    read -p "Press Enter to continue..."
    main_menu
}

read_data_menu() {
    clear
    echo "----------------------------------------"
    echo " Read data from file"
    echo "----------------------------------------"
    read -p "Enter the path to the file: " file
    if [ ! -f "$file" ]; then
        log "ERROR: File not found: $file"
        read -p "Press Enter to continue..."
        main_menu
        return
    fi
    read -p "Enter the offset: " offset
    read -p "Enter the number of bytes: " bytes
    hexdump -s "$offset" -n "$bytes" -C "$file"
    read -p "Press Enter to continue..."
    main_menu
}

blkid_menu() {
    clear
    echo "----------------------------------------"
    echo " Auto-detect image type (blkid)"
    echo "----------------------------------------"
    read -p "Enter the path to the image file: " image_file
    if [ ! -f "$image_file" ]; then
        log "ERROR: File not found: $image_file"
        read -p "Press Enter to continue..."
        main_menu
        return
    fi
    blkid "$image_file"
    read -p "Press Enter to continue..."
    main_menu
}

create_vbmeta_menu() {
    clear
    echo "----------------------------------------"
    echo " Create vbmeta"
    echo "----------------------------------------"
    read -p "Enter the path to the output image file: " output_file
    read -p "Enter the path to the key file: " key_file
    read -p "Enter the algorithm (e.g., SHA256_RSA4096): " algorithm
    read -p "Enter the images to include (e.g., --include_descriptors_from_image boot.img): " include_images
    python3 "$TOOLS_DIR/avbtool.py" make_vbmeta_image --output "$output_file" --key "$key_file" --algorithm "$algorithm" $include_images
    log "Created successfully."
    read -p "Press Enter to continue..."
    main_menu
}

unpack_super_menu() {
    clear
    echo "----------------------------------------"
    echo " Unpack super.img"
    echo "----------------------------------------"
    read -p "Enter the path to the super.img file: " super_image
    if [ ! -f "$super_image" ]; then
        log "ERROR: File not found: $super_image"
        read -p "Press Enter to continue..."
        main_menu
        return
    fi
    local output_dir="$OUTPUT_DIR/$(basename "${super_image%.*}")_unpacked"
    mkdir -p "$output_dir"
    python3 "$TOOLS_DIR/lpunpack.py" "$super_image" "$output_dir"
    log "Unpacked successfully."
    read -p "Press Enter to continue..."
    main_menu
}

auto_detect_menu() {
    clear
    echo "----------------------------------------"
    echo " Auto-detect image type"
    echo "----------------------------------------"
    read -p "Enter the path to the image file: " image_file
    if [ ! -f "$image_file" ]; then
        log "ERROR: File not found: $image_file"
        read -p "Press Enter to continue..."
        main_menu
        return
    fi
    detect_image_type "$image_file"
    read -p "Press Enter to continue..."
    main_menu
}

detect_image_type() {
    local image_file=$1
    log "Detecting image type for $image_file..."
    file -m "$TOOLS_DIR/android.magic" "$image_file"
}

view_vbmeta_info_menu() {
    clear
    echo "----------------------------------------"
    echo " View vbmeta info"
    echo "----------------------------------------"
    read -p "Enter the path to the vbmeta image file: " vbmeta_file
    if [ ! -f "$vbmeta_file" ]; then
        log "ERROR: File not found: $vbmeta_file"
        read -p "Press Enter to continue..."
        main_menu
        return
    fi
    python3 "$TOOLS_DIR/avbtool.py" info --image "$vbmeta_file"
    read -p "Press Enter to continue..."
    main_menu
}

resign_vbmeta_menu() {
    clear
    echo "----------------------------------------"
    echo " Resign vbmeta"
    echo "----------------------------------------"
    read -p "Enter the path to the vbmeta image file: " vbmeta_file
    if [ ! -f "$vbmeta_file" ]; then
        log "ERROR: File not found: $vbmeta_file"
        read -p "Press Enter to continue..."
        main_menu
        return
    fi
    read -p "Enter the path to the key file: " key_file
    if [ ! -f "$key_file" ]; then
        log "ERROR: File not found: $key_file"
        read -p "Press Enter to continue..."
        main_menu
        return
    fi
    read -p "Enter the algorithm (e.g., SHA256_RSA4096): " algorithm
    read -p "Enter the images to include (e.g., --include_descriptors_from_image boot.img): " include_images
    read -p "Enter the path to the output image file: " output_file
    python3 "$TOOLS_DIR/avbtool.py" make_vbmeta_image --output "$output_file" --key "$key_file" --algorithm "$algorithm" $include_images
    log "Resigned successfully."
    read -p "Press Enter to continue..."
    main_menu
}

unpack_menu() {
    clear
    echo "----------------------------------------"
    echo " Unpack an image file"
    echo "----------------------------------------"
    read -p "Enter the path to the image file: " image_file
    if [ ! -f "$image_file" ]; then
        log "ERROR: File not found: $image_file"
        read -p "Press Enter to continue..."
        main_menu
        return
    fi
    unpack_image "$image_file"
    read -p "Press Enter to continue..."
    main_menu
}

unpack_image() {
    local image_file=$1
    local image_name=$(basename "$image_file")
    local output_dir="$OUTPUT_DIR/${image_name%.*}"
    mkdir -p "$output_dir"
    log "Unpacking $image_file to $output_dir..."
    python3 "$TOOLS_DIR/unpack_bootimg.py" --boot_img "$image_file" --out "$output_dir"
    log "Unpacked successfully."
}

repack_menu() {
    clear
    echo "----------------------------------------"
    echo " Repack a directory"
    echo "----------------------------------------"
    read -p "Enter the path to the directory: " dir_path
    if [ ! -d "$dir_path" ]; then
        log "ERROR: Directory not found: $dir_path"
        read -p "Press Enter to continue..."
        main_menu
        return
    fi
    repack_image "$dir_path"
    read -p "Press Enter to continue..."
    main_menu
}

repack_image() {
    local dir_path=$1
    local output_file="$OUTPUT_DIR/$(basename "$dir_path").img"
    local args_file="$dir_path/mkbootimg_args.json"
    if [ ! -f "$args_file" ]; then
        log "ERROR: mkbootimg_args.json not found in $dir_path"
        return
    fi
    log "Repacking $dir_path to $output_file..."
    local args=$(python3 -c "import json; f = open('$args_file'); args = json.load(f); f.close(); print(' '.join(['--' + k + ' ' + v for k, v in args.items()]))")
    python3 "$TOOLS_DIR/mkbootimg.py" --kernel "$dir_path/kernel" --ramdisk "$dir_path/ramdisk" $args -o "$output_file"
    log "Repacked successfully."
}

mount_menu() {
    clear
    echo "----------------------------------------"
    echo " Mount an image file"
    echo "----------------------------------------"
    read -p "Enter the path to the image file: " image_file
    if [ ! -f "$image_file" ]; then
        log "ERROR: File not found: $image_file"
        read -p "Press Enter to continue..."
        main_menu
        return
    fi
    read -p "Enter the path to the mount point: " mount_point
    if [ ! -d "$mount_point" ]; then
        log "ERROR: Directory not found: $mount_point"
        read -p "Press Enter to continue..."
        main_menu
        return
    fi
    mount_image "$image_file" "$mount_point"
    read -p "Press Enter to continue..."
    main_menu
}

mount_image() {
    local image_file=$1
    local mount_point=$2
    log "Mounting $image_file to $mount_point..."
    local loop_device=$(sudo losetup -f --show "$image_file")
    sudo mount "$loop_device" "$mount_point"
    log "Mounted successfully."
}

unmount_menu() {
    clear
    echo "----------------------------------------"
    echo " Unmount an image file"
    echo "----------------------------------------"
    read -p "Enter the path to the mount point: " mount_point
    if [ ! -d "$mount_point" ]; then
        log "ERROR: Directory not found: $mount_point"
        read -p "Press Enter to continue..."
        main_menu
        return
    fi
    unmount_image "$mount_point"
    read -p "Press Enter to continue..."
    main_menu
}

unmount_image() {
    local mount_point=$1
    log "Unmounting $mount_point..."
    local loop_device=$(mount | grep "$mount_point" | cut -d' ' -f1)
    sudo umount "$mount_point"
    sudo losetup -d "$loop_device"
    log "Unmounted successfully."
}

main_menu
