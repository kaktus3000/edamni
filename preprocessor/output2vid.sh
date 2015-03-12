#!/usr/bin/bash
#argument: xml base name
echo $1
python3 output2images.py $1.output.txt $1.png $1.frame

ffmpeg -y -r 30 -i $1.frame%04d.png -vcodec h264 $1.video.mkv

rm -f $1.frame*
