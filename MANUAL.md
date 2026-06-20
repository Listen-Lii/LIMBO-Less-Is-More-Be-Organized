# Manual Installation Guide

## usearch (Steps 2 & 5)

**Purpose:** Sequence relabeling (`-fastx_relabel`) and ASV denoising (`-unoise3`)

**Download:** https://www.drive5.com/usearch/download.html

**Installation:**

1. Download the appropriate binary for your platform
2. Make it executable:
   ```bash
   chmod +x usearch*.osx   # macOS
   chmod +x usearch*.linux # Linux
   ```
3. Move to a directory in your PATH, or create a symlink:
   ```bash
   sudo ln -s /path/to/usearch /usr/local/bin/usearch
   ```

**Verify installation:**
```bash
usearch --version
```

> ⚠️ **Apple Silicon (M1/M2/M3) users:** usearch is **x86_64 only**. You must run it through Rosetta 2:
> ```bash
> arch -x86_64 /path/to/usearch <args>
> ```
> Ensure Rosetta 2 is installed:
> ```bash
> softwareupdate --install-rosetta
> ```

---

## Reference Database (Step 6: Chimera Removal)

**Purpose:** Reference database for `vsearch --uchime_ref`

### Option 1: SILVA 16S (Bacterial/Archaeal)

**Download:** https://www.arb-silva.de/no_cache/download/archive/current/

Recommended file: `SILVA_138.1_SSURef_NR99_tax_silva_trunc.fasta.gz`

```bash
# Download and extract
curl -L -o silva_ref.fasta.gz "https://www.arb-silva.de/fileadmin/silva_databases/current/Exports/Release_164_1/SILVA_138.1_SSURef_NR99_tax_silva_trunc.fasta.gz"
gunzip silva_ref.fasta.gz
mv SILVA_138.1_SSURef_NR99_tax_silva_trunc.fasta silva_16S_ref.fa
```

### Option 2: UNITE (Fungal ITS)

**Download:** https://unite.ut.ee/repository.php

Choose "SHs general release" FASTA file for your region (e.g., all eukaryotes).

```bash
# After download, rename for pipeline use
mv unite_sh_general_release_*.fasta unite_sh_general_release.fasta
```

---

## Summary

| Item | Type | Auto-install? | Notes |
|------|------|---------------|-------|
| usearch | Binary | ❌ Manual | x86_64 only, Rosetta 2 required on ARM64 |
| SILVA 16S ref DB | Database | ❌ Manual | ~50 MB compressed |
| UNITE ITS ref DB (optional) | Database | ❌ Manual | For fungal workflows |
