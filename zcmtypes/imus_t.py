"""ZCM type definitions
This file automatically generated by zcm.
DO NOT MODIFY BY HAND!!!!
"""

try:
    import cStringIO.StringIO as BytesIO
except ImportError:
    from io import BytesIO
import struct

from .euler_t import euler_t


class imus_t(object):
    __slots__ = ["utime", "imu_values"]

    IS_LITTLE_ENDIAN = False

    def __init__(self):
        self.utime = 0
        self.imu_values = [euler_t() for dim0 in range(4)]

    def encode(self):
        buf = BytesIO()
        buf.write(imus_t._get_packed_fingerprint())
        self._encode_one(buf)
        return buf.getvalue()

    def _encode_one(self, buf):
        buf.write(struct.pack(">q", self.utime))
        for i0 in range(4):
            assert (
                self.imu_values[i0]._get_packed_fingerprint()
                == euler_t._get_packed_fingerprint()
            )
            self.imu_values[i0]._encode_one(buf)

    def decode(data):
        if hasattr(data, "read"):
            buf = data
        else:
            buf = BytesIO(data)
        if buf.read(8) != imus_t._get_packed_fingerprint():
            raise ValueError("Decode error")
        return imus_t._decode_one(buf)

    decode = staticmethod(decode)

    def _decode_one(buf):
        self = imus_t()
        self.utime = struct.unpack(">q", buf.read(8))[0]
        self.imu_values = []
        for i0 in range(4):
            self.imu_values.append(euler_t._decode_one(buf))
        return self

    _decode_one = staticmethod(_decode_one)

    _hash = None

    def _get_hash_recursive(parents):
        if imus_t in parents:
            return 0
        newparents = parents + [imus_t]
        tmphash = (
            0x9C32321114829F77 + euler_t._get_hash_recursive(newparents)
        ) & 0xFFFFFFFFFFFFFFFF
        tmphash = (
            ((tmphash << 1) & 0xFFFFFFFFFFFFFFFF) + ((tmphash >> 63) & 0x1)
        ) & 0xFFFFFFFFFFFFFFFF
        return tmphash

    _get_hash_recursive = staticmethod(_get_hash_recursive)
    _packed_fingerprint = None

    def _get_packed_fingerprint():
        if imus_t._packed_fingerprint is None:
            imus_t._packed_fingerprint = struct.pack(
                ">Q", imus_t._get_hash_recursive([])
            )
        return imus_t._packed_fingerprint

    _get_packed_fingerprint = staticmethod(_get_packed_fingerprint)
