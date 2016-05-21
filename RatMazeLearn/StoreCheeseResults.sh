cd /home/ctnuser/Pete/ratmaze1

md $1
cp ./*.py $1
cp ./*.pic $1
cp ./*.txt $1
cp ./*.csv $1
cp ./MappedMoves.png $1
cp ./qlearn_decodedMoves.png $1
cp ./log/*.* $1

rm ./*.pic
rm ./*.txt
rm ./*.csv
rm  ./MappedMoves.png
rm ./qlearn_decodedMoves.png
rm ./log/*.*

