execpath=$(pwd)/$(dirname $0)
echo execution path $execpath
export PYTHONPATH=$PYTHONPATH:$execpath/tools/:$execpath/tools/lightsim
cd $(dirname $0)/gui/ && python3 workbench.py
