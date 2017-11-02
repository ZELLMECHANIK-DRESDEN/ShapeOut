#!/bin/bash
# Source this script to get the python environment ready:
# source activate_env.sh
DIRECTORY=".env_shapeout"

echo "------------------------------------------------------------------"
echo "Make sure you dclab and fcswrite are checked out in the parent directory:"
echo "   https://github.com/ZELLMECHANIK-DRESDEN/dclab.git"
echo "   https://github.com/ZELLMECHANIK-DRESDEN/fcswrite.git"
echo "------------------------------------------------------------------"
echo "Make sure you have the following packages installed:"
echo "   python-chaco python-numpy python-scipy python-wxgtk2.8 r-base r-recommended"
echo "------------------------------------------------------------------"

## old dir ##
_old="$(pwd)"
## who am i? ##
_script="$(readlink -f ${BASH_SOURCE[0]})"
## Delete last component from $_script ##
_base="$(dirname $_script)"
cd $_base

if [ ! -d $DIRECTORY ]; then
    virtualenv --system-site-packages $DIRECTORY
    source "$DIRECTORY/bin/activate"
    pip install git+git://github.com/pyinstaller/pyinstaller.git@779d07b236a943a4bf9d2b1a0ae3e0ebcc914798
    pip install nptdms
    pip install statsmodels==0.6.1
    pip install kiwisolver
    pip install pyper
    pip install imageio
    pip install appdirs
    pip install simplejson

    # install dclab and fcswrite
    cd ../../fcswrite
    pip install -e .
    cd $_base
    cd ../../dclab
    pip install -e .

	# install lme4 package
	R -e "install.packages('lme4', repos='http://cran.r-project.org')"
fi

source "${_base}/${DIRECTORY}/bin/activate"

cd $_old

