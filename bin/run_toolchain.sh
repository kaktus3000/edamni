#argument: base filename
echo "base filename $1"

python3 ../preprocessor/xml2list.py $1.xml $1.elems.txt
echo "test"
python3 ../preprocessor/list2img.py $1.elems.txt $1.png

./simu $1.elems.txt $1.tsp.txt $1.output.txt

echo "mache bilder fuer video..."
python3 ../preprocessor/output2images.py $1.output.txt $1.png $1.frame

avconv -y -r 30 -i $1.frame%04d.png -vcodec h264 $1.video.mkv

rm -f $1.frame*
