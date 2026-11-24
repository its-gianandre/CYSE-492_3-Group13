# GRIDLOCK Attack

## Directory:
[GRIDLOCK Attacks](./GRIDLOCK/)

[Experiment Data](./CSV_Data/)

[Documentation](./Notebooks/)

## Summary
Research Regarding the effectiveness of Cache Eviction based attacks on Visual Learning Models (VLMs) and Visual Language Action (VLA) Models running on NVIDIA Graphics Processing Units (GPUs). VLMs are attacked as stand alone models and while integrated to make robot motion decisions. A VLA model is attacked while making decisions to control robot motion.

## Hardware/Software Requirements
### Hardware
NVIDIA Jetson AGX Orin
* Running Jetson Linux 36.4 (Ubuntu 24.04)

NVIDIA Jeton Orin Nano
* Running Jetson Linux 36.4 (Ubuntu 24.04)

Raspberry Pi 3 Model B+
* Running Ubuntu 22.04
* Used to control the 2nd TurtleBot3

TurtleBot3 Burger (2x)

### Software
* Ollama
* Robot Operating System 2 (ROS 2) Jazzy Jalisco Distro
* Robot Operating System 2 (ROS 2) Humble Hawksbill Distro

#### VLMs
* Moondream
* Qwen3-VL:2B
* MiniCPM-v4.6
* Aeline/Opan
* SmolVLM2-2.2B
* SmolVLM2-256M
* SmolVLM2-500M

#### VLA Model
* SmolVLA-256M

## VLM Setup Section
* First install Ollama
    * Download and install from the instructions here: https://ollama.com/download/linux

* To install the VLMs follow the syntax: 
```bash
ollama run [model]
```
* For the above VLMs:
```bash
ollama run moondream:latest
ollama run qwen3-vl:2b
ollama run aeline/opan
ollama run ahmadwaqar/smolvlm2-2.2b-instruct
ollama run ahmadwaqar/smolvlm2-256m-video:q8_0
ollama run ahmadwaqar/smolvlm2-500m-video
```

## VLA Setup Section

### LiteVLA Initial Setup

This project uses the LiteVLA resources from
[Omega1029/offline-robotcs](https://github.com/Omega1029/offline-robotcs),
including the `smolvlm_turtlebot_action_balanced` adapter for
`HuggingFaceTB/SmolVLM-Base`.

Our ROS 2 integration uses three additional files:

- `vla_model.py`: Loads the base model and adapter and generates action predictions.
- `inference_node.py`: Handles camera input and publishes model predictions through ROS 2.
- `action_controller.py`: Converts predicted actions into robot movement commands.

The following steps cover the initial environment and dependency setup.
Configuration and execution of these three files are covered separately.

### Prerequisites

- NVIDIA Jetson with a CUDA-enabled PyTorch installation compatible with
  its JetPack and Python versions.
- ROS 2 Jazzy.
- Git and Python virtual environment support.
- Internet access to download dependencies and model files.

### 1. Clone the LiteVLA repository

```bash
cd ~
git clone https://github.com/Omega1029/offline-robotcs.git
cd ~/offline-robotcs
```

The adapter used by this project is located at:

```text
~/offline-robotcs/smolvlm_turtlebot_action_balanced
```

### 2. Create a Python environment

Use the system Python to maintain compatibility with ROS 2.
The `--system-site-packages` option provides access to system-installed
ROS 2 packages and PyTorch.

```bash
python3 -m venv --system-site-packages ~/venvs/smolvla
source ~/venvs/smolvla/bin/activate
```

### 3. Install model dependencies

```bash
python -m pip install --upgrade pip

python -m pip install \
  "transformers>=4.49,<5" \
  "peft>=0.18,<0.19" \
  accelerate pillow safetensors
```

### 4. Verify the environment

```bash
source /opt/ros/jazzy/setup.bash
source ~/venvs/smolvla/bin/activate

python - <<'PY'
import torch
import rclpy
from transformers import AutoProcessor
from peft import PeftModel

print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("ROS 2 and model dependencies imported successfully.")
PY
```

For GPU inference, `CUDA available` should print `True`.

Once these checks pass, the environment is ready for configuration of
`vla_model.py`, `inference_node.py`, and `action_controller.py`.


## Robot Operating System / Turtlebot3 Set Up
### For the NVIDIA Jetson AGX Orin and NVIDIA Jetson Orin Nano:
* Follow the instructions from here: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html
* Then follow the instructions for the Quick Start Guide from here: https://docs.robotis.com/docs/systems/turtlebot3/overview/

### For the Raspberry Pi 3 Model B+:
* Follow the instructions from here: https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html
* Then follow the instructions for the Quick Start Guide from here: https://docs.robotis.com/docs/systems/turtlebot3/overview/

## GRIDLOCK
A Cache Eviction based attack on NVIDIA GPUs. The 3 attacks implemented are **GRIDLOCK PIN**, **GRIDLOCK SCAN**, and **GRIDLOCK DDS**

### GRIDLOCK PIN

### GRIDLOCK SCAN

### GRIDLOCK DDS

