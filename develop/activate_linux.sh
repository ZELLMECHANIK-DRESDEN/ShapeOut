#!/bin/bash
# Source this script to get the python environment ready:
# source activate_env.sh
DIRECTORY="env_shapeout"

echo "---------------------------------------------------------"
echo "Make sure you dclab checked out in the parent directory:"
echo "   https://github.com/ZellMechanik-Dresden/dclab.git"
echo "---------------------------------------------------------"
echo "Make sure you have the following packages installed:"
echo "   python-numpy python-opencv python-wxgtk2.8"
echo "---------------------------------------------------------"

## who am i? ##
_script="$(readlink -f ${BASH_SOURCE[0]})"
## Delete last component from $_script ##
_base="$(dirname $_script)"
cd $_base

if [ ! -d $DIRECTORY ]; then
    virtualenv --system-site-packages $DIRECTORY
    source "$DIRECTORY/bin/activate"
    #pip install pyinstaller==2.0
    pip install git+git://github.com/pyinstaller/pyinstaller.git@779d07b236a943a4bf9d2b1a0ae3e0ebcc914798
    pip install nptdms
    pip install statsmodels==0.6.1
    pip install kiwisolver
    #deactivate
    
    # register dclab
    ln -s "../../../../../../dclab/dclab" "$DIRECTORY/lib/python2.7/site-packages"

fi

source "${_base}/${DIRECTORY}/bin/activate"

cd ..
