#!/bin/bash
set -e

# =============================================================================
# Environment setup for 16S/ITS ASV pipeline
# Tools: vsearch (conda), usearch (manual)
# =============================================================================

WORK_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_PATH="${WORK_DIR}/bioinfo_env"

echo "=== Creating conda environment ==="
conda env create -p "${ENV_PATH}" -f environment.yml

echo ""
echo "=== Conda environment created at: ${ENV_PATH} ==="
echo "To activate: conda activate ${ENV_PATH}"
echo ""

# -----------------------------------------------------------------------------
# Note: usearch is NOT installed automatically (commercial software).
# See MANUAL.md for download and installation instructions.
#
# ⚠️ usearch is x86_64 only. On Apple Silicon (M1/M2/M3), run via Rosetta 2:
#    arch -x86_64 /path/to/usearch <args>
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Download reference database for chimera checking (Step 6)
# -----------------------------------------------------------------------------
echo "=== Downloading SILVA 16S reference database ==="
DB_DIR="${WORK_DIR}/databases"
mkdir -p "${DB_DIR}"

SILVA_URL="https://www.arb-silva.de/fileadmin/silva_databases/current/Exports/Release_164_1/SILVA_138.1_SSURef_NR99_tax_silva_trunc.fasta.gz"
echo "Downloading SILVA SSURef NR99 (truncated)..."
echo "URL: ${SILVA_URL}"
echo ""
echo "If download fails, manually download from:"
echo "  https://www.arb-silva.de/no_cache/download/archive/current/"
echo "and place the file in: ${DB_DIR}/"
echo ""

# Uncomment to auto-download:
# curl -L -o "${DB_DIR}/silva_ref.fasta.gz" "${SILVA_URL}"
# gunzip "${DB_DIR}/silva_ref.fasta.gz"
# mv "${DB_DIR}/silva_ref.fasta" "${DB_DIR}/silva_16S_ref.fa"

echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Install usearch manually (see MANUAL.md)"
echo "  2. Download reference database if not done above"
echo "  3. Run the pipeline"
