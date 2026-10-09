#!/bin/bash
# run_full_experiment.sh -- runs the complete experiment: N models x 4 conditions x REPEATS repeats each 
# run same script on orin and nano 
# just make sure BOARD and GPU_CLOCK_MHZ are set correctly for each
# board inside run_attack.sh before running this on that machine.
MODELS=(
    "ahmadwaqar/smolvlm2-2.2b-instruct:latest"
    "qwen3-vl:2b"
    "minicpm-v4.6:latest"
    "aeline/opan:latest"
    "moondream:latest"
)

CONDITIONS=("normal" "evict" "pin" "scan")
REPEATS=5
DURATION=60          # seconds per run
COOLDOWN=15          # cooldown!!! seconds to idle between runs, letting GPU/model state settle

TOTAL_RUNS=$((${#MODELS[@]} * ${#CONDITIONS[@]} * REPEATS))
RUN_COUNT=0
START_TIME=$(date +%s)

# Lock clocks ONCE here so you can see and respond to the sudo password
# prompt right now -- rather than run_attack.sh silently re-prompting on every single
# one of the 100 runs below...could stall the whole batch unattended if the sudo credential cache expires partway through
echo "Locking clocks for the full experiment..."
sudo jetson_clocks
sudo -v   # refresh the credential cache timestamp right before the long unattended loop starts

echo "=== Full experiment: ${#MODELS[@]} models x ${#CONDITIONS[@]} conditions x ${REPEATS} repeats = ${TOTAL_RUNS} runs ==="
echo "Estimated minimum time: $(( TOTAL_RUNS * (DURATION + COOLDOWN) / 60 )) minutes (excluding model load/startup overhead)"
echo ""

for MODEL in "${MODELS[@]}"; do
    echo ""
    echo "########################################"
    echo "# MODEL: $MODEL"
    echo "########################################"

    # Make sure this model is actually pulled before testing it 
    # missing model would otherwise fail 20 runs in a row (4 conditions x 5 repeats) before you notice.
    if ! ollama list | grep -q "$MODEL"; then
        echo "WARNING: '$MODEL' not found in 'ollama list'. Skipping this model entirely."
        echo "         Run: ollama pull $MODEL"
        continue
    fi

    for CONDITION in "${CONDITIONS[@]}"; do
        for ((RUN=1; RUN<=REPEATS; RUN++)); do
            RUN_COUNT=$((RUN_COUNT + 1))
            ELAPSED=$(($(date +%s) - START_TIME))
            echo ""
            echo "--- Run ${RUN_COUNT}/${TOTAL_RUNS} | Model: $MODEL | Condition: $CONDITION | Repeat: $RUN/$REPEATS | Elapsed so far: ${ELAPSED}s ---"

            ./run_attack.sh "$CONDITION" "$DURATION" "$MODEL" "$RUN"

            echo "Cooling down for ${COOLDOWN}s before next run..."
            sleep "$COOLDOWN"
        done
    done
done

TOTAL_ELAPSED=$(($(date +%s) - START_TIME))
echo ""
echo "=== Experiment complete: ${RUN_COUNT}/${TOTAL_RUNS} runs finished in $((TOTAL_ELAPSED / 60)) minutes ==="
echo "Results organized under: results/<board>/<model>/<condition>/"
