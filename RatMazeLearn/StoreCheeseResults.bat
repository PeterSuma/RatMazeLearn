
F:
cd "F:\\Peter\\Dropbox\\CS 750 - Eliasmith\\Project\\Solution"

md %1
copy *.py %1
copy *.pic %1
copy *.txt %1
copy *.csv %1
copy MappedMoves.png %1
copy qlearn_decodedMoves.png %1
copy .\log\*.* %1

del /Q *.pic
del /Q *.txt
del /Q *.csv
del /Q  MappedMoves.png
del /Q qlearn_decodedMoves.png
del /Q .\log\*.*

exit

