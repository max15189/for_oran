"""Creates a soft-pink test invitation PNG using only stdlib (no Pillow needed)."""
import os
import struct
import zlib


def _png_chunk(name: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(name + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + name + data + struct.pack(">I", crc)


def create_png(path: str, width: int = 800, height: int = 400, color=(252, 228, 220)):
    r, g, b = color
    row = bytes([0]) + bytes([r, g, b] * width)   # filter byte + RGB pixels
    raw = row * height
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(_png_chunk(b"IHDR", ihdr))
        f.write(_png_chunk(b"IDAT", zlib.compress(raw)))
        f.write(_png_chunk(b"IEND", b""))
    print(f"Test image created: {path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "static", "invitation.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    create_png(out)
