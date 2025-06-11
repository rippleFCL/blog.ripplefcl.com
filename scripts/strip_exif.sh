#!/bin/bash

files="$@"

# Check if the orientation tag exists in the file
for file in $files; do
    if exiftool -orientation "$file" | grep -q 'Orientation'; then
        # Run the command preserving the orientation tag
        echo "Processing $file with orientation tag preserved."
        exiftool -m -all= --icc_profile:all -tagsfromfile @ -orientation -overwrite_original "$file"
    else
        echo "Processing $file without orientation tag preserved."
        # Run the command without preserving the orientation tag
        exiftool -m -all= --icc_profile:all -overwrite_original "$file"
    fi
done
