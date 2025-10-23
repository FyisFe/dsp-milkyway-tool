# md5f.py
# A direct Python port of the provided C# MD5F implementation.
# NOTE: This preserves the original (non-standard) IV values exactly.

from __future__ import annotations
from typing import List, Tuple, BinaryIO

MASK32 = 0xFFFFFFFF

def _F(x: int, y: int, z: int) -> int:
    return (x & y) | (~x & z)

def _G(x: int, y: int, z: int) -> int:
    return (x & z) | (y & ~z)

def _H(x: int, y: int, z: int) -> int:
    return x ^ y ^ z

def _I(x: int, y: int, z: int) -> int:
    return y ^ (x | ~z)

def _rol(v: int, s: int) -> int:
    v &= MASK32
    return ((v << s) | (v >> (32 - s))) & MASK32

def _FF(a: int, b: int, c: int, d: int, mj: int, s: int, ti: int) -> int:
    a = (a + _F(b, c, d) + mj + ti) & MASK32
    a = _rol(a, s)
    a = (a + b) & MASK32
    return a

def _GG(a: int, b: int, c: int, d: int, mj: int, s: int, ti: int) -> int:
    a = (a + _G(b, c, d) + mj + ti) & MASK32
    a = _rol(a, s)
    a = (a + b) & MASK32
    return a

def _HH(a: int, b: int, c: int, d: int, mj: int, s: int, ti: int) -> int:
    a = (a + _H(b, c, d) + mj + ti) & MASK32
    a = _rol(a, s)
    a = (a + b) & MASK32
    return a

def _II(a: int, b: int, c: int, d: int, mj: int, s: int, ti: int) -> int:
    a = (a + _I(b, c, d) + mj + ti) & MASK32
    a = _rol(a, s)
    a = (a + b) & MASK32
    return a

class MD5F:
    # Kept as class attributes to mirror the original static fields
    A: int = 0
    B: int = 0
    C: int = 0
    D: int = 0

    # NOTE: These match your C# code exactly (they are NOT the standard MD5 IV).
    @staticmethod
    def _init_state() -> None:
        MD5F.A = 1732584193        # 0x67452301
        MD5F.B = 4024216457        # 0xEFDCAB89  (differs from standard MD5)
        MD5F.C = 2562383102        # 0x98BADCFE
        MD5F.D = 271734598         # 0x10325746  (differs from standard MD5)

    @staticmethod
    def _append(message: bytes) -> List[int]:
        """Mimics the original MD5_Append: pad and return 32-bit little-endian words."""
        num2 = len(message)
        rem = num2 % 64

        if rem < 56:
            pad_zeros = 55 - rem
            total_bytes = num2 - rem + 64
        elif rem == 56:
            pad_zeros = 63
            total_bytes = num2 + 8 + 64
        else:
            pad_zeros = 63 - rem + 56
            total_bytes = num2 + 64 - rem + 64

        # Build padded buffer
        out = bytearray(message)
        out.append(0x80)  # the '1' bit (same as your code’s "num == 1")
        out.extend(b"\x00" * pad_zeros)

        bit_len = (num2 * 8) & ((1 << 64) - 1)
        # append length in bits as 64-bit little endian
        out.extend(bit_len.to_bytes(8, "little"))

        # Convert to 32-bit words (little endian)
        x: List[int] = []
        for i in range(0, total_bytes, 4):
            x.append(int.from_bytes(out[i:i+4], "little"))
        return x

    @staticmethod
    def _append_opt(message: bytes) -> List[int]:
        """Ports MD5_Append_Opt (functionally same output as _append)."""
        num2 = len(message)
        rem = num2 % 64

        if rem < 56:
            pad_zeros = 55 - rem
            total_bytes = num2 - rem + 64
        elif rem == 56:
            pad_zeros = 63
            total_bytes = num2 + 8 + 64
        else:
            pad_zeros = 63 - rem + 56
            total_bytes = num2 + 64 - rem + 64

        # Pre-size buffer roughly like the C# code
        out = bytearray(message)
        out.append(0x80)
        out.extend(b"\x00" * pad_zeros)

        bit_len = (num2 * 8) & ((1 << 64) - 1)
        out.extend(bit_len.to_bytes(8, "little"))

        x: List[int] = []
        for i in range(0, total_bytes, 4):
            x.append(int.from_bytes(out[i:i+4], "little"))
        return x

    @staticmethod
    def _transform(x: List[int]) -> Tuple[int, int, int, int]:
        i = 0
        while i < len(x):
            a, b, c, d = MD5F.A, MD5F.B, MD5F.C, MD5F.D

            # Round 1
            a = _FF(a, b, c, d, x[i + 0],  7, 0xD76AA478)
            d = _FF(d, a, b, c, x[i + 1], 12, 0xE8C7B756)
            c = _FF(c, d, a, b, x[i + 2], 17, 0x242070DB)
            b = _FF(b, c, d, a, x[i + 3], 22, 0xC1BDCEEE)
            a = _FF(a, b, c, d, x[i + 4],  7, 0xF57C0FAF)
            d = _FF(d, a, b, c, x[i + 5], 12, 0x4787C62A)
            c = _FF(c, d, a, b, x[i + 6], 17, 0xA8304613)
            b = _FF(b, c, d, a, x[i + 7], 22, 0xFD469501)
            a = _FF(a, b, c, d, x[i + 8],  7, 0x698098D8)
            d = _FF(d, a, b, c, x[i + 9], 12, 0x8B44F7AF)
            c = _FF(c, d, a, b, x[i +10], 17, 0xFFFF5BB1)
            b = _FF(b, c, d, a, x[i +11], 22, 0x895CD7BE)
            a = _FF(a, b, c, d, x[i +12],  7, 0x6B901122)
            d = _FF(d, a, b, c, x[i +13], 12, 0xFD987193)
            c = _FF(c, d, a, b, x[i +14], 17, 0xA679438E)
            b = _FF(b, c, d, a, x[i +15], 22, 0x49B40821)

            # Round 2
            a = _GG(a, b, c, d, x[i + 1],  5, 0xF61E2562)
            d = _GG(d, a, b, c, x[i + 6],  9, 0xC040B340)
            c = _GG(c, d, a, b, x[i +11], 14, 0x265E5A51)
            b = _GG(b, c, d, a, x[i + 0], 20, 0xE9B6C7AA)
            a = _GG(a, b, c, d, x[i + 5],  5, 0xD62F105D)
            d = _GG(d, a, b, c, x[i +10],  9, 0x02441453)
            c = _GG(c, d, a, b, x[i +15], 14, 0xD8A1E681)
            b = _GG(b, c, d, a, x[i + 4], 20, 0xE7D3FBC8)
            a = _GG(a, b, c, d, x[i + 9],  5, 0x21E1CDE6)
            d = _GG(d, a, b, c, x[i +14],  9, 0xC33707D6)
            c = _GG(c, d, a, b, x[i + 3], 14, 0xF4D50D87)
            b = _GG(b, c, d, a, x[i + 8], 20, 0x455A14ED)
            a = _GG(a, b, c, d, x[i +13],  5, 0xA9E3E905)
            d = _GG(d, a, b, c, x[i + 2],  9, 0xFCEFA3F8)
            c = _GG(c, d, a, b, x[i + 7], 14, 0x676F02D9)
            b = _GG(b, c, d, a, x[i +12], 20, 0x8D2A4C8A)

            # Round 3
            a = _HH(a, b, c, d, x[i + 5],  4, 0xFFFA3942)
            d = _HH(d, a, b, c, x[i + 8], 11, 0x8771F681)
            c = _HH(c, d, a, b, x[i +11], 16, 0x6D9D6122)
            b = _HH(b, c, d, a, x[i +14], 23, 0xFDE5380C)
            a = _HH(a, b, c, d, x[i + 1],  4, 0xA4BEEA44)
            d = _HH(d, a, b, c, x[i + 4], 11, 0x4BDECFA9)
            c = _HH(c, d, a, b, x[i + 7], 16, 0xF6BB4B60)
            b = _HH(b, c, d, a, x[i +10], 23, 0xBEBFBC70)
            a = _HH(a, b, c, d, x[i +13],  4, 0x289B7EC6)
            d = _HH(d, a, b, c, x[i + 0], 11, 0xEAA127FA)
            c = _HH(c, d, a, b, x[i + 3], 16, 0xD4EF3085)
            b = _HH(b, c, d, a, x[i + 6], 23, 0x04881D05)
            a = _HH(a, b, c, d, x[i + 9],  4, 0xD9D4D039)
            d = _HH(d, a, b, c, x[i +12], 11, 0xE6DB99E5)
            c = _HH(c, d, a, b, x[i +15], 16, 0x1FA27CF8)
            b = _HH(b, c, d, a, x[i + 2], 23, 0xC4AC5665)

            # Round 4
            a = _II(a, b, c, d, x[i + 0],  6, 0xF4292244)
            d = _II(d, a, b, c, x[i + 7], 10, 0x432AFF97)
            c = _II(c, d, a, b, x[i +14], 15, 0xAB9423A7)
            b = _II(b, c, d, a, x[i + 5], 21, 0xFC93A039)
            a = _II(a, b, c, d, x[i +12],  6, 0x655B59C3)
            d = _II(d, a, b, c, x[i + 3], 10, 0x8F0CCC92)
            c = _II(c, d, a, b, x[i +10], 15, 0xFFEFF47D)
            b = _II(b, c, d, a, x[i + 1], 21, 0x85845DD1)
            a = _II(a, b, c, d, x[i + 8],  6, 0x6FA87E4F)
            d = _II(d, a, b, c, x[i +15], 10, 0xFE2CE6E0)
            c = _II(c, d, a, b, x[i + 6], 15, 0xA3014314)
            b = _II(b, c, d, a, x[i +13], 21, 0x4E0811A1)
            a = _II(a, b, c, d, x[i + 4],  6, 0xF7537E82)
            d = _II(d, a, b, c, x[i +11], 10, 0xBD3AF235)
            c = _II(c, d, a, b, x[i + 2], 15, 0x2AD7D2BB)
            b = _II(b, c, d, a, x[i + 9], 21, 0xEB86D391)

            MD5F.A = (MD5F.A + a) & MASK32
            MD5F.B = (MD5F.B + b) & MASK32
            MD5F.C = (MD5F.C + c) & MASK32
            MD5F.D = (MD5F.D + d) & MASK32

            i += 16

        return MD5F.A, MD5F.B, MD5F.C, MD5F.D

    @staticmethod
    def _digest_to_bytes(state: Tuple[int, int, int, int]) -> bytes:
        out = bytearray()
        for w in state:
            out.extend(w.to_bytes(4, "little"))
        return bytes(out)

    @staticmethod
    def _bytes_to_hex_upper(bs: bytes) -> str:
        # Match C# ToString("X2")
        return "".join(f"{b:02X}" for b in bs)

    # --- Public APIs mirroring the C# names ---

    @staticmethod
    def Compute(message: bytes) -> str:
        """Compute digest of raw bytes -> uppercase hex (matches C#)."""
        MD5F._init_state()
        x = MD5F._append(message)
        state = MD5F._transform(x)
        return MD5F._bytes_to_hex_upper(MD5F._digest_to_bytes(state))

    @staticmethod
    def Compute_Stream(stream: BinaryIO) -> str:
        """Compute digest of a stream -> uppercase hex (reads whole stream)."""
        data = stream.read()
        MD5F._init_state()
        x = MD5F._append(data)
        state = MD5F._transform(x)
        return MD5F._bytes_to_hex_upper(MD5F._digest_to_bytes(state))

    @staticmethod
    def Compute_Opt(stream: BinaryIO) -> str:
        """Compute digest using the _append_opt variant (kept for parity)."""
        data = stream.read()
        MD5F._init_state()
        x = MD5F._append_opt(data)
        state = MD5F._transform(x)
        return MD5F._bytes_to_hex_upper(MD5F._digest_to_bytes(state))

    @staticmethod
    def Compute_String(message: str, encoding: str = "utf-8") -> str:
        """Compute digest of a string -> uppercase hex."""
        return MD5F.Compute(message.encode(encoding))
