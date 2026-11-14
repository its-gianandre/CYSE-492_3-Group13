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

