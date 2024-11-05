#!/bin/bash

# get venv made
python3 -m pip install virtualenv
if [ -d 'venv/' ]; then
    echo "venv already exists."
else
    echo "venv has been made"
    virtualenv venv
fi

# install requirements inside venv
source venv/Scripts/activate
pip install -r requirements.txt
deactivate
