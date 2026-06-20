#!/bin/bash
# Step 4.3: reference-based chimera removal
# Software: vsearch

conda activate <PROJECT_DIR>/bioinfo_env

vsearch \
    --relabel workflow/2_1_relabel.txt