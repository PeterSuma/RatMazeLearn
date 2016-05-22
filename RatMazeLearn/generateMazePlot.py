from __future__ import division
import matplotlib
import matplotlib.pyplot as plt
import pickle
import logging
import os


TraceOn = True

def writePrint ( msg ):
    if TraceOn:
        logging.warning (msg)

osdir = os.getcwd()  # this script is run outside of the jython environment in regular python via the call function...
writePrint ( 'OSDir [%s] .' % ( osdir ) )
if osdir.find('\\') >= 0:
    OSname = 'win'
    graphicsDir = ".\\"
else:
    OSname = 'linux'
    graphicsDir = './'

TrainingGraphFile = graphicsDir + r"MappedMoves.png"
mappingDataFile =  graphicsDir + r"mappingdata.pic"

writePrint ( 'generateMazePlot: Loading saved mapping data file [%s].' %  ( mappingDataFile )) 
mapLoadFileHndl = open(mappingDataFile,'rb')
mappingResults = pickle.load (mapLoadFileHndl) # load the weights variable back into memory (note: determines binary or ASCII mode itself
mapLoadFileHndl.close()

# Structure of mapping results: [x,y, bestMoveActionNumber, learnChoosenActionNumber]
# count only those where the learnmove is not a wall (ie: mappingResults[3] != -1)
accuracyNum = len([ i for i in mappingResults if ((i[2] == i[3]) and i[3] != -1) ]) /  len([ j for j in mappingResults if (j[3] != -1)]) * 100 # count the number of plcaes where the moves are identical

# plot 2 lines; 1 for the best moves and one for the choosenMoves..should be same!! or learning did not work!!
fig1 = plt.figure(1)
fig = plt.gcf()
fig.set_size_inches(6, 1.5)

#plt.xlabel('(x*10+y)')
#plt.ylabel('Move')

plt.yticks( (0, 1, 2, 3, 4, 5, 6, 7), ('Wall', 'Up', 'Down', 'Left', 'Right', 'L-Lever', 'R-Lever') )

plt.plot( [(x[0] * 10) + x[1] for x in mappingResults], [bm[2]+1 for bm in mappingResults], color="b", label='BestMove')  # best move
plt.plot( [(x[0] * 10) + x[1] for x in mappingResults], [cm[3]+1 for cm in mappingResults], color="r", label=('LearnMove ' + '{0:.2f}%'.format(accuracyNum)) )  # moves choosen
plt.legend(fontsize='xx-small', frameon=False, borderpad=0, labelspacing=0.1)
plt.savefig(TrainingGraphFile)
writePrint ( 'generateMazePlot: Saved graph to file [%s].' %  ( TrainingGraphFile )) 
