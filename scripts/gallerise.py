from hashlib import sha256
from io import BytesIO
from pathlib import Path
import random
import click
from PIL import Image, ExifTags

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
                exif = image._getexif()

                if exif[orientation] == 3:
                    image=image.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    image=image.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    image=image.rotate(90, expand=True)
                click.echo(f"Corrected orientation for image: {image_path.name}")
                break

        image.save(buf, img.format, optimize=True, quality=85)
        click.echo(f"Compressed image from {hr_size(before_size)} to {hr_size(buf.tell())} bytes")
        with open(image_path, "wb") as f:
            f.write(buf.getbuffer())


def get_new_col_width(min_cols:int, max_cols:int,  current_cols:int) -> int:
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

    directory = Path(path)
    if not directory.is_dir():
        click.echo(f"Provided path '{path}' is not a directory.")
        return
    gallory_structure = [[]]
    cols = int((min_cols+max_cols)/2)
    for index, file in enumerate(directory.glob("*")):
        if file.is_file() and file.suffix.lower() == f".{filetype.lower()}":
            if len(gallory_structure[-1]) >= cols:
                gallory_structure.append([])
            try:
                # Simulate processing the file
                click.echo(f"Processing file: {file.name}")
                old_file_name = file.name
                if not "compgi_" in old_file_name:
                    new_file_name = f"compgi_{sha256(old_file_name.encode('utf8')).hexdigest()[:10]}.{filetype.lower()}"
                    if not testrun:
                        new_file_path = file.with_name(new_file_name)
                        new_file = file.rename(new_file_path)
                        resize_compress_image(new_file.absolute(), 4000)

                    short_code = f"![]({new_file_name})"
                    click.echo(f"Processed {old_file_name} as {new_file_name}, shortcode: {short_code}")
                else:
                    short_code = f"![]({old_file_name})"
                    click.echo(f"Already processed {old_file_name}, shortcode: {short_code}")


                gallory_structure[-1].append(short_code)
                cols = get_new_col_width(min_cols, max_cols, cols)
                # Here you would add your image processing logic
            except Exception as e:
                click.echo(f"Error processing {file.name}: {e}")
    gallary_string = "\n\n".join(" ".join(x) for x in gallory_structure)
    click.echo("\nGallary Structure:")
    click.echo(gallary_string)
if __name__ == "__main__":
    main()
