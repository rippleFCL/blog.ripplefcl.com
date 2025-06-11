from hashlib import sha256
from io import BytesIO
from pathlib import Path
import random
from subprocess import Popen
import subprocess
import click
from PIL import Image, ExifTags
import shutil

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
        if img.size[0] > max_width:
            w_percent = max_width / float(img.size[0])
            h_size = int(float(img.size[1]) * float(w_percent))
            image = img.resize(
                (max_width, h_size), Image.Resampling.LANCZOS, reducing_gap=3
            )
            click.echo(f"Resized image from {img.size} to {image.size}")
        else:
            image = img
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation]=='Orientation':
                exif = image.getexif()
                if orientation in exif:
                    if exif[orientation] == 3:
                        image=image.rotate(180, expand=True)
                    elif exif[orientation] == 6:
                        image=image.rotate(270, expand=True)
                    elif exif[orientation] == 8:
                        image=image.rotate(90, expand=True)
                    click.echo(f"Corrected orientation for image: {image_path.name}")
                else:
                    click.echo(f"No orientation tag in exif for image: {image_path.name}")
                break

        image.save(buf, img.format, optimize=True, quality=85)
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
@click.option("--min-cols", type=int, default=2, help="Number of columns for processing")
@click.option("--max-cols", type=int, default=4, help="Number of columns for processing")
@click.option("--testrun", is_flag=True, default=False, help="Enable debug mode")
def main(path: str, filetype: str, min_cols: int, max_cols: int, testrun: bool):
    if min_cols > max_cols:
        click.echo("Fucked it")
        return
    directory = Path(path)
    if not directory.is_dir():
        click.echo(f"Provided path '{path}' is not a directory.")
        return
    gallery_structure = [[]]
    cols = int((min_cols+max_cols)/2)
    for index, file in enumerate(directory.glob("*")):
        if file.is_file() and file.suffix.lower() == f".{filetype.lower()}":
            if len(gallery_structure[-1]) >= cols:
                gallery_structure.append([])
                cols = get_new_col_width(min_cols, max_cols, cols)

            new_file = file.parent / f"compgi_{sha256(file.name.encode('utf8')).hexdigest()[:10]}.{filetype.lower()}"
            if new_file.exists() :
                click.echo(f"File {file.name} already processed as {new_file.name}")
                short_code = f"![]({new_file.name})"
                file.unlink()
                gallery_structure[-1].append(short_code)
            elif "compgi_" in file.name:
                continue
            else:
                click.echo(f"Processing file: {file.name}")
                try:
                    # Simulate processing the file
                    if not testrun:
                        shutil.copy(file, new_file)
                        resize_compress_image(new_file.absolute(), 4000)
                        strip_exif = Path(__file__).parent / "strip_exif.sh"
                        process = subprocess.run([str(strip_exif.absolute()), str(new_file.absolute())], check=True, shell=True)
                        if process.stdout:
                            click.echo(process.stdout.decode('utf-8'))
                        else:
                            click.echo(f"Stripped exif {new_file.name} successfully.")

                    short_code = f"![]({new_file.name})"
                    gallery_structure[-1].append(short_code)
                    file.unlink()
                    click.echo(f"Processed {file.name} as {new_file.name}, shortcode: {short_code}")

                except Exception as e:
                    click.echo(f"Error processing {file.name}: {e}")
                    new_file.unlink()

    gallery_string = "\n\n".join(" ".join(x) for x in gallery_structure)
    click.echo("\nGallery Structure:")
    click.echo(gallery_string)

if __name__ == "__main__":
    main()
