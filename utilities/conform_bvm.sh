#!/bin/bash

find . -name \*.bvm | xargs -n 1 -P 16 utilities/find_python.sh utilities/bvmfmt.py --symfile build/bugsite_alpha.sym --charmap script/charmap.txt
