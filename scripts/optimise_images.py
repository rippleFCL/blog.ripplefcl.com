#!/usr/bin/env python3
"""Resize and compress images."""

# Thanks for the inspiration https://ericmjl.github.io/blog/2023/10/14/how-i-made-a-local-pre-commit-hook-to-resize-images/

import sys
from io import BytesIO
from os import stat
from pathlib import Path

from PIL import Image
from pyprojroot import find_root, has_dir  # type: ignore


def resize_image(image_path: Path, max_width: int) -> bool:
    if "compgi_" in image_path.name:
        print(f"Skipping already processed image: {image_path}")
        return False
    with Image.open(image_path) as img:
        if img.size[0] > max_width:
            w_percent = max_width / float(img.size[0])
            h_size = int(float(img.size[1]) * float(w_percent))
            resized_img = img.resize(
                (max_width, h_size), Image.Resampling.LANCZOS, reducing_gap=3
            )
            resized_img.save(image_path, optimize=True)
            return True
    return False


def compress_image(image_path: Path, max_size: int) -> bool:
    if "compgi_" in image_path.name:
        print(f"Skipping already processed image: {image_path}")
        return False
    filesize = stat(image_path).st_size
    if filesize > max_size:
        buf = BytesIO()
        with Image.open(image_path) as img:
            img.save(buf, img.format, optimize=True, quality=85)
            new_size = buf.tell()
        print(image_path, max_size, new_size)
        if new_size <= max_size:
            with open(image_path, "wb") as f:
                f.write(buf.getbuffer())
                return True
        else:
            print(f"Could not compress to desired size: {image_path}, {new_size}")
    return False


def find_images_in_tree(
    root_dir: Path, allowed_extensions: tuple[str, ...]
) -> list[Path]:
    found_paths = [
        match
        for img_type in allowed_extensions
        for match in root_dir.rglob(f"*.{img_type}")
    ]
    return found_paths


def resize_images_in_tree(
    root_dir: Path, allowed_extensions: tuple[str, ...], max_width: int
) -> bool:
    resized_any = False
    for path in find_images_in_tree(root_dir, allowed_extensions):
        if resize_image(path, max_width):
            print(f"Resized: {path}")
            resized_any = True
    return resized_any


def compress_images_in_tree(
    root_dir: Path, allowed_extensions: tuple[str, ...], max_size: int
) -> bool:
    compressed_any = False
    for path in find_images_in_tree(root_dir, allowed_extensions):
        if compress_image(path, max_size):
            print(f"Compressed: {path}")
            compressed_any = True
    return compressed_any


def process_specific_files(
    file_paths: list[Path],
    allowed_extensions: tuple[str, ...],
    max_width: int,
    max_size: int,
) -> tuple[bool, bool]:
    resized_any = False
    compressed_any = False
    for path in file_paths:
        if path.suffix.lstrip(".").lower() in allowed_extensions:
            if resize_image(path, max_width):
                print(f"Resized: {path}")
                resized_any = True
            if compress_image(path, max_size):
                print(f"Compressed: {path}")
                compressed_any = True
    return resized_any, compressed_any


if __name__ == "__main__":
    content_directory = find_root(has_dir(".git")).joinpath("content")
    allowed_extensions = ("jpg", "png")
    maximum_width = 4000
    maximum_size_mb = 3

    # Do not edit
    maximum_size_bytes = maximum_size_mb * 1_048_576

    # Check for passed filenames
    if len(sys.argv) > 1:
        file_paths = [Path(arg).resolve() for arg in sys.argv[1:]]
        resized, compressed = process_specific_files(
            file_paths, allowed_extensions, maximum_width, maximum_size_bytes
        )
    else:
        resized = resize_images_in_tree(
            content_directory, allowed_extensions, maximum_width
        )
        compressed = compress_images_in_tree(
            content_directory, allowed_extensions, maximum_size_bytes
        )

    fail_msg = "Some images were %s. Commit rejected"
    if resized or compressed:
        msg_fmt_str = (
            "resized and compressed"
            if resized and compressed
            else "resized"
            if resized
            else "compressed"
        )
        print(fail_msg % msg_fmt_str)
        exit(1)
    else:
        print("Image(s) within spec.")
        exit(0)
