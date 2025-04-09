#!/bin/bash
export MESA_GLES_VERSION_OVERRIDE=2.0
export LOG_LEVEL=DEBUG
# Uncomment the below line if you have issues with rendering
#export WEBKIT_DISABLE_COMPOSITING_MODE=1
cd /home/pmos/remote-assist-display/application && pipenv run python main.py