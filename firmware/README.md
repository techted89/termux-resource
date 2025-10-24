# Android Firmware Processor

This tool suite allows you to extract, unpack, and create a TWRP recovery image from an Android firmware archive. It automates the process of generating a device tree and building a custom recovery.

## Features

*   **Automatic Firmware Extraction**: The script automatically tries to extract the firmware using the best tool for the job. It defaults to `srlabs/extractor` and falls back to `unblob` if the first tool fails.
*   **TWRP Device Tree Generation**: Automatically creates a TWRP-compatible device tree from the `recovery.img`, `boot.img`, or `vendor_boot.img` (for Android < 13).
*   **TWRP Build**: The script automates the entire process of building a TWRP image from the generated device tree.

## Prerequisites

1.  **Linux Environment**: A Debian-based Linux distribution (like Ubuntu) is recommended.
2.  **Python 3**: With `venv` and `pip`.
3.  **Required Packages**: You will need several packages to run the tools.
    *   **TWRP/AOSP Build Dependencies (Ubuntu)**:
        ```bash
        sudo apt-get install git-core gnupg flex bison build-essential zip curl zlib1g-dev gcc-multilib g++-multilib libc6-dev-i386 lib32ncurses5-dev x11proto-core-dev libx11-dev lib32z-dev ccache libgl1-mesa-dev libxml2-utils xsltproc unzip
        ```
    *   **Extractor Dependencies**: Since the script can use either extractor, it is recommended to install the dependencies for both:
        *   **For `srlabs/extractor`**:
            ```bash
            sudo apt install -y android-sdk-libsparse-utils liblz4-tool brotli unrar libxml2-dev libffi-dev
            ```
        *   **For `unblob`**:
            The `unblob` tool has its own set of dependencies. You can install them by running the script included in its repository:
            ```bash
            ./firmware/tools/unblob/install-deps.sh
            ```
4.  **Git & Repo**: You will need `git` and `repo` installed and available in your `PATH`.

## How to Use

1.  **Initialize the Tools**:
    The first time you use this script, you need to initialize the submodules and their dependencies:
    ```bash
    git submodule update --init --recursive
    cd firmware/tools/extractor
    ./scripts/init.sh
    cd ../../.. # Return to the root
    ./firmware/tools/unblob/install-deps.sh
    ```

2.  **Run the Script**:
    Place your firmware archive in a known location and run the `process_firmware.sh` script:
    ```bash
    ./firmware/process_firmware.sh /path/to/your/firmware.zip
    ```

    The script will:
    *   Extract the firmware to the `firmware/output/<device_name>/firmware` directory.
    *   Generate the TWRP device tree in `firmware/output/<device_name>/device_tree`.
    *   Build the TWRP image and save it to the `firmware/output` directory.

## Disclaimer

*   This tool modifies system images and is intended for advanced users. Use it at your own risk.
*   The effectiveness of the tools can vary depending on the firmware format and device.
*   **The auto-generated device tree may not be perfect.** It is a starting point, and you may need to make manual adjustments to get a fully functional TWRP build.
