for folder in database/*
do
  echo "Processing folder $folder..."

  for f in $folder/*.bcd
  do
    echo "Processing file $f..."
    # take action on each file. $f store current file name

    python3 importBCD.py $f "$folder/`basename $f .bcd`.xml"
    rm $f
  done
done 
