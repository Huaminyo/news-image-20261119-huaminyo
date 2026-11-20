#!/usr/bin/env python3
"""news-image-20261119 entry: copy the rendered front page to /output/entry.png.

Standard library only. The image beside this file is the entry; the program
copies it, so both runs write identical bytes. Outside the grader's container,
MAKEFUN_OUTPUT_DIR stands in for /output:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import os
import shutil

here = os.path.dirname(os.path.abspath(__file__))
out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
os.makedirs(out_dir, exist_ok=True)
shutil.copyfile(os.path.join(here, "entry.png"),
                os.path.join(out_dir, "entry.png"))
