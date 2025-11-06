import os
import adb_helper

class DeviceAnalyzer:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def analyze(self):
        """
        Main orchestration method to perform all analysis tasks.
        """
        print("Starting device analysis...")
        self.pull_live_dtb()
        self.pull_kernel_config()
        self.pull_module_manifests()
        self.pull_mount_info()
        self.pull_init_scripts()
        print("Device analysis complete.")

    def pull_live_dtb(self):
        """
        Pulls the live Device Tree Blob from the device.
        """
        print("Pulling live DTB...")
        remote_path = "/sdcard/live_device.dtb"
        result = adb_helper.run_adb_shell_su(f"dd if=/sys/firmware/fdt of={remote_path}")
        if result.returncode != 0:
            print(f"Warning: Could not pull DTB from /sys/firmware/fdt: {result.stderr}")
            # Try /proc/device-tree as a fallback
            result = adb_helper.run_adb_shell_su(f"dd if=/proc/device-tree of={remote_path}")
            if result.returncode != 0:
                print(f"Error: Could not pull DTB from /proc/device-tree either: {result.stderr}")
                return

        local_path = os.path.join(self.output_dir, "live_device.dtb")
        result = adb_helper.adb_pull(remote_path, local_path)
        if result.returncode != 0:
            print(f"Error: Could not pull {remote_path} to {local_path}: {result.stderr}")

        # Clean up the file on the device
        adb_helper.run_adb_shell(f"rm {remote_path}")

    def pull_kernel_config(self):
        """
        Pulls the running kernel's configuration.
        """
        print("Pulling kernel config...")
        result = adb_helper.run_adb_shell("zcat /proc/config.gz")
        if result.returncode != 0:
            print(f"Warning: Could not get kernel config from /proc/config.gz: {result.stderr}")
            return

        local_path = os.path.join(self.output_dir, "running.config")
        with open(local_path, 'w') as f:
            f.write(result.stdout)

    def pull_module_manifests(self):
        """
        Pulls the module dependency manifests.
        """
        print("Pulling module manifests...")
        for manifest in ["modules.dep", "modules.load"]:
            remote_path = f"/vendor/lib/modules/{manifest}"
            local_path = os.path.join(self.output_dir, manifest)
            result = adb_helper.adb_pull(remote_path, local_path)
            if result.returncode != 0:
                print(f"Warning: Could not pull {remote_path}: {result.stderr}")

    def pull_mount_info(self):
        """
        Pulls the mount information from the device.
        """
        print("Pulling mount info...")
        result = adb_helper.run_adb_shell("cat /proc/self/mountinfo")
        if result.returncode != 0:
            print(f"Warning: Could not get mount info from /proc/self/mountinfo: {result.stderr}")
            return

        local_path = os.path.join(self.output_dir, "mountinfo.txt")
        with open(local_path, 'w') as f:
            f.write(result.stdout)

    def pull_init_scripts(self):
        """
        Pulls device-specific init scripts.
        """
        print("Pulling init scripts...")
        init_scripts_dir = os.path.join(self.output_dir, "init_scripts")
        os.makedirs(init_scripts_dir, exist_ok=True)

        scripts_to_pull = [
            "/vendor/etc/init/hw/init.processor.rc",
            "/vendor/etc/init/init.device.rc"
        ]

        for script_path in scripts_to_pull:
            local_path = os.path.join(init_scripts_dir, os.path.basename(script_path))
            result = adb_helper.adb_pull(script_path, local_path)
            if result.returncode != 0:
                print(f"Warning: Could not pull {script_path}: {result.stderr}")
