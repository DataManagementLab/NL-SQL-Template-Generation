#!/bin/bash

set -e

if [[ "$1" == "ubuntu" ]]; then
		sudo apt install python3 python3-virtualenv python3-dev build-essential
fi

virtualenv --python=python3.7 env
source env/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

py_script="
import nltk
nltk.download('punkt')
"

python -c "$py_script"

export PYTHONPATH="${PYTHONPATH}:$(pwd)"
mkdir logs