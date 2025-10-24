# Android Firmware Processor

This tool suite allows you to extract, unpack, and create a TWRP recovery image from an Android firmware archive. It automates the process of generating a device tree and building a custom recovery.

## Features

*   **Firmware Extraction**: Extracts a variety of firmware formats (`.zip`, `.pac`, `.bin`, etc.).
*   **TWRP Device Tree Generation**: Automatically creates a TWRP-compatible device tree from the `recovery.img` or `boot.img`.
*   **TWRP Build (Coming Soon)**: The script is set up to be extended with a full TWRP build process.

## Prerequisites

1.  **Linux Environment**: A Debian-based Linux distribution (like Ubuntu) is recommended.
2.  **Python 3**: With `venv` and `pip`.
3.  **Required Packages**: You will need several packages to run the tools. You can install them with:
    ```bash
    sudo apt update
    sudo apt install -y git android-sdk-libsparse-utils liblz4-tool brotli unrar libxml2 libxml2-dev libffi-dev
    ```
4.  **Git**: To clone the necessary repositories.

## How to Use

1.  **Initialize the Tools**:
    The first time you use this script, you need to initialize the submodules and their dependencies:
    ```bash
    git submodule update --init --recursive
    cd firmware/tools/extractor
    ./scripts/init.sh
    cd ../../.. # Return to the root
    ```

2.  **Run the Script**:
    Place your firmware archive in a known location and run the `process_firmware.sh` script:
    ```bash
    ./firmware/process_firmware.sh /path/to/your/firmware.zip
    ```

    The script will:
    *   Extract the firmware to the `firmware/output/<device_name>/firmware` directory.
    *   Generate the TWRP device tree in `firmware/output/<device_name>/device_tree`.
    *   (Future) Build the TWRP image and save it to the `firmware/output` directory.

## Disclaimer

*   This tool modifies system images and is intended for advanced users. Use it at your own risk.
*   The effectiveness of the tools can vary depending on the firmware format and device.
