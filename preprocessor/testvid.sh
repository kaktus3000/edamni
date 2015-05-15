
#argument: xml base name
echo $1

python3 list2img.py $1.elems.txt $1.png
python3 output2images.py $1.output.txt $1.png $1.frame
#ffmpeg -y -r 30 -i $1.frame%04d.png -vcodec h264 $1.video.mkv
avconv -y -r 30 -i $1.frame%04d.png -vcodec h264 $1.video.mkv
