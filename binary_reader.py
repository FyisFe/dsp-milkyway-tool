#!/usr/bin/env python3

import struct
from typing import BinaryIO


class BinReader:
    """Binary reader for parsing binary data with various data type support."""

    def __init__(self, f: BinaryIO):
        self.f = f

    def read(self, n: int) -> bytes:
        """Read exactly n bytes from the stream."""
        b = self.f.read(n)
        if len(b) != n:
            raise EOFError("unexpected EOF")
        return b

    def u32(self) -> int:
        """Read unsigned 32-bit integer (little-endian)."""
        return struct.unpack("<I", self.read(4))[0]

    def i32(self) -> int:
        """Read signed 32-bit integer (little-endian)."""
        return struct.unpack("<i", self.read(4))[0]

    def i64(self) -> int:
        """Read signed 64-bit integer (little-endian)."""
        return struct.unpack("<q", self.read(8))[0]

    def f32(self) -> float:
        """Read 32-bit float (little-endian)."""
        return struct.unpack("<f", self.read(4))[0]

    def u8(self) -> int:
        """Read unsigned 8-bit integer."""
        return struct.unpack("<B", self.read(1))[0]

    def read7bit_encoded_int(self) -> int:
        """
        Read a 7-bit encoded integer.

        Matches the Go read7BitEncodedInt: read little-endian 7-bit continuation int32.
        """
        num = 0
        shift = 0
        # Up to 5 bytes for 32-bit (Go caps at 35 bits in the loop)
        while shift != 35:
            b = self.u8()
            num |= (b & 0x7F) << shift
            shift += 7
            if (b & 0x80) == 0:
                return num
        raise ValueError("too many bytes in what should have been a 7 bit encoded Int32")
