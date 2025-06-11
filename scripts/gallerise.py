from hashlib import sha256
from io import BytesIO
from pathlib import Path
import random
from subprocess import Popen
import subprocess
import click
from PIL import Image, ExifTags
import shutil
import zipfile

def hr_size(size: float) -> str:
    """Convert bytes to a human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def resize_compress_image(image_path: Path, max_width: int):
    before_size = image_path.stat().st_size
    buf = BytesIO()
    with Image.open(image_path) as img:
        exif = img.getexif()
        if img.size[0] > max_width:
            w_percent = max_width / float(img.size[0])
            h_size = int(float(img.size[1]) * float(w_percent))
            image = img.resize(
                (max_width, h_size), Image.Resampling.LANCZOS, reducing_gap=3
            )
            click.echo(f"Resized image from {img.size} to {image.size}")
            img.save(buf, img.format, optimize=True, exif=exif)

            with open(image_path, "wb") as f:
                f.write(buf.getbuffer())

    buf = BytesIO()
    with Image.open(image_path) as img:
        exif = img.getexif()
        img.save(buf, img.format, optimize=True, quality=85, exif=exif)
        click.echo(f"Compressed image from {hr_size(before_size)} to {hr_size(buf.tell())} bytes")
        if buf.tell() >= before_size:
            click.echo(f"Image {image_path.name} got bigger after compression, skipping write.")
            return

        with open(image_path, "wb") as f:
            f.write(buf.getbuffer())



def get_new_col_width(min_cols:int, max_cols:int,  current_cols:int) -> int:
    if random.randint(0, 100) < 95:
        if min_cols < current_cols < max_cols:
            current_cols += random.randint(-1, 1)
        elif current_cols == min_cols:
            current_cols += 1
        elif current_cols == max_cols:
            current_cols -= 1
    return current_cols

@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option("--filetype", type=str, default="jpg", help="File type to process")
@click.option("--rebuild", is_flag=True, default=False, help="Enable debug mode")
def main(path: str, filetype: str, rebuild: bool):
    directory = Path(path)
    if not directory.is_dir():
        click.echo(f"Provided path '{path}' is not a directory.")
        return

    for file in directory.glob("**"):
        if "gallery" not in str(file.parent):
            continue
        elif file.is_file() and file.suffix.lower() == ".zip":
            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall(file.parent)
                click.echo(f"Extracted {file.name} to {file.parent}")

    for file in directory.glob("**"):
        if "gallery" not in str(file.parent):
            continue
        if file.is_file() and file.suffix.lower() == f".{filetype.lower()}":
            if "compgi_" in file.name:
                continue
            new_file = file.parent / f"compgi_{sha256(file.name.encode('utf8')).hexdigest()[:10]}.{filetype.lower()}"
            if new_file.exists() and not rebuild:
                click.echo(f"File {file.name} already processed as {new_file.name}")
                short_code = f"![]({new_file.name})"
                file.unlink()
            else:
                click.echo(f"Processing file: {file.name}")
                try:
                    # Simulate processing the file
                    shutil.copy(file, new_file)
                    resize_compress_image(new_file.absolute(), 4000)
                    strip_exif = Path(__file__).parent / "strip_exif.sh"
                    process = subprocess.run([str(strip_exif.absolute()), str(new_file.absolute())], check=True, capture_output=True)
                    if process.stdout:
                        click.echo(f"Stripped EXIF from {new_file.name} with '{process.stdout.decode('utf-8').strip()}'")
                    else:
                        click.echo(f"Stripped EXIF {new_file.name} successfully.")

                    file.unlink()
                    click.echo(f"Processed {file.name} as {new_file.name}")

                except Exception as e:
                    click.echo(f"Error processing {file.name}: {e}")
                    new_file.unlink()
        elif file.is_file() and file.suffix.lower() != f".{filetype.lower()}" and file.suffix.lower() != ".zip":
            file.unlink()

if __name__ == "__main__":
    main()
