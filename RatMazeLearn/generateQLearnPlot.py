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
    graphicsDir = "F:\\Peter\\Dropbox\\CS 750 - Eliasmith\\Project\\Solution\\"
else:
    OSname = 'linux'
    graphicsDir = '/home/ctnuser/Pete/ratmaze1/'

mazeX = 10
mazeY = 10

TotalCells = ( mazeX + 1 ) * (mazeY + 1)

TrainingGraphFile = graphicsDir + r"qlearn_decodedMoves.png"
mappingDataFile =  graphicsDir + r"qlearn_data.pic"
csvFile =  graphicsDir + r"qlearn_data.csv"

writePrint ( 'generateMazePlot: Loading saved mapping data file [%s].' %  ( mappingDataFile )) 
mapLoadFileHndl = open(mappingDataFile,'rb')
mappingResults = pickle.load (mapLoadFileHndl) # load the weights variable back into memory (note: determines binary or ASCII mode itself
mapLoadFileHndl.close()
 
# Structure of mapping results: [x,y, bestMoveActionNumber, qlearnChoosenActionNumber]
accuracyNum = len([ i for i in mappingResults if round(i[2], 0) == round(i[3], 0) and i[3] != -1]) /  len([ j for j in mappingResults if (j[3] != -1)]) * 100 # count the number of plcaes where the moves are identical

# plot 2 lines; 1 for the best moves and one for the choosenMoves..should be same!! or learning did not work!!
fig1 = plt.figure(1)
fig = plt.gcf()
fig.set_size_inches(6, 1.5)

#plt.xlabel('(x*10+y)')
#plt.ylabel('Move')

plt.yticks( (0, 1, 2, 3, 4, 5, 6, 7), ('Wall', 'Up', 'Down', 'Left', 'Right', 'L-Lever', 'R-Lever') )

#  learnActions.append([ x, y, bnm[2], qLearn_action])

plt.plot( [(x[0] * mazeY) + x[1] for x in mappingResults], [bm[2]+1 for bm in mappingResults], color="b", label="BestMove")  # best move ; the plus one is to allow 0 row to be wall movement (see graph)
plt.plot( [(x[0] * mazeY) + x[1] for x in mappingResults], [qm[3]+1 for qm in mappingResults], color="r", label=('qLearnMove ' + '{0:.2f}%'.format(accuracyNum)) )  # qlearn moves choosen
plt.legend(fontsize='xx-small', frameon=False, borderpad=0, labelspacing=0.1)
plt.savefig(TrainingGraphFile)
writePrint ( 'generateQLearnPlot: Saved graph to file [%s].' %  ( TrainingGraphFile ))

import csv
with open(csvFile, 'wb') as csvfileHndl:
    spamwriter = csv.writer(csvfileHndl, dialect='excel', quoting=csv.QUOTE_MINIMAL)
    for i in range(len(mappingResults)):
        spamwriter.writerow( mappingResults[i] )
    csvfileHndl.close
    
