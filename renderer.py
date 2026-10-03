# coding: utf-8
"""Barcode rendering core: pdf417 and code128 -> PNG bytes.

Extracted from barcode_gen's barcode.py / code-128.py so the service owns its
working directory and does not depend on any cwd-relative file layout.
"""
import io
import re

from libs.pdf417 import encode, render_image

_DC = {str(i): i for i in range(10)}
_DC.update({chr(ord("A") + i): 10 + i for i in range(6)})


def _byte_from_pair(x: str) -> int:
    return _DC[x[0]] * 16 + _DC[x[1]]


def render_pdf417(data: str, config_str: str) -> bytes:
    data = (
        data.replace("\u240a", "\n", 150)
        .replace("\u240d", "\r", 150)
        .replace("\u241e", "\x1e", 150)
    )

    config: dict[str, str] = {}
    for el in config_str.replace("'", "").split("|"):
        if el:
            key, value = el.split("=", 1)
            config[key] = value

    columns = config.pop("columns")
    sec_level = config.pop("errorLevel")

    els = re.findall(r"x[A-F0-9]{2}", data)
    encoded = [_byte_from_pair(e[1:]) for e in els]
    chars = "".join(chr(c) for c in encoded)

    if len(els) > 2:
        for en in els:
            data = data.replace(en, "")
        data += chars

    codes = encode(
        config,
        data,
        columns=int(columns),
        security_level=int(sec_level),
        numeric_compaction=True,
    )
    image = render_image(codes)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def render_code128(value: str) -> bytes:
    from libs import code128

    image = code128.image(value)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()
