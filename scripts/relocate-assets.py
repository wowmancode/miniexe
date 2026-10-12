#!/usr/bin/env python3
"""Relocate Winlator's absolute app paths inside pinned runtime tar.zst assets.

The replacement package ID intentionally has the same byte length. Several
bundled ELF libraries embed the old path, so changing their binary layout is
unsafe. Tar members are rewritten individually to preserve valid headers.
"""

import io
import os
from pathlib import Path
import sys
import tarfile
import tempfile

import zstandard as zstd


OLD = "com.winlator"
NEW = "com.miniexes"
ARCHIVES = (
    "container_pattern.tzst",
    "rootfs.tzst",
    "rootfs_patches.tzst",
    "box64/box64-0.4.4.tzst",
    "graphics_driver/vortek-2.1.tzst",
    "graphics_driver/gladio-1.1.tzst",
    "graphics_driver/turnip-26.2.0.tzst",
    "graphics_driver/virgl-23.1.9.tzst",
)


def relocate(data: bytes) -> tuple[bytes, int]:
    count = 0
    for encoding in ("ascii", "utf-16le"):
        old = OLD.encode(encoding)
        new = NEW.encode(encoding)
        count += data.count(old)
        data = data.replace(old, new)
    return data, count


def relocate_archive(path: Path) -> int:
    count = 0
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as output:
        temp_path = Path(output.name)
    try:
        with path.open("rb") as source, temp_path.open("wb") as target:
            with zstd.ZstdDecompressor().stream_reader(source) as reader:
                with zstd.ZstdCompressor(level=9).stream_writer(target) as writer:
                    with tarfile.open(fileobj=reader, mode="r|") as archive:
                        with tarfile.open(fileobj=writer, mode="w|") as relocated:
                            for member in archive:
                                if OLD in member.name:
                                    member.name = member.name.replace(OLD, NEW)
                                    count += 1
                                if OLD in member.linkname:
                                    member.linkname = member.linkname.replace(OLD, NEW)
                                    count += 1
                                if member.isfile():
                                    data = archive.extractfile(member).read()
                                    data, found = relocate(data)
                                    count += found
                                    relocated.addfile(member, io.BytesIO(data))
                                else:
                                    relocated.addfile(member)
        if count == 0:
            raise RuntimeError(f"No Winlator path found in {path}")
        os.replace(temp_path, path)
        return count
    finally:
        temp_path.unlink(missing_ok=True)


def main() -> None:
    if len(OLD) != len(NEW):
        raise RuntimeError("Package IDs must have the same byte length")
    root = Path(sys.argv[1])
    for relative_path in ARCHIVES:
        path = root / relative_path
        if not path.is_file():
            raise FileNotFoundError(path)
        print(f"{relative_path}: {relocate_archive(path)} paths relocated", flush=True)


if __name__ == "__main__":
    main()
