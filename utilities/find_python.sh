#!/bin/bash

# Activate the project environment if it exists
if test -d env; then
    source env/bin/activate
fi

#Some platforms install Python3 as "python3", others install it as "python".
#VENVs tend to have both.
if hash python3 2>/dev/null; then
    python3 "$@"
else
    python "$@"
fi
