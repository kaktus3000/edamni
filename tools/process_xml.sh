
#argument: xml list
echo $1
python3 xml2list.py $1.xml $1.elems.txt
python3 list2img.py $1.elems.txt $1.png
