#!/bin/bash
# Step 4.1: dereplication
# Software: vsearch

conda activate <PROJECT_DIR>/bioinfo_env

vsearch \
    --relabel workflow/2_1_relabel.txt