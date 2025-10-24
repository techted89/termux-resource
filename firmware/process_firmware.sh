#!/bin/bash

# This script processes an Android firmware archive to extract its contents,
# generate a TWRP device tree, and build a TWRP image.

set -e

# --- Configuration ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TOOLS_DIR="$SCRIPT_DIR/tools"
OUTPUT_DIR="$SCRIPT_DIR/output"
EXTRACTOR_PATH="$TOOLS_DIR/extractor/extractor.py"
TWRPDTGEN_PATH="$TOOLS_DIR/twrpdtgen/twrpdtgen/__main__.py"

# --- Functions ---
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

usage() {
    echo "Usage: $0 <firmware_archive>"
    exit 1
}

check_dependencies() {
    log "Checking for required command-line tools..."
    local missing_deps=0
    for dep in repo git python3; do
        if ! command -v "$dep" &> /dev/null; then
            log "ERROR: '$dep' is not installed or not in your PATH."
            missing_deps=1
        fi
    done
    if [ "$missing_deps" -eq 1 ]; then
        log "Please install the missing dependencies and try again."
        exit 1
    fi
    log "All required command-line tools are installed."
}

# --- Main Logic ---
check_dependencies
if [ "$#" -ne 1 ]; then
    usage
fi

FIRMWARE_ARCHIVE=$1
FILENAME=$(basename "$FIRMWARE_ARCHIVE")
DEVICE_NAME="${FILENAME%.*}"
EXTRACTED_FIRMWARE_DIR="$OUTPUT_DIR/$DEVICE_NAME/firmware"
DEVICE_TREE_DIR="$OUTPUT_DIR/$DEVICE_NAME/device_tree"

log "Starting firmware processing for $FIRMWARE_ARCHIVE..."

# 1. Extract the firmware
extract_firmware() {
    log "Attempting to extract firmware with srlabs/extractor..."
    if python3 "$EXTRACTOR_PATH" "$FIRMWARE_ARCHIVE" --system-dir-output "$EXTRACTED_FIRMWARE_DIR"; then
        log "Firmware successfully extracted with srlabs/extractor."
        return 0
    fi

    log "srlabs/extractor failed. Falling back to unblob..."
    if python3 -m unblob "$FIRMWARE_ARCHIVE" --extract-dir "$EXTRACTED_FIRMWARE_DIR"; then
        log "Firmware successfully extracted with unblob."
        return 0
    fi

    log "ERROR: Both srlabs/extractor and unblob failed to extract the firmware."
    exit 1
}

mkdir -p "$EXTRACTED_FIRMWARE_DIR"
extract_firmware
log "Firmware extracted to $EXTRACTED_FIRMWARE_DIR"

# 2. Generate the TWRP device tree
get_android_version() {
    local build_prop
    build_prop=$(find "$EXTRACTED_FIRMWARE_DIR" -name "build.prop" | head -n 1)
    if [ -f "$build_prop" ]; then
        grep "ro.build.version.release" "$build_prop" | cut -d'=' -f2
    else
        echo ""
    fi
}

log "Generating TWRP device tree..."
ANDROID_VERSION=$(get_android_version)
log "Detected Android version: $ANDROID_VERSION"

if [[ "$ANDROID_VERSION" && "$(echo "$ANDROID_VERSION" | cut -d. -f1)" -lt 13 ]]; then
    log "Android version is less than 13. Looking for vendor_boot.img..."
    RECOVERY_IMG=$(find "$EXTRACTED_FIRMWARE_DIR" -name "vendor_boot.img")
    if [ -z "$RECOVERY_IMG" ]; then
        log "vendor_boot.img not found. Falling back to recovery.img..."
        RECOVERY_IMG=$(find "$EXTRACTED_FIRMWARE_DIR" -name "recovery.img")
    fi
else
    RECOVERY_IMG=$(find "$EXTRACTED_FIRMWARE_DIR" -name "recovery.img")
fi

if [ -z "$RECOVERY_IMG" ]; then
    log "recovery.img not found. Trying boot.img..."
    RECOVERY_IMG=$(find "$EXTRACTED_FIRMWARE_DIR" -name "boot.img")
fi

if [ -z "$RECOVERY_IMG" ]; then
    log "ERROR: Could not find a suitable image (recovery.img, boot.img, or vendor_boot.img) in the extracted firmware."
    exit 1
fi

python3 "$TWRPDTGEN_PATH" "$RECOVERY_IMG" --output "$DEVICE_TREE_DIR"
log "TWRP device tree generated at $DEVICE_TREE_DIR"

# 3. Build TWRP
TWRP_SOURCE_DIR="$SCRIPT_DIR/twrp_source"

setup_twrp_build() {
    log "Setting up TWRP build environment..."
    if [ ! -d "$TWRP_SOURCE_DIR/.repo" ]; then
        log "Cloning minimal TWRP manifest..."
        mkdir -p "$TWRP_SOURCE_DIR"
        (
            cd "$TWRP_SOURCE_DIR"
            repo init --depth=1 -u https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git -b twrp-12.1
            repo sync -j"$(nproc --all)"
        )
    else
        log "TWRP source directory already exists. Skipping clone."
    fi

    log "Copying device tree to TWRP source..."
    DEVICE_TREE_PATH=$(find "$DEVICE_TREE_DIR" -mindepth 2 -maxdepth 2 -type d)
    if [ -z "$DEVICE_TREE_PATH" ]; then
        log "ERROR: Could not find the generated device tree."
        exit 1
    fi
    if [ "$(echo "$DEVICE_TREE_PATH" | wc -l)" -ne 1 ]; then
        log "ERROR: Found multiple device trees. Please ensure that the output of twrpdtgen contains only one device tree."
        exit 1
    fi

    MANUFACTURER=$(basename "$(dirname "$DEVICE_TREE_PATH")")
    CODENAME=$(basename "$DEVICE_TREE_PATH")
    TARGET_DEVICE_TREE_DIR="$TWRP_SOURCE_DIR/device/$MANUFACTURER/$CODENAME"
    mkdir -p "$(dirname "$TARGET_DEVICE_TREE_DIR")"
    cp -r "$DEVICE_TREE_PATH" "$TARGET_DEVICE_TREE_DIR"
    log "Device tree copied to $TARGET_DEVICE_TREE_DIR"
}

build_twrp() {
    log "Building TWRP image..."
    (
        cd "$TWRP_SOURCE_DIR"
        export ALLOW_MISSING_DEPENDENCIES=true
        source build/envsetup.sh
        lunch "twrp_$CODENAME-eng"
        mka recoveryimage
    )
    log "TWRP image built successfully."

    BUILT_IMAGE=$(find "$TWRP_SOURCE_DIR/out/target/product/$CODENAME" -name "recovery.img")
    if [ -f "$BUILT_IMAGE" ]; then
        cp "$BUILT_IMAGE" "$OUTPUT_DIR/${DEVICE_NAME}_twrp.img"
        log "TWRP image copied to $OUTPUT_DIR/${DEVICE_NAME}_twrp.img"
    else
        log "ERROR: Could not find the built TWRP image."
        exit 1
    fi
}

setup_twrp_build
build_twrp

log "Firmware processing complete."
