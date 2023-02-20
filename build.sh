#! /bin/bash

# export ARCHIVE_NAME="Test"
# export ENVIRONMENT="Debug"

export FILES=(./*.py)

mkdir -p "$ARCHIVE_NAME"
# cp "${FILES[@]}" "$ARCHIVE_NAME"

tmp=$(mktemp) # Create a temporary file
trap "rm -f $tmp; exit 1" 0 1 2 3 13 15

for file in "${FILES[@]}"; do
    echo "Processing $file"
    {
        cat _header.md
        cat "$file"
    } >"$tmp"

    sed -i "s/<deploy-date>/$(date)/g" "$tmp"
    sed -i "s/<deploy-type>/$ENVIRONMENT/g" "$tmp"

    mv "$tmp" "$ARCHIVE_NAME/$file"
done

# zip -r "$ARCHIVE_NAME" "$ARCHIVE_NAME"
