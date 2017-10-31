#!/bin/bash

find . -name \*.bvm -exec python utilities/bvmfmt.py {} script/charmap.txt --symfile build/bugsite_alpha.sym \;