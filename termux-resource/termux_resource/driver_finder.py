import os
import tempfile
from .parser.dtb import Dtb
from elftools.elf.elffile import ELFFile

from .parser.boot_image import BootImage

class DriverFinder:
    def __init__(self, stock_image_path, twrp_image_path, analysis_dir=None):
        self.stock_image_path = stock_image_path
        self.twrp_image_path = twrp_image_path
        self.analysis_dir = analysis_dir
        self.unpacked_stock_dir = tempfile.mkdtemp()
        self.mounted_vendor_dir = tempfile.mkdtemp()
        self.driver_manifest = []
        self.missing_cmdline_args = []

    def find_drivers(self):
        """
        Main orchestration method to find all necessary drivers.
        """
        self.missing_cmdline_args = self._compare_kernel_cmdline()

        self._unpack_stock_image()
        self._mount_vendor_image()

        try:
            if self.analysis_dir:
                print("Using live device analysis data.")
                touchscreen_drivers = self._find_touchscreen_drivers_from_live_dtb()
                self._resolve_dependencies_from_manifest(touchscreen_drivers)
            else:
                print("No analysis data provided, falling back to static analysis.")
                touchscreen_drivers = self._find_touchscreen_drivers_from_dtb()
                for driver in touchscreen_drivers:
                    self._resolve_dependencies(driver)

            self._get_selinux_contexts()
        finally:
            self._cleanup()

        return self.driver_manifest, self.missing_cmdline_args

    def _find_touchscreen_drivers_from_live_dtb(self):
        """
        Parses the live DTB from the analysis directory to find touchscreen drivers.
        """
        print("Finding touchscreen drivers from live DTB...")
        dtb_path = os.path.join(self.analysis_dir, "live_device.dtb")
        if not os.path.exists(dtb_path):
            print("Error: live_device.dtb not found in analysis directory.")
            return []

        with open(dtb_path, 'rb') as f:
            dtb_data = f.read()

        dtb = Dtb.from_bytes(dtb_data)

        touchscreen_driver_names = []
        for node in self._traverse_dtb(dtb.structure_block):
            if node.type == Dtb.Fdt.begin_node and 'touch' in node.body.name:
                for prop_node in self._get_properties(node):
                    if prop_node.body.name == 'compatible':
                        compatible_strings = prop_node.body.property.decode().split('\x00')
                        for compatible_string in compatible_strings:
                            if not compatible_string: continue
                            driver_name = compatible_string.split(',')[-1]
                            if driver_name not in touchscreen_driver_names:
                                touchscreen_driver_names.append(driver_name)
        return touchscreen_driver_names

    def _resolve_dependencies_from_manifest(self, touchscreen_drivers):
        """
        Resolves dependencies using the modules.dep manifest.
        """
        print("Resolving dependencies from modules.dep...")
        modules_dep_path = os.path.join(self.analysis_dir, "modules.dep")
        if not os.path.exists(modules_dep_path):
            print("Warning: modules.dep not found in analysis directory. Falling back to manual resolution.")
            self._unpack_stock_image()
            self._mount_vendor_image()
            for driver in touchscreen_drivers:
                # We need to find the full path to the driver
                found = False
                for root, _, files in os.walk(self.mounted_vendor_dir):
                    if f"{driver}.ko" in files:
                        self._resolve_dependencies(os.path.join(root, f"{driver}.ko"))
                        found = True
                        break
                if not found:
                    print(f"Error: Could not find driver '{driver}.ko' in stock image.")
            self._cleanup()
            return

        dependencies = {}
        with open(modules_dep_path, 'r') as f:
            for line in f:
                parts = line.strip().split(':')
                if len(parts) < 2: continue
                module = parts[0]
                deps = parts[1].strip().split()
                dependencies[module] = deps

        drivers_to_add = touchscreen_drivers.copy()
        processed_drivers = set()

        self._unpack_stock_image()
        self._mount_vendor_image()

        while drivers_to_add:
            driver = drivers_to_add.pop(0)
            if driver in processed_drivers:
                continue

            driver_ko = f"{driver}.ko"
            if driver_ko in dependencies:
                for dep in dependencies[driver_ko]:
                    drivers_to_add.append(dep.replace('.ko', ''))

            # Find the full path of the driver in the stock image
            found = False
            for root, _, files in os.walk(self.mounted_vendor_dir):
                if driver_ko in files:
                    full_path = os.path.join(root, driver_ko)
                    relative_path = os.path.relpath(full_path, self.mounted_vendor_dir)
                    self.driver_manifest.append({'path': full_path, 'relative_path': relative_path, 'selinux_context': None})
                    found = True
                    break
            if not found:
                print(f"Warning: Could not find driver '{driver_ko}' in stock image.")

            processed_drivers.add(driver)

    def _unpack_stock_image(self):
        """
        Unpacks the stock image to a temporary directory.
        """
        print(f"Unpacking {self.stock_image_path} to {self.unpacked_stock_dir}...")
        if 'super' in os.path.basename(self.stock_image_path):
            from .parser.super_image import SuperImage
            super_image = SuperImage(self.stock_image_path)
            super_image.unpack(self.unpacked_stock_dir, 'vendor')
            self.vendor_image_path = os.path.join(self.unpacked_stock_dir, 'vendor.img')
        else:
            self.vendor_image_path = self.stock_image_path

    def _mount_vendor_image(self):
        """
        Mounts the vendor image from the unpacked stock image.
        """
        print(f"Mounting {self.vendor_image_path} to {self.mounted_vendor_dir}...")
        # This will require root privileges. We should inform the user.
        os.system(f"sudo mount -o ro {self.vendor_image_path} {self.mounted_vendor_dir}")

    def _compare_kernel_cmdline(self):
        """
        Compares the kernel command line of the stock and TWRP images.
        """
        print("Comparing kernel command lines...")
        stock_boot_image = BootImage(self.stock_image_path)
        stock_boot_image.parse()
        stock_cmdline = stock_boot_image.header['cmdline'] + ' ' + stock_boot_image.header['extra_cmdline']
        stock_cmdline_args = set(stock_cmdline.split())

        twrp_boot_image = BootImage(self.twrp_image_path)
        twrp_boot_image.parse()
        twrp_cmdline = twrp_boot_image.header['cmdline'] + ' ' + twrp_boot_image.header['extra_cmdline']
        twrp_cmdline_args = set(twrp_cmdline.split())

        return list(stock_cmdline_args - twrp_cmdline_args)

    def _find_touchscreen_drivers_from_dtb(self):
        """
        Parses the DTB to find touchscreen drivers.
        """
        print("Finding touchscreen drivers from DTB...")
        stock_boot_image = BootImage(self.stock_image_path)
        stock_boot_image.parse()
        dtb_data = stock_boot_image.dtb

        if not dtb_data:
            print("No DTB found in the stock image.")
            return []

        dtb = Dtb.from_bytes(dtb_data)

        touchscreen_drivers = []
        for node in self._traverse_dtb(dtb.structure_block):
            if node.type == Dtb.Fdt.begin_node and 'touch' in node.body.name:
                # This is a potential touchscreen node. Now we need to find its properties in the following nodes.
                for prop_node in self._get_properties(node):
                    if prop_node.body.name == 'compatible':
                        compatible_strings = prop_node.body.property.decode().split('\x00')
                        for compatible_string in compatible_strings:
                            if not compatible_string: continue
                            driver_name = compatible_string.split(',')[-1]
                            # Search for the driver file
                            for root, _, files in os.walk(self.mounted_vendor_dir):
                                for file in files:
                                    if file == f"{driver_name}.ko":
                                        if os.path.join(root, file) not in touchscreen_drivers:
                                            touchscreen_drivers.append(os.path.join(root, file))
        return touchscreen_drivers

    def _traverse_dtb(self, node):
        """
        Recursively traverses the DTB node structure.
        """
        if hasattr(node, 'nodes'):
            for subnode in node.nodes:
                yield subnode
                yield from self._traverse_dtb(subnode)

    def _get_properties(self, node):
        """
        Gets the properties of a given DTB node.
        """
        # Properties are the nodes that follow a BEGIN_NODE until the next BEGIN_NODE or END_NODE
        for sibling in node._parent.nodes[node._parent.nodes.index(node) + 1:]:
            if sibling.type == Dtb.Fdt.prop:
                yield sibling
            elif sibling.type in (Dtb.Fdt.begin_node, Dtb.Fdt.end_node):
                break

    def _resolve_dependencies(self, driver_path):
        """
        Resolves the dependencies of a given kernel module.
        """
        print(f"Resolving dependencies for {driver_path}...")
        if driver_path in [d['path'] for d in self.driver_manifest]:
            return # Already processed

        with open(driver_path, 'rb') as f:
            elf = ELFFile(f)
            modinfo = elf.get_section_by_name('.modinfo')
            if modinfo:
                data = modinfo.data()
                fields = data.split(b'\x00')
                for field in fields:
                    if field.startswith(b'depends='):
                        dependencies = field.split(b'=')[1].decode().split(',')
                        for dep in dependencies:
                            if not dep: continue
                            found = False
                            for root, _, files in os.walk(self.mounted_vendor_dir):
                                if f"{dep}.ko" in files:
                                    dep_path = os.path.join(root, f"{dep}.ko")
                                    self._resolve_dependencies(dep_path)
                                    found = True
                                    break
                            if not found:
                                print(f"Warning: Could not find dependency '{dep}' for driver '{driver_path}'")

        relative_path = os.path.relpath(driver_path, self.mounted_vendor_dir)
        self.driver_manifest.append({'path': driver_path, 'relative_path': relative_path, 'selinux_context': None})

    def _get_selinux_contexts(self):
        """
        Gets the SELinux contexts for the drivers in the manifest.
        """
        print("Getting SELinux contexts...")
        for driver in self.driver_manifest:
            try:
                mounted_path = os.path.join(self.mounted_vendor_dir, driver['relative_path'])
                context = os.getxattr(mounted_path, b'security.selinux')
                driver['selinux_context'] = context.decode()
            except OSError as e:
                print(f"Warning: Could not get SELinux context for {driver['path']}: {e}")

    def _cleanup(self):
        """
        Cleans up temporary directories and mounts.
        """
        print("Cleaning up...")
        os.system(f"sudo umount {self.mounted_vendor_dir}")
        os.rmdir(self.mounted_vendor_dir)
        # We need to be careful here, as rmtree can be dangerous
        if self.unpacked_stock_dir and os.path.isdir(self.unpacked_stock_dir):
            import shutil
            shutil.rmtree(self.unpacked_stock_dir)
