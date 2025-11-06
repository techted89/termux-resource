import os
from struct import unpack

class SuperImage:
    def __init__(self, path):
        self.path = path
        self.metadata = None
        self.partitions = {}

    def parse(self):
        with open(self.path, 'rb') as f:
            self.metadata = self.parse_metadata(f)
            self.extract_partitions(f)

    def parse_metadata(self, f):
        f.seek(4096) # Metadata is located after the first 4096 bytes
        magic = f.read(4)
        if magic != b'glah':
            raise ValueError('Invalid dynamic partition metadata magic')

        metadata = {}
        metadata['major_version'] = unpack('H', f.read(2))[0]
        metadata['minor_version'] = unpack('H', f.read(2))[0]
        metadata['header_size'] = unpack('I', f.read(4))[0]
        metadata['header_checksum'] = f.read(32)
        metadata['tables_size'] = unpack('I', f.read(4))[0]
        metadata['tables_checksum'] = f.read(32)
        metadata['partitions_offset'] = unpack('I', f.read(4))[0]
        metadata['partitions_size'] = unpack('I', f.read(4))[0]
        metadata['partitions_checksum'] = f.read(32)

        return metadata

    def extract_partitions(self, f):
        self.parse_partitions_and_extents(f)
        for name, partition in self.partitions.items():
            partition['data'] = b''
            for extent in partition['extents']:
                f.seek(extent['start'] * 512)
                partition['data'] += f.read(extent['length'] * 512)

    def parse_partitions_and_extents(self, f):
        f.seek(4096 + self.metadata['partitions_offset'])
        num_partitions = self.metadata['partitions_size'] // 128
        for _ in range(num_partitions):
            name = f.read(36).decode().strip('\x00')
            attr_readonly = unpack('I', f.read(4))[0]
            first_extent_index = unpack('I', f.read(4))[0]
            num_extents = unpack('I', f.read(4))[0]
            group_index = unpack('I', f.read(4))[0]
            self.partitions[name] = {
                'readonly': attr_readonly,
                'first_extent_index': first_extent_index,
                'num_extents': num_extents,
                'group_index': group_index,
                'extents': []
            }

        # This is a placeholder for parsing the extent table
        # A real implementation would parse the extent table and populate
        # the 'extents' list for each partition.
