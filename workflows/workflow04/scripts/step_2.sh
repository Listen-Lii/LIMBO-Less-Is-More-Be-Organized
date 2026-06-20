#!/bin/bash
# Step 3: primer removal & QC
# Software: vsearch

conda activate <PROJECT_DIR>/bioinfo_env

vsearch \
    --fastaout workflow/2_1_fastaout.fasta \
    --fastq_minlen 1