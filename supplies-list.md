# pipeline checklist

| step | description | software | option/etc. | input | output | check | method |
| ---- | ----------- | -------- | ----------- | ----- | ------ | ----- | ------ |
| 1 | merge paired-end reads | vsearch | --fastq_mergepairs | paired FASTQ (R1/R2) | merged FASTQ | yes | conda |
| 2 | relabel merged sequences | usearch | -fastx_relabel | merged FASTQ | relabeled FASTQ | yes | manual:https://www.drive5.com/usearch/download.html |
| 3 | primer trimming and quality filtering | vsearch | --fastx_filter | relabeled FASTQ | filtered FASTQ | yes | conda |
| 4 | dereplication | vsearch | --derep_fulllength | filtered FASTQ | dereplicated FASTQ | yes | conda |
| 5 | ASV clustering (denoising) | usearch | -unoise3 | dereplicated FASTQ | ZOTU FASTA | yes | manual:https://www.drive5.com/usearch/download.html |
| 6 | chimera removal (reference-based) | vsearch | --uchime_ref | ZOTU FASTA | non-chimeric FASTA | yes | conda |
| 7 | sequence alignment and OTU table generation | vsearch | --usearch_global | filtered FASTQ + ZOTU FASTA | feature table (OTU table) | yes | conda |

## dependencies

| database | purpose | download |
|----------|---------|---------|
| silva_16S_ref.fa | reference database for chimera detection (--uchime_ref) | https://www.arb-silva.de/no_cache/download/archive/current/ |
| unite_sh_general_release.fasta | fungal ITS reference (optional, for ITS workflows) | https://unite.ut.ee/repository.php |

## pipeline connectivity

```
┌─────────────────┐
│  Paired FASTQ   │
│  (R1 + R2)      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Step 1: vsearch --fastq_mergepairs      │
│ Merge paired-end reads                  │
└────────┬────────────────────────────────┘
         │ merged FASTQ
         ▼
┌─────────────────────────────────────────┐
│ Step 2: usearch -fastx_relabel          │
│ Relabel merged sequences                │
└────────┬────────────────────────────────┘
         │ relabeled FASTQ
         ▼
┌─────────────────────────────────────────┐
│ Step 3: vsearch --fastx_filter          │
│ Primer trimming + quality filtering     │
└────────┬────────────────────────────────┘
         │ filtered FASTQ
         ▼
┌─────────────────────────────────────────┐
│ Step 4: vsearch --derep_fulllength      │
│ Dereplication                           │
└────────┬────────────────────────────────┘
         │ dereplicated FASTQ
         ▼
┌─────────────────────────────────────────┐
│ Step 5: usearch -unoise3                │
│ ASV clustering / denoising              │
└────────┬────────────────────────────────┘
         │ ZOTU FASTA (representative sequences)
         ▼
┌─────────────────────────────────────────┐
│ Step 6: vsearch --uchime_ref            │
│ Chimera removal (vs. reference DB)      │
│ Input: ZOTU FASTA + silva_16S_ref.fa    │
└────────┬────────────────────────────────┘
         │ non-chimeric FASTA (final ASV table)
         ▼
┌─────────────────────────────────────────┐
│ Step 7: vsearch --usearch_global        │
│ Map filtered reads → ASV representatives│
│ Input: filtered FASTQ + ZOTU FASTA      │
└────────┬────────────────────────────────┘
         │ feature table (OTU/ASV abundance table)
         ▼
┌─────────────────┐
│  OTU Table      │
│  (.uc / .biom)  │
└─────────────────┘
```
