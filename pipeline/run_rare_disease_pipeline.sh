#!/usr/bin/env bash
# run_rare_disease_pipeline.sh
#
# Automated GRCh38 annotation pipeline for:
#   kabuki, sotos, tay_sachs, noonan
#
# Usage:
#   bash pipeline/run_rare_disease_pipeline.sh tay_sachs
#   bash pipeline/run_rare_disease_pipeline.sh tay_sachs --force
#   bash pipeline/run_rare_disease_pipeline.sh all
#
# Main workflow:
#   SNV: bcftools -> VEP 115 -> SnpEff -> ClinVar -> ClinGen -> SpliceAI
#   CNV: AnnotSV + ClassifyCNV + ISV-CNV
#
# Full local gnomAD, ANNOVAR/InterVar, MAVERICK and Horizon are intentionally
# excluded from this low-storage workflow. VEP cache frequencies are retained.

set -Eeuo pipefail
IFS=$'\n\t'

usage() {
    cat <<'USAGE'
Usage:
  bash pipeline/run_rare_disease_pipeline.sh DISEASE [--force]

DISEASE:
  tay_sachs
  kabuki
  sotos
  noonan
  all

Options:
  --force   Remove the existing result folder for the selected disease and rerun.

Examples:
  bash pipeline/run_rare_disease_pipeline.sh tay_sachs
  bash pipeline/run_rare_disease_pipeline.sh tay_sachs --force
  bash pipeline/run_rare_disease_pipeline.sh all
USAGE
}

die() {
    printf '[ERROR] %s\n' "$*" >&2
    exit 1
}

log() {
    printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

need_file() {
    [[ -s "$1" ]] || die "Missing or empty file: $1"
}

need_dir() {
    [[ -d "$1" ]] || die "Missing directory: $1"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

[[ $# -ge 1 && $# -le 2 ]] || {
    usage
    exit 1
}

TARGET="$1"
FORCE=0

if [[ "${2:-}" == "--force" ]]; then
    FORCE=1
elif [[ -n "${2:-}" ]]; then
    die "Unknown option: $2"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
THREADS="${THREADS:-4}"
JAVA_MEM="${JAVA_MEM:-8g}"

DISEASES=(kabuki sotos tay_sachs noonan)

valid_disease() {
    local query="$1"
    local d
    for d in "${DISEASES[@]}"; do
        [[ "$d" == "$query" ]] && return 0
    done
    return 1
}

if [[ "$TARGET" == "all" ]]; then
    for disease in "${DISEASES[@]}"; do
        if [[ "$FORCE" -eq 1 ]]; then
            "$0" "$disease" --force
        else
            "$0" "$disease"
        fi
    done
    exit 0
fi

valid_disease "$TARGET" || {
    usage
    die "Unsupported disease: $TARGET"
}

DISEASE="$TARGET"

# ------------------------- Project paths -------------------------

SNV_INPUT_REL="input/snv/synthetic_${DISEASE}_small_variants_GRCh38_unannotated.vcf"
CNV_INPUT_REL="input/cnv/synthetic_${DISEASE}_cnv_GRCh38_unannotated.bed"

SNV_INPUT="$PROJECT_ROOT/$SNV_INPUT_REL"
CNV_INPUT="$PROJECT_ROOT/$CNV_INPUT_REL"

RESULT_REL="results/$DISEASE"
RESULT_DIR="$PROJECT_ROOT/$RESULT_REL"
WORK_REL="$RESULT_REL/work"
SNV_REL="$RESULT_REL/snv"
CNV_REL="$RESULT_REL/cnv"
FINAL_REL="$RESULT_REL/final"
LOG_REL="$RESULT_REL/logs"

WORK_DIR="$PROJECT_ROOT/$WORK_REL"
SNV_DIR="$PROJECT_ROOT/$SNV_REL"
CNV_DIR="$PROJECT_ROOT/$CNV_REL"
FINAL_DIR="$PROJECT_ROOT/$FINAL_REL"
LOG_DIR="$PROJECT_ROOT/$LOG_REL"

REF_REL="resources/reference/hg38.fa"
VEP_CACHE_REL="resources/vep_cache"
SNPEFF_DATA_REL="resources/snpeff_data/data"
CLINVAR_REL="resources/clinvar/clinvar.chr.vcf.gz"
CLINGEN_REL="resources/clingen/clingen_dosage.hg38.bed.gz"
ANNOTSV_ANNOTATIONS_REL="resources/annotsv_annotations/AnnotSV_annotations"
CLASSIFYCNV_REL="tools/ClassifyCNV"

REF="$PROJECT_ROOT/$REF_REL"
VEP_CACHE="$PROJECT_ROOT/$VEP_CACHE_REL"
SNPEFF_DATA="$PROJECT_ROOT/$SNPEFF_DATA_REL"
CLINVAR="$PROJECT_ROOT/$CLINVAR_REL"
CLINGEN="$PROJECT_ROOT/$CLINGEN_REL"
ANNOTSV_ANNOTATIONS="$PROJECT_ROOT/$ANNOTSV_ANNOTATIONS_REL"
CLASSIFYCNV_DIR="$PROJECT_ROOT/$CLASSIFYCNV_REL"

CORE_SIF="$PROJECT_ROOT/containers/core_tools.sif"
VEP_SIF="$PROJECT_ROOT/containers/vep_release115.sif"
SNPEFF_SIF="$PROJECT_ROOT/containers/snpeff.sif"
SPLICEAI_SIF="$PROJECT_ROOT/containers/spliceai.sif"
ANNOTSV_SIF="$PROJECT_ROOT/containers/annotsv.sif"
ISV_SIF="$PROJECT_ROOT/containers/isv.sif"

SNPEFF_DB="GRCh38.mane.1.2.ensembl"

# ------------------------- Preflight checks -------------------------

need_file "$SNV_INPUT"
need_file "$CNV_INPUT"

need_file "$CORE_SIF"
need_file "$VEP_SIF"
need_file "$SNPEFF_SIF"
need_file "$SPLICEAI_SIF"
need_file "$ANNOTSV_SIF"
need_file "$ISV_SIF"

need_file "$REF"
need_file "${REF}.fai"
need_dir "$VEP_CACHE"
need_dir "$SNPEFF_DATA"
need_file "$CLINVAR"
need_file "${CLINVAR}.tbi"
need_file "$CLINGEN"
need_file "${CLINGEN}.tbi"
need_dir "$ANNOTSV_ANNOTATIONS"
need_file "$CLASSIFYCNV_DIR/ClassifyCNV.py"

command -v apptainer >/dev/null 2>&1 || die "Apptainer is not available in PATH"

if [[ -e "$RESULT_DIR" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
        rm -rf "$RESULT_DIR"
    else
        die "Result folder already exists: $RESULT_DIR. Use --force to rerun."
    fi
fi

mkdir -p "$WORK_DIR" "$SNV_DIR" "$CNV_DIR" "$FINAL_DIR" "$LOG_DIR"

LOGFILE="$LOG_DIR/${DISEASE}.pipeline.log"
exec > >(tee -a "$LOGFILE") 2>&1

CORE=(apptainer exec --bind "$PROJECT_ROOT:/project" "$CORE_SIF")
VEP=(apptainer exec --bind "$PROJECT_ROOT:/project" "$VEP_SIF")
SNPEFF=(apptainer exec --bind "$PROJECT_ROOT:/project" "$SNPEFF_SIF")
SPLICEAI=(apptainer exec --bind "$PROJECT_ROOT:/project" "$SPLICEAI_SIF")
ANNOTSV=(apptainer exec --bind "$PROJECT_ROOT:/project" "$ANNOTSV_SIF")
ISV=(apptainer exec --bind "$PROJECT_ROOT:/project" "$ISV_SIF")

log "Starting pipeline for: $DISEASE"
log "Project root: $PROJECT_ROOT"
log "Threads: $THREADS"
log "SNV input: $SNV_INPUT"
log "CNV input: $CNV_INPUT"

# Confirm that the expected SnpEff and SnpSift jars exist inside the container.
"${SNPEFF[@]}" test -s /opt/snpEff/snpEff.jar \
    || die "Missing /opt/snpEff/snpEff.jar inside snpeff.sif"
"${SNPEFF[@]}" test -s /opt/snpEff/SnpSift.jar \
    || die "Missing /opt/snpEff/SnpSift.jar inside snpeff.sif"

# Validate the input CNV BED again before running CNV tools.
awk '
BEGIN { errors=0; rows=0 }
{
    rows++
    if (NF != 4) errors++
    if ($1 !~ /^chr/) errors++
    if ($2 !~ /^[0-9]+$/ || $3 !~ /^[0-9]+$/) errors++
    if (($2 ~ /^[0-9]+$/) && ($3 ~ /^[0-9]+$/) && $3 <= $2) errors++
    if ($4 != "DEL" && $4 != "DUP") errors++
}
END {
    if (rows == 0 || errors > 0) exit 1
}
' "$CNV_INPUT" || die "CNV BED validation failed: $CNV_INPUT"

# =================================================================
# SNV / small-indel branch
# =================================================================

RAW_REL="$WORK_REL/${DISEASE}.input.vcf.gz"
NORM_REL="$WORK_REL/${DISEASE}.normalized.vcf.gz"
VEP_OUT_REL="$SNV_REL/${DISEASE}.vep.vcf.gz"
SNPEFF_OUT_REL="$SNV_REL/${DISEASE}.vep.snpeff.vcf.gz"
CLINVAR_OUT_REL="$SNV_REL/${DISEASE}.vep.snpeff.clinvar.vcf.gz"
CLINGEN_OUT_REL="$SNV_REL/${DISEASE}.vep.snpeff.clinvar.clingen.vcf.gz"
SPLICEAI_RAW_REL="$WORK_REL/${DISEASE}.spliceai.raw.vcf"
SPLICEAI_OUT_REL="$SNV_REL/${DISEASE}.vep.snpeff.clinvar.clingen.spliceai.vcf.gz"
FINAL_SNV_REL="$FINAL_REL/${DISEASE}.final.small_variants.annotated.vcf.gz"

RAW="$PROJECT_ROOT/$RAW_REL"
NORM="$PROJECT_ROOT/$NORM_REL"
VEP_OUT="$PROJECT_ROOT/$VEP_OUT_REL"
SNPEFF_OUT="$PROJECT_ROOT/$SNPEFF_OUT_REL"
CLINVAR_OUT="$PROJECT_ROOT/$CLINVAR_OUT_REL"
CLINGEN_OUT="$PROJECT_ROOT/$CLINGEN_OUT_REL"
SPLICEAI_RAW="$PROJECT_ROOT/$SPLICEAI_RAW_REL"
SPLICEAI_OUT="$PROJECT_ROOT/$SPLICEAI_OUT_REL"
FINAL_SNV="$PROJECT_ROOT/$FINAL_SNV_REL"

log "SNV step 1/6: bgzip and index the original VCF"
"${CORE[@]}" bgzip -c "/project/$SNV_INPUT_REL" > "$RAW"
"${CORE[@]}" tabix -f -p vcf "/project/$RAW_REL"

log "SNV step 2/6: normalize and split multiallelic records"
"${CORE[@]}" bcftools norm \
    -f "/project/$REF_REL" \
    -m -any \
    -c x \
    -Oz \
    -o "/project/$NORM_REL" \
    "/project/$RAW_REL"
"${CORE[@]}" tabix -f -p vcf "/project/$NORM_REL"

INPUT_COUNT=$("${CORE[@]}" bcftools view -H "/project/$RAW_REL" | wc -l)
NORM_COUNT=$("${CORE[@]}" bcftools view -H "/project/$NORM_REL" | wc -l)
log "Input variant records: $INPUT_COUNT"
log "Normalized variant records: $NORM_COUNT"

log "SNV step 3/6: VEP 115 offline annotation"
"${VEP[@]}" vep \
    --input_file "/project/$NORM_REL" \
    --output_file "/project/$VEP_OUT_REL" \
    --format vcf \
    --vcf \
    --compress_output bgzip \
    --force_overwrite \
    --species homo_sapiens \
    --assembly GRCh38 \
    --cache \
    --offline \
    --dir_cache "/project/$VEP_CACHE_REL" \
    --fasta "/project/$REF_REL" \
    --fork "$THREADS" \
    --everything \
    --af_gnomade \
    --af_gnomadg \
    --max_af \
    --symbol \
    --canonical \
    --mane \
    --hgvs \
    --numbers \
    --protein \
    --biotype
"${CORE[@]}" tabix -f -p vcf "/project/$VEP_OUT_REL"

log "SNV step 4/6: SnpEff consequence annotation"
"${SNPEFF[@]}" java -Xmx"$JAVA_MEM" \
    -jar /opt/snpEff/snpEff.jar ann \
    -noStats \
    -canon \
    -hgvs \
    -dataDir "/project/$SNPEFF_DATA_REL" \
    "$SNPEFF_DB" \
    "/project/$VEP_OUT_REL" \
    | "${CORE[@]}" bgzip -c > "$SNPEFF_OUT"
"${CORE[@]}" tabix -f -p vcf "/project/$SNPEFF_OUT_REL"

log "SNV step 5/6: ClinVar and ClinGen annotations"
"${SNPEFF[@]}" java -Xmx"$JAVA_MEM" \
    -jar /opt/snpEff/SnpSift.jar annotate \
    -id \
    -info "CLNSIG,CLNREVSTAT,CLNDN,CLNDISDB,CLNHGVS,CLNVC,CLNVCSO,GENEINFO" \
    "/project/$CLINVAR_REL" \
    "/project/$SNPEFF_OUT_REL" \
    | "${CORE[@]}" bgzip -c > "$CLINVAR_OUT"
"${CORE[@]}" tabix -f -p vcf "/project/$CLINVAR_OUT_REL"

CLINGEN_HEADER="$WORK_DIR/clingen.header.txt"
cat > "$CLINGEN_HEADER" <<'HDR'
##INFO=<ID=CLINGEN_REGION,Number=.,Type=String,Description="ClinGen dosage sensitivity region or gene">
##INFO=<ID=CLINGEN_HAPLO,Number=.,Type=String,Description="ClinGen haploinsufficiency score">
##INFO=<ID=CLINGEN_TRIPLO,Number=.,Type=String,Description="ClinGen triplosensitivity score">
HDR

"${CORE[@]}" bcftools annotate \
    -a "/project/$CLINGEN_REL" \
    -h "/project/$WORK_REL/clingen.header.txt" \
    -c CHROM,FROM,TO,INFO/CLINGEN_REGION,INFO/CLINGEN_HAPLO,INFO/CLINGEN_TRIPLO \
    -Oz \
    -o "/project/$CLINGEN_OUT_REL" \
    "/project/$CLINVAR_OUT_REL"
"${CORE[@]}" tabix -f -p vcf "/project/$CLINGEN_OUT_REL"

log "SNV step 6/6: standalone SpliceAI annotation"
"${SPLICEAI[@]}" spliceai \
    -I "/project/$CLINGEN_OUT_REL" \
    -O "/project/$SPLICEAI_RAW_REL" \
    -R "/project/$REF_REL" \
    -A grch38

"${CORE[@]}" bgzip -c "/project/$SPLICEAI_RAW_REL" > "$SPLICEAI_OUT"
"${CORE[@]}" tabix -f -p vcf "/project/$SPLICEAI_OUT_REL"

cp -f "$SPLICEAI_OUT" "$FINAL_SNV"
cp -f "${SPLICEAI_OUT}.tbi" "${FINAL_SNV}.tbi"

FINAL_COUNT=$("${CORE[@]}" bcftools view -H "/project/$FINAL_SNV_REL" | wc -l)
log "Final annotated SNV records: $FINAL_COUNT"
log "Final SNV output: $FINAL_SNV"

# =================================================================
# CNV branch
# =================================================================

ANNOTSV_OUT_REL="$CNV_REL/${DISEASE}.AnnotSV.tsv"
ANNOTSV_OUT="$PROJECT_ROOT/$ANNOTSV_OUT_REL"
CLASSIFY_OUT_REL="$CNV_REL/${DISEASE}.ClassifyCNV"
CLASSIFY_OUT="$PROJECT_ROOT/$CLASSIFY_OUT_REL"
ISV_INPUT_REL="$WORK_REL/${DISEASE}.isv.headered.bed"
ISV_INPUT="$PROJECT_ROOT/$ISV_INPUT_REL"
ISV_OUT_REL="$CNV_REL/${DISEASE}.ISV_with_SHAP.tsv"
ISV_OUT="$PROJECT_ROOT/$ISV_OUT_REL"
FINAL_CNV_SUMMARY="$FINAL_DIR/${DISEASE}.final.cnv.summary.tsv"

log "CNV step 1/3: AnnotSV"
"${ANNOTSV[@]}" AnnotSV \
    -SVinputFile "/project/$CNV_INPUT_REL" \
    -outputFile "/project/$ANNOTSV_OUT_REL" \
    -genomeBuild GRCh38 \
    -svtBEDcol 4 \
    -annotationsDir "/project/$ANNOTSV_ANNOTATIONS_REL" \
    > "$LOG_DIR/${DISEASE}.AnnotSV.stdout.log" \
    2> "$LOG_DIR/${DISEASE}.AnnotSV.stderr.log"

need_file "$ANNOTSV_OUT"

log "CNV step 2/3: ClassifyCNV"
if ! "${CORE[@]}" bash -lc "
    cd '/project/$CLASSIFYCNV_REL'
    python3 ClassifyCNV.py \
        --infile '/project/$CNV_INPUT_REL' \
        --GenomeBuild hg38 \
        --cores '$THREADS' \
        --precise \
        --outdir '/project/$CLASSIFY_OUT_REL'
"; then
    log "ClassifyCNV did not run inside core_tools.sif; trying the tested host installation"
    (
        cd "$CLASSIFYCNV_DIR"
        python3 ClassifyCNV.py \
            --infile "$CNV_INPUT" \
            --GenomeBuild hg38 \
            --cores "$THREADS" \
            --precise \
            --outdir "$CLASSIFY_OUT"
    )
fi

need_dir "$CLASSIFY_OUT"

log "CNV step 3/3: ISV-CNV with probability and SHAP values"
{
    printf 'chromosome\tstart\tend\tcnv_type\n'
    cat "$CNV_INPUT"
} > "$ISV_INPUT"

"${ISV[@]}" python3 - "/project/$ISV_INPUT_REL" "/project/$ISV_OUT_REL" <<'PY'
import sys
import pandas as pd
from isv import isv

input_bed, output_tsv = sys.argv[1], sys.argv[2]
cnvs = pd.read_csv(input_bed, sep="\t")
result = isv(cnvs=cnvs, proba=True, shap=True, threshold=0.95)
result.to_csv(output_tsv, sep="\t", index=False)
print(f"ISV-CNV output: {output_tsv}")
PY

need_file "$ISV_OUT"

# Create a compact final CNV manifest. The tool outputs remain separate because
# AnnotSV can contain multiple gene-level lines for a single CNV.
{
    printf 'disease\tchromosome\tstart\tend\tcnv_type\tAnnotSV_output\tClassifyCNV_directory\tISV_output\n'
    awk -v disease="$DISEASE" \
        -v annotsv="$ANNOTSV_OUT_REL" \
        -v classify="$CLASSIFY_OUT_REL" \
        -v isv="$ISV_OUT_REL" \
        'BEGIN{OFS="\t"} {print disease,$1,$2,$3,$4,annotsv,classify,isv}' \
        "$CNV_INPUT"
} > "$FINAL_CNV_SUMMARY"

log "Final CNV summary: $FINAL_CNV_SUMMARY"

# =================================================================
# Final report
# =================================================================

REPORT="$FINAL_DIR/${DISEASE}.pipeline_outputs.txt"
{
    echo "Disease: $DISEASE"
    echo "Assembly: GRCh38"
    echo
    echo "Input SNV VCF: $SNV_INPUT"
    echo "Input CNV BED: $CNV_INPUT"
    echo
    echo "Final annotated SNV VCF: $FINAL_SNV"
    echo "Final annotated SNV index: ${FINAL_SNV}.tbi"
    echo
    echo "AnnotSV output: $ANNOTSV_OUT"
    echo "ClassifyCNV output directory: $CLASSIFY_OUT"
    echo "ISV-CNV output: $ISV_OUT"
    echo "Final CNV summary: $FINAL_CNV_SUMMARY"
    echo
    echo "Pipeline log: $LOGFILE"
} > "$REPORT"

log "Pipeline completed successfully for: $DISEASE"
log "Output report: $REPORT"
