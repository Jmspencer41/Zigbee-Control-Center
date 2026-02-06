#!/bin/bash
set -e

> TODO.txt

echo "TODOs in this directory" > TODO.txt
echo "========================" >> TODO.txt
echo "" >> TODO.txt

for file in *.py; do
    [ -e "$file" ] || continue
    
    if grep -q 'TODO' "$file"; then
        echo "File: $file" >> TODO.txt
        grep -n 'TODO' "$file" >> TODO.txt
        echo "" >> TODO.txt
    fi
done

echo "Done! Check TODO.txt"
