#!/bin/bash
# Workflow: workflow
# Generated from: workflow.md

conda activate <PROJECT_DIR>/bioinfo_env

# Step 2.1: merge paired-end reads
# Software: vsearch
vsearch
    --fastq_mergepairs {{--fastq_mergepairs}} \
    --reverse {{--reverse}} \
    --fastqout {{--fastqout}} \
    --fastaout {{--fastaout}} \
    --relabel {{--relabel}} \
    --fastq_minlen {{--fastq_minlen}} \
    --fastq_maxee {{--fastq_maxee}} \
    --fastq_maxdiffs {{--fastq_maxdiffs}} \
    --fastq_maxns {{--fastq_maxns}} \

# Step 2.2: relabel pre-merged reads
# Software: usearch
usearch

# Step 3: primer removal & QC
# Software: vsearch
vsearch
    --fastx_filter {{--fastx_filter}} \
    --fastq_stripleft {{--fastq_stripleft}} \
    --fastq_stripright {{--fastq_stripright}} \
    --fastq_maxee_rate {{--fastq_maxee_rate}} \
    --fastaout {{--fastaout}} \
    --fastq_maxlen {{--fastq_maxlen}} \
    --fastq_minlen {{--fastq_minlen}} \
    --fastq_maxns {{--fastq_maxns}} \

# Step 4.1: dereplication
# Software: vsearch
vsearch
    --derep_fulllength {{--derep_fulllength}} \
    --minuniquesize {{--minuniquesize}} \
    --sizeout {{--sizeout}} \
    --relabel {{--relabel}} \
    --output {{--output}} \
    --strand {{--strand}} \

# Step 4.2: ASV clustering (denoise)
# Software: usearch
usearch

# Step 4.3: reference-based chimera removal
# Software: vsearch
vsearch
    --uchime_ref {{--uchime_ref}} \
    --db {{--db}} \
    --threads {{--threads}} \
    --nonchimeras {{--nonchimeras}} \
    --chimeras {{--chimeras}} \
    --abskew {{--abskew}} \
    --relabel {{--relabel}} \
    --sizeout {{--sizeout}} \

# Step 5.1: feature table generation
# Software: vsearch
vsearch
    --usearch_global {{--usearch_global}} \
    --db {{--db}} \
    --id {{--id}} \
    --threads {{--threads}} \
    --otutabout {{--otutabout}} \
    --biomout {{--biomout}} \
    --mothur_shared_out {{--mothur_shared_out}} \
    --strand {{--strand}} \
    --sizeout {{--sizeout}} \
