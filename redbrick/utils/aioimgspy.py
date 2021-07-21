# coding: utf-8
# type: ignore
"""
aioimgspy
======

aioimgspy is a port of imgspy by Derek Lukacs for RedBrick AI.

imgspy finds the metadata (type, size) of an image given its url by fetching
as little as needed. This is a python implementation of `fastimage`_. Supports
image types BMP, CUR, GIF, ICO, JPEG, PNG, PSD, TIFF, WEBP.

.. _fastimage: https://github.com/sdsykes/fastimage

usage
-----

::
    >>> async with aiohttp.ClientSession() as session:
    ...     async with session.get(url) as response:
    ...         await imgspy.probe(response.content)



ORIGINAL license:

Copyright (c) 2017 Nazar Kanaev (nkanaev@live.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""


import struct


# All of this code is taken from imgspy, just added await statements when
# reading from stream.
async def probe(stream):
    """Probe for img dimensions."""
    w, h = None, None
    chunk = await stream.readexactly(26)

    if chunk.startswith(b"\x89PNG\r\n\x1a\n"):
        if chunk[12:16] == b"IHDR":
            w, h = struct.unpack(">LL", chunk[16:24])
        elif chunk[12:16] == b"CgBI":
            # fried png http://www.jongware.com/pngdefry.html
            chunk += await stream.readexactly(40 - len(chunk))
            w, h = struct.unpack(">LL", chunk[32:40])
        else:
            w, h = struct.unpack(">LL", chunk[8:16])
        return {"type": "png", "width": w, "height": h}
    elif chunk.startswith(b"GIF89a") or chunk.startswith(b"GIF87a"):
        w, h = struct.unpack("<HH", chunk[6:10])
        return {"type": "gif", "width": w, "height": h}
    elif chunk.startswith(b"\xff\xd8"):
        start = 2
        data = chunk
        while True:
            if data[start : start + 1] != b"\xff":
                return
            if data[start + 1] in b"\xc0\xc2":
                h, w = struct.unpack(">HH", data[start + 5 : start + 9])
                return {"type": "jpg", "width": w, "height": h}
            (segment_size,) = struct.unpack(">H", data[start + 2 : start + 4])
            data += await stream.readexactly(segment_size + 9)
            start = start + segment_size + 2
    elif chunk.startswith(b"\x00\x00\x01\x00") or chunk.startswith(b"\x00\x00\x02\x00"):
        img_type = "ico" if chunk[2:3] == b"\x01" else "cur"
        num_images = struct.unpack("<H", chunk[4:6])[0]
        w, h = struct.unpack("BB", chunk[6:8])
        w = 256 if w == 0 else w
        h = 256 if h == 0 else h
        return {"type": img_type, "width": w, "height": h, "num_images": num_images}
    elif chunk.startswith(b"BM"):
        headersize = struct.unpack("<I", chunk[14:18])[0]
        if headersize == 12:
            w, h = struct.unpack("<HH", chunk[18:22])
        elif headersize >= 40:
            w, h = struct.unpack("<ii", chunk[18:26])
        else:
            return
        return {"type": "bmp", "width": w, "height": h}
    elif chunk.startswith(b"MM\x00\x2a") or chunk.startswith(b"II\x2a\x00"):
        w, h, orientation = None, None, None

        endian = ">" if chunk[0:2] == b"MM" else "<"
        offset = struct.unpack(endian + "I", chunk[4:8])[0]
        chunk += await stream.readexactly(offset - len(chunk) + 2)

        tag_count = struct.unpack(endian + "H", chunk[offset : offset + 2])[0]
        offset += 2
        for i in range(tag_count):
            if len(chunk) - offset < 12:
                chunk += stream.readexactly(12)
            type = struct.unpack(endian + "H", chunk[offset : offset + 2])[0]
            data = struct.unpack(endian + "H", chunk[offset + 8 : offset + 10])[0]
            offset += 12
            if type == 0x100:
                w = data
            elif type == 0x101:
                h = data
            elif type == 0x112:
                orientation = data
            if all([w, h, orientation]):
                break

        if orientation >= 5:
            w, h = h, w
        return {"type": "tiff", "width": w, "height": h, "orientation": orientation}
    elif chunk[:4] == b"RIFF" and chunk[8:15] == b"WEBPVP8":
        w, h = None, None
        type = chunk[15:16]
        chunk += await stream.readexactly(30 - len(chunk))
        if type == b" ":
            w, h = struct.unpack("<HH", chunk[26:30])
            w, h = w & 0x3FFF, h & 0x3FFF
        elif type == b"L":
            w = 1 + (((ord(chunk[22:23]) & 0x3F) << 8) | ord(chunk[21:22]))
            h = 1 + (
                ((ord(chunk[24:25]) & 0xF) << 10)
                | (ord(chunk[23:24]) << 2)
                | ((ord(chunk[22:23]) & 0xC0) >> 6)
            )
        elif type == b"X":
            w = 1 + struct.unpack("<I", chunk[24:27] + b"\x00")[0]
            h = 1 + struct.unpack("<I", chunk[27:30] + b"\x00")[0]
        return {"type": "webp", "width": w, "height": h}
    elif chunk.startswith(b"8BPS"):
        h, w = struct.unpack(">LL", chunk[14:22])
        return {"type": "psd", "width": w, "height": h}
