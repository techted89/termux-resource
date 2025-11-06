import io
import struct
import sys
from pathlib import Path
from typing import IO, List, TypeVar, cast, BinaryIO

SPARSE_HEADER_MAGIC = 0xED26FF3A
SPARSE_HEADER_SIZE = 28
SPARSE_CHUNK_HEADER_SIZE = 12

LP_PARTITION_RESERVED_BYTES = 4096
LP_METADATA_GEOMETRY_MAGIC = 0x616c4467
LP_METADATA_GEOMETRY_SIZE = 4096
LP_METADATA_HEADER_MAGIC = 0x414C5030
LP_SECTOR_SIZE = 512

LP_TARGET_TYPE_LINEAR = 0
LP_TARGET_TYPE_ZERO = 1

class LpUnpackError(Exception):
    """Raised any error unpacking"""
    pass

class SparseHeader:
    def __init__(self, buffer):
        fmt = '<I4H4I'
        (
            self.magic,
            self.major_version,
            self.minor_version,
            self.file_hdr_sz,
            self.chunk_hdr_sz,
            self.blk_sz,
            self.total_blks,
            self.total_chunks,
            self.image_checksum
        ) = struct.unpack(fmt, buffer[0:struct.calcsize(fmt)])

class SparseChunkHeader:
    def __init__(self, buffer):
        fmt = '<2H2I'
        (
            self.chunk_type,
            self.reserved,
            self.chunk_sz,
            self.total_sz,
        ) = struct.unpack(fmt, buffer[0:struct.calcsize(fmt)])

class LpMetadataBase:
    _fmt = None
    @property
    def size(cls) -> int:
        return struct.calcsize(cls._fmt)
    @classmethod
    def get_size(cls) -> int:
        return struct.calcsize(cls._fmt)

class LpMetadataGeometry(LpMetadataBase):
    _fmt = '<2I32s3I'
    def __init__(self, buffer):
        (
            self.magic,
            self.struct_size,
            self.checksum,
            self.metadata_max_size,
            self.metadata_slot_count,
            self.logical_block_size
        ) = struct.unpack(self._fmt, buffer[0:self.size])

class LpMetadataTableDescriptor(LpMetadataBase):
    _fmt = '<3I'
    def __init__(self, buffer):
        (
            self.offset,
            self.num_entries,
            self.entry_size
        ) = struct.unpack(self._fmt, buffer[:self.size])

class LpMetadataPartition(LpMetadataBase):
    _fmt = '<36s4I'
    def __init__(self, buffer):
        (
            self.name,
            self.attributes,
            self.first_extent_index,
            self.num_extents,
            self.group_index
        ) = struct.unpack(self._fmt, buffer[0:self.size])
        self.name = self.name.decode("utf-8").strip('\x00')
    @property
    def filename(self) -> str:
        return f'{self.name}.img'

class LpMetadataExtent(LpMetadataBase):
    _fmt = '<QIQI'
    def __init__(self, buffer):
        (
            self.num_sectors,
            self.target_type,
            self.target_data,
            self.target_source
        ) = struct.unpack(self._fmt, buffer[0:struct.calcsize(self._fmt)])

class LpMetadataHeader(LpMetadataBase):
    _fmt = '<I2hI32sI32s'
    def __init__(self, buffer):
        (
            self.magic,
            self.major_version,
            self.minor_version,
            self.header_size,
            self.header_checksum,
            self.tables_size,
            self.tables_checksum
        ) = struct.unpack(self._fmt, buffer[0:self.size])
        self.flags = 0

class LpMetadataPartitionGroup(LpMetadataBase):
    _fmt = '<36sIQ'
    def __init__(self, buffer):
        (
            self.name,
            self.flags,
            self.maximum_size
        ) = struct.unpack(self._fmt, buffer[0:self.size])
        self.name = self.name.decode("utf-8").strip('\x00')

class LpMetadataBlockDevice(LpMetadataBase):
    _fmt = '<Q2IQ36sI'
    def __init__(self, buffer):
        (
            self.first_logical_sector,
            self.alignment,
            self.alignment_offset,
            self.block_device_size,
            self.partition_name,
            self.flags
        ) = struct.unpack(self._fmt, buffer[0:self.size])
        self.partition_name = self.partition_name.decode("utf-8").strip('\x00')

class Metadata:
    def __init__(self):
        self.header = None
        self.geometry = None
        self.partitions = []
        self.extents = []
        self.groups = []
        self.block_devices = []

    def get_offsets(self, slot_number: int = 0) -> List[int]:
        base = LP_PARTITION_RESERVED_BYTES + (LP_METADATA_GEOMETRY_SIZE * 2)
        _tmp_offset = self.geometry.metadata_max_size * slot_number
        primary_offset = base + _tmp_offset
        backup_offset = base + self.geometry.metadata_max_size * self.geometry.metadata_slot_count + _tmp_offset
        return [primary_offset, backup_offset]

class UnpackJob:
    def __init__(self, name, geometry):
        self.name = name
        self.geometry = geometry
        self.parts = []
        self.total_size = 0

class SparseImage:
    def __init__(self, fd):
        self._fd = fd
        self.header = None

    def check(self):
        self._fd.seek(0)
        self.header = SparseHeader(self._fd.read(SPARSE_HEADER_SIZE))
        return self.header.magic == SPARSE_HEADER_MAGIC

    def _read_data(self, chunk_data_size: int):
        if self.header.chunk_hdr_sz > SPARSE_CHUNK_HEADER_SIZE:
            self._fd.seek(self.header.chunk_hdr_sz - SPARSE_CHUNK_HEADER_SIZE, 1)
        return self._fd.read(chunk_data_size)

    def unsparse(self, out_path):
        with open(out_path, 'wb') as out:
            self._fd.seek(self.header.file_hdr_sz)
            for _ in range(self.header.total_chunks):
                chunk_header = SparseChunkHeader(self._fd.read(SPARSE_CHUNK_HEADER_SIZE))
                chunk_data_size = chunk_header.total_sz - self.header.chunk_hdr_sz
                if chunk_header.chunk_type == 0xCAC1: # Raw
                    data = self._read_data(chunk_data_size)
                    out.write(data)
                elif chunk_header.chunk_type == 0xCAC2: # Fill
                    fill_data = self._read_data(chunk_data_size)
                    out.write(fill_data * (chunk_header.chunk_sz * self.header.blk_sz // len(fill_data)))
                elif chunk_header.chunk_type == 0xCAC3: # Don't care
                    out.seek(chunk_header.chunk_sz * self.header.blk_sz, 1)
                else: # CRC32
                    self._read_data(chunk_data_size)

T = TypeVar('T')

class SuperImage:
    def __init__(self, image_path):
        self._fd: BinaryIO = open(image_path, 'rb')
        self.metadata = None

    def unpack(self, output_dir, partition_name=None):
        try:
            sparse_image = SparseImage(self._fd)
            if sparse_image.check():
                print('Sparse image detected, unsparsing...')
                unsparse_path = Path(output_dir) / 'super.unsparse.img'
                sparse_image.unsparse(unsparse_path)
                self._fd.close()
                self._fd = open(unsparse_path, 'rb')

            self._read_metadata()

            partitions_to_unpack = self.metadata.partitions
            if partition_name:
                partitions_to_unpack = [p for p in self.metadata.partitions if p.name == partition_name]
                if not partitions_to_unpack:
                    raise LpUnpackError(f'Partition not found: {partition_name}')

            for partition in partitions_to_unpack:
                self._extract_partition(partition, output_dir)
        finally:
            self._fd.close()

    def _extract_partition(self, partition, output_dir):
        unpack_job = UnpackJob(name=partition.name, geometry=self.metadata.geometry)

        for i in range(partition.num_extents):
            extent = self.metadata.extents[partition.first_extent_index + i]
            if extent.target_type != LP_TARGET_TYPE_LINEAR:
                continue
            offset = extent.target_data * LP_SECTOR_SIZE
            size = extent.num_sectors * LP_SECTOR_SIZE
            unpack_job.parts.append((offset, size))

        out_path = Path(output_dir) / f'{partition.name}.img'
        print(f'Extracting {partition.name} to {out_path}')
        with open(out_path, 'wb') as out:
            for offset, size in unpack_job.parts:
                self._fd.seek(offset)
                remaining = size
                while remaining > 0:
                    chunk = self._fd.read(min(remaining, 4096))
                    if not chunk:
                        break
                    out.write(chunk)
                    remaining -= len(chunk)

    def _read_metadata(self):
        self._fd.seek(LP_PARTITION_RESERVED_BYTES)
        geometry = LpMetadataGeometry(self._fd.read(LP_METADATA_GEOMETRY_SIZE))
        if geometry.magic != LP_METADATA_GEOMETRY_MAGIC:
            raise LpUnpackError('Invalid geometry magic')

        self.metadata = Metadata()
        self.metadata.geometry = geometry

        for offset in self.metadata.get_offsets():
            self._fd.seek(offset)
            header = LpMetadataHeader(self._fd.read(LpMetadataHeader.get_size()))
            if header.magic == LP_METADATA_HEADER_MAGIC:
                self.metadata.header = header
                break

        if not self.metadata.header:
            raise LpUnpackError('Could not find valid metadata header')

        self._fd.seek(offset + self.metadata.header.header_size)

        desc_size = LpMetadataTableDescriptor.get_size()
        partitions_desc = LpMetadataTableDescriptor(self._fd.read(desc_size))
        extents_desc = LpMetadataTableDescriptor(self._fd.read(desc_size))
        groups_desc = LpMetadataTableDescriptor(self._fd.read(desc_size))
        block_devices_desc = LpMetadataTableDescriptor(self._fd.read(desc_size))

        self.metadata.partitions = self._get_data(partitions_desc, LpMetadataPartition)
        self.metadata.extents = self._get_data(extents_desc, LpMetadataExtent)
        self.metadata.groups = self._get_data(groups_desc, LpMetadataPartitionGroup)
        self.metadata.block_devices = self._get_data(block_devices_desc, LpMetadataBlockDevice)

    def _get_data(self, desc, clazz: T) -> List[T]:
        result = []
        for _ in range(desc.num_entries):
            result.append(clazz(self._fd.read(desc.entry_size)))
        return result
