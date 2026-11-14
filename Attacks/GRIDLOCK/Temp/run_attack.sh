#!/bin/bash
# run_attack.sh -- runs the jtop power logger, an GPU cache attack, and vlm_webcam.py for fixed duration, for ONE model and ONE condition
#
# Usage:
#   ./run_attack.sh <normal|evict|pin|scan> <duration_seconds> <ollama_model> [run_number]
#
# Examples:
#   ./run_attack.sh normal 60 minicpm-v4.6:latest 1
#   ./run_attack.sh pin    60 moondream:latest    3
#
# EDIT THESE TO MATCH THIS SPECIFIC BOARD 
JTOP_SCRIPT="./jetson_log.py"       #jtop power logging script
VLM_SCRIPT="./vlm_webcam.py"
THRASH_BIN="./gpu_cache_thrash"
GPU_CLOCK_MHZ=1300                  # do sudo jetson_clocks --show (GPU CurrentFreq / 1e6) -- BOARD-SPECIFIC
BOARD="orin"                        # "orin" or "nano" 
VIDEO_SOURCE="./recorded_input.avi" # recorded video for controlled, repeatable input # leave empty ("") to use the live camera instead

MODE="$1"
DURATION="${2:-60}" # 60 seconds run 
MODEL="${3:-minicpm-v4.6:latest}" 
RUN_NUM="${4:-1}"

if [ -z "$MODE" ]; then
    echo "Usage: $0 <normal|evict|pin|scan> <duration_seconds> <ollama_model> [run_number]" # format for command 
    exit 1
fi
if [ "$MODE" != "normal" ] && [ "$MODE" != "evict" ] && [ "$MODE" != "pin" ] && [ "$MODE" != "scan" ]; then
    echo "Unknown mode '$MODE'. Use: normal, evict, pin, or scan." # if does not match throw message
    exit 1
fi

# Organize output into results/<board>/<model>/<condition>/ so results from both boards
# Model names often contain ':' which isn't safe in paths, so swap it for '_'.
MODEL_SAFE=$(echo "$MODEL" | tr ':/' '__')
OUT_DIR="results/${BOARD}/${MODEL_SAFE}/${MODE}"
mkdir -p "$OUT_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LABEL="${BOARD}_${MODEL_SAFE}_${MODE}_run${RUN_NUM}_${TIMESTAMP}"

echo "=== Board: $BOARD | Model: $MODEL | Mode: $MODE | Run: $RUN_NUM | Duration: ${DURATION}s ==="

echo "Locking clocks..."
# -n = non-interactive: if sudo isn't already authenticated/cached
# fails first with a warning instead of hanging indefinitely waiting for a password prompt 
# run `sudo -v` (or let run_full_experiment.sh do it once) to avoid this warning firing on every run
if ! sudo -n jetson_clocks 2>/dev/null; then
    echo "WARNING: sudo not pre-authenticated -- skipped clock locking for this run."
    echo "         Run 'sudo -v' before starting, or clocks may not be at max for this run."
fi

echo "Starting power logger..."
# Keep the logger's duration in sync with the VLM's
# attempt to scale the sampling interval for ~ 4 samples regardless of how long DURATION is 
JTOP_INTERVAL=$(python3 -c "print($DURATION / 4)")
JTOP_DURATION="$DURATION" JTOP_INTERVAL="$JTOP_INTERVAL" python3 "$JTOP_SCRIPT" &
JTOP_PID=$!
sleep 2

THRASH_PID=""
if [ "$MODE" == "pin" ]; then
    echo "Starting pin attack..."
    "$THRASH_BIN" pin "$DURATION" "$GPU_CLOCK_MHZ" &
    THRASH_PID=$!
    sleep 1
elif [ "$MODE" == "scan" ]; then
    echo "Starting scan attack..."
    "$THRASH_BIN" scan "$DURATION" 256 &
    THRASH_PID=$!
    sleep 1
fi

echo "Starting VLM workload (foreground, will run for ${DURATION}s)..."
EVICT_FLAG="0"
if [ "$MODE" == "evict" ]; then
    EVICT_FLAG="1"
fi
VLM_EVICT="$EVICT_FLAG" VLM_LABEL="$LABEL" VLM_DURATION="$DURATION" VLM_MODEL="$MODEL" \
    VLM_VIDEO_SOURCE="$VIDEO_SOURCE" python3 "$VLM_SCRIPT"

echo "Cleaning up background processes..."
if [ -n "$THRASH_PID" ]; then
    kill "$THRASH_PID" 2>/dev/null
fi
kill "$JTOP_PID" 2>/dev/null

# locate two raw output files before merging > adjust the jetson_log* glob if jtop script names its output differently
POWER_FILE=$(ls -t jetson_log*.csv 2>/dev/null | head -n 1)
LATENCY_FILE=$(ls -t latency_"${LABEL}"*.csv 2>/dev/null | head -n 1)

if [ -n "$POWER_FILE" ] && [ -n "$LATENCY_FILE" ]; then
    echo "Merging power + latency into one file..."
    python3 merge_logs.py "$POWER_FILE" "$LATENCY_FILE" "${OUT_DIR}/merged_${LABEL}.csv"
fi

# Keep the raw files too (in case the merge needs double-checking later) -- just organized.
mv jetson_log*.csv "$OUT_DIR/" 2>/dev/null
mv latency_"${LABEL}"*.csv "$OUT_DIR/" 2>/dev/null

echo "=== Run complete: $LABEL -> $OUT_DIR ==="
