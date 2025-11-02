import struct

def create_dummy_boot_image(filename):
    with open(filename, 'wb') as f:
        # magic
        f.write(b'ANDROID!')
        # kernel_size, kernel_addr, ramdisk_size, ramdisk_addr, second_size, second_addr, tags_addr
        for _ in range(7):
            f.write(struct.pack('I', 0))
        # page_size
        f.write(struct.pack('I', 2048))
        # header_version, os_version
        for _ in range(2):
            f.write(struct.pack('I', 0))
        # name (16 bytes)
        f.write(b'\0' * 16)
        # cmdline (512 bytes)
        f.write(b'\0' * 512)
        # sha (32 bytes)
        f.write(b'\0' * 32)
        # extra_cmdline (1024 bytes)
        f.write(b'\0' * 1024)

def create_dummy_dtb(filename):
    with open(filename, 'wb') as f:
        # Header
        f.write(b'\xd0\x0d\xfe\xed') # magic
        f.write(struct.pack('>I', 68)) # total_size
        f.write(struct.pack('>I', 36)) # ofs_structure_block
        f.write(struct.pack('>I', 60)) # ofs_strings_block
        f.write(struct.pack('>I', 28)) # ofs_memory_reservation_block
        f.write(struct.pack('>I', 17)) # version
        f.write(struct.pack('>I', 16)) # min_compatible_version
        f.write(struct.pack('>I', 0))  # boot_cpuid_phys
        f.write(struct.pack('>I', 8))  # len_strings_block
        f.write(struct.pack('>I', 24)) # len_structure_block

        # Memory reservation block (empty)

        # Structure block
        f.write(struct.pack('>I', 1)) # FDT_BEGIN_NODE
        f.write(b'\0\0\0\0') # Empty node name
        f.write(struct.pack('>I', 2)) # FDT_END_NODE
        f.write(struct.pack('>I', 9)) # FDT_END

        # Strings block
        f.write(b'dummy\0')

create_dummy_boot_image('stock.img')
create_dummy_boot_image('twrp.img')
create_dummy_dtb('mock_analysis/live_device.dtb')
