#!/bin/bash
set -e

> TODO.txt

echo "TODO in this project" > TODO.txt
echo "=====================" >> TODO.txt
echo "" >> TODO.txt

for file in $(find . -name "*.py" -type f); do
    [ -e "$file" ] || continue
    
    if grep -q 'TODO' "$file"; then
        echo "File: $file" >> TODO.txt
        grep -n 'TODO' "$file" >> TODO.txt
        echo "" >> TODO.txt
    fi
done

echo "Done! Check TODO.txt"
