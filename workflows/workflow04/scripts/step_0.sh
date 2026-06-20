#!/bin/bash
# Step 2.1: merge paired-end reads
# Software: vsearch

conda activate <PROJECT_DIR>/bioinfo_env

vsearch \
    --fastq_mergepairs 1 \
    --reverse 2 \
    --fastqout workflow/2_1_fastqout.fastq \
    --fastaout workflow/2_1_fastaout.fasta \
    --relabel workflow/2_1_relabel.txt \
    --fastq_minlen 1 \
    --fastq_maxdiffs 10