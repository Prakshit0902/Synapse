#!/bin/bash

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' 

echo "" 
echo -e "${GREEN}      [SYNAPSE] Powering Naina AI - Desktop Edition${NC}"
echo -e "${GREEN}      Environment: Linux Native DAEMON Init...${NC}"
echo -e 
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment 'venv' not found!"
    echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "[SYSTEM] Activating Python Virtual Environment..."
source venv/bin/activate

echo "[SYSTEM] Booting Synapse Core..."
echo ""

python3 main.py