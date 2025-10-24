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

# --- Main Logic ---
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
log "Extracting firmware..."
mkdir -p "$EXTRACTED_FIRMWARE_DIR"
python3 "$EXTRACTOR_PATH" "$FIRMWARE_ARCHIVE" --system-dir-output "$EXTRACTED_FIRMWARE_DIR"
log "Firmware extracted to $EXTRACTED_FIRMWARE_DIR"

# 2. Generate the TWRP device tree
log "Generating TWRP device tree..."
RECOVERY_IMG=$(find "$EXTRACTED_FIRMWARE_DIR" -name "recovery.img")
if [ -z "$RECOVERY_IMG" ]; then
    log "recovery.img not found. Trying boot.img..."
    RECOVERY_IMG=$(find "$EXTRACTED_FIRMWARE_DIR" -name "boot.img")
fi

if [ -z "$RECOVERY_IMG" ]; then
    log "ERROR: Neither recovery.img nor boot.img found in the extracted firmware."
    exit 1
fi

python3 "$TWRPDTGEN_PATH" "$RECOVERY_IMG" --output "$DEVICE_TREE_DIR"
log "TWRP device tree generated at $DEVICE_TREE_DIR"

# 3. Build TWRP
TWRP_SOURCE_DIR="$OUTPUT_DIR/$DEVICE_NAME/twrp_source"

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
    MANUFACTURER=$(ls "$DEVICE_TREE_DIR")
    CODENAME=$(ls "$DEVICE_TREE_DIR/$MANUFACTURER")
    TARGET_DEVICE_TREE_DIR="$TWRP_SOURCE_DIR/device/$MANUFACTURER/$CODENAME"
    mkdir -p "$(dirname "$TARGET_DEVICE_TREE_DIR")"
    cp -r "$DEVICE_TREE_DIR/$MANUFACTURER/$CODENAME" "$TARGET_DEVICE_TREE_DIR"
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
