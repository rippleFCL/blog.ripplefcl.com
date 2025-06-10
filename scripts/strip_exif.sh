#!/bin/bash

files="$@"

echo "Processing file: $files" >> test.log
# Check if the orientation tag exists in the file
for file in $files; do
    if exiftool -orientation "$file" | grep -q 'Orientation'; then
        # Run the command preserving the orientation tag
        exiftool -m -all= --icc_profile:all -tagsfromfile @ -orientation -overwrite_original "$file"
    else
        # Run the command without preserving the orientation tag
        exiftool -m -all= --icc_profile:all -overwrite_original "$file"
    fi
    echo "Exif data stripped from $file" >> test.log

done
