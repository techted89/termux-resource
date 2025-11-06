import os
from struct import unpack

class SparseImage:
    def __init__(self, path):
        self.path = path
        self.header = None
        self.chunks = []

    def parse(self):
        with open(self.path, 'rb') as f:
            self.header = self.parse_header(f)
            self.parse_chunks(f)

    def parse_header(self, f):
        header_bin = f.read(28)
        header = unpack("<I4H4I", header_bin)
        return {
            'magic': header[0],
            'major_version': header[1],
            'minor_version': header[2],
            'file_hdr_sz': header[3],
            'chunk_hdr_sz': header[4],
            'blk_sz': header[5],
            'total_blks': header[6],
            'total_chunks': header[7],
            'image_checksum': header[8],
        }

    def parse_chunks(self, f):
        for _ in range(self.header['total_chunks']):
            header_bin = f.read(12)
            header = unpack("<2H2I", header_bin)
            self.chunks.append({
                'chunk_type': header[0],
                'reserved1': header[1],
                'chunk_sz': header[2],
                'total_sz': header[3],
            })

    def unsparse(self, output_path):
        with open(self.path, 'rb') as in_f, open(output_path, 'wb') as out_f:
            in_f.seek(self.header['file_hdr_sz'])
            for chunk in self.chunks:
                if chunk['chunk_type'] == 0xCAC1:
                    # Raw data
                    data_sz = chunk['total_sz'] - self.header['chunk_hdr_sz']
                    out_f.write(in_f.read(data_sz))
                elif chunk['chunk_type'] == 0xCAC2:
                    # Fill
                    fill_bin = in_f.read(4)
                    fill = unpack("<I", fill_bin)[0]
                    out_f.write(bytearray([fill] * (chunk['chunk_sz'] * self.header['blk_sz'])))
                elif chunk['chunk_type'] == 0xCAC3:
                    # Don't care
                    out_f.seek(chunk['chunk_sz'] * self.header['blk_sz'], os.SEEK_CUR)
                elif chunk['chunk_type'] == 0xCAC4:
                    # CRC32
                    in_f.read(4)
