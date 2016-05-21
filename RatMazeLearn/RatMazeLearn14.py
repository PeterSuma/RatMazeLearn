
# Requires Nengo 1.4

from __future__ import division
import nef
import time
import sys
import logging
import timeview
import timeview.components.core as core
import java.lang
import array
import os
from subprocess import call

from ca.nengo.util.impl import NodeThreadPool, NEFGPUInterface

##
## PARAMETERS.......................................................................................................................
##


# Logging parameters...
ttimestamp = time.asctime().replace(':', '-').replace(' ', '-')

OSname = java.lang.System.getProperty("os.name").lower()

print OSname

wallsNone = []
wallsEasy = [ (1,0), (1,1), (1,2), (3,2), (3,3), (3,4), (7,8),(7,9),(9,8) ]  # walls array...for 5 x 5 maze
wallsMedium = [ (1,0),(1,1),(1,2),(2,5),(3,6),(4,6),(4,7),(5,3),(5,4),(6,8),(6,9),(7,2),(7,3),(7,4),(8,5) ]  # medium walls for a 10 x 10 maze
wallsHard = [ (1,0), (1,1), (1,2), (2,2), (2,3), (2,4), (2,5), (2,6), (2,7), (2,8), (4,6), (4,7), (4,8), (4,9), (5,2), (5,3), (5,4), (5,5), (6,2), (6,7), (6,8), (6,9), (7,2), (7,3), (8,5), (9,5) ]  # hard walls array for 10 x 10 maze

# Command line arguments; 
# [0] = name of nengo script "RatMazeLearn.py"
# [1] = a name given to this run ie: "MediumWallsWithQLearn", final results file will be saved with this name as a prefix, so no special characters or spaces
# [2] = "B" or "I" (BatchMode or Interactive[default])
# [3] = "Q" or "-Q" (Qlearn or no QLearn[default])
# [4] = "N" or "E" or "M" or "H" (walls None, Easy[default], Medium or Hard)


RandomTraining = True  # if false then trains on path solutions in order cell by cell for all maze best paths for every open cell in maze

if len(sys.argv) >= 4:
    
    if sys.argv[1] == '':
        runName = 'RatMazeLearn_'
    else:
        runName = sys.argv[1]
    
    if sys.argv[2] == "B":
        runBatch = True
    else:
        runBatch = False
        
    if sys.argv[3] == "Q":
        useQLearn = True
    else:
        useQLearn = False
    
    if sys.argv[4] == "N":
        walls = wallsNone
    elif sys.argv[4] == "M":
        walls = wallsMedium
    elif sys.argv[4] == "H":
        walls = wallsHard
    elif sys.argv[4] == "E":
        walls = wallsEasy
    else:
        walls = wallsHard

    if sys.argv[5] == "R":
        RandomTraining = True
    elif sys.argv[5] == "P":
        RandomTraining = False
    else:
        RandomTraining = True
        
else:
    walls = wallsEasy
    runBatch = False
    useQLearn = False
    runName = 'RatMaze_InteractiveWallsHardNoQLearn'
    
    
OSWin = False
OSLinux = False
OSMac = False

# import nengo python classes
if OSname.find("win")  > -1 :
    
    #NengoDir = "C:\\Anaconda3\\Lib\\site-packages\\nengo"  
    projectdir = "."
    tracedir = ".\\Log"

    NEFCSVdir =  tracedir

    tracefilename = tracedir + '\\RatMaze_learn' + str(ttimestamp) + '_'   # trace files for .txt output of object trace messages...
    NEFCSVFileName = '\\RatMaze_learn' + ttimestamp + '_log.csv'   # CSV Data: logging files for .csv output
    weightsFile = projectdir +  '\\weightsDump.pic'
    
    fileSep = "\\"

    # Number of neurons               
    N_err = 500  # Number of neurons in the error population for the learned termination
    N_default = 500 # number of neurons for all other populations...
    
    learnRate =  5.00000e-05 # values of 5 x 10^-5 to 5 x 10^-7
    train_time = 5 * 60 * 1000  # = minutes * seconds * 1000ms/s ; time training is turned on in ms
    mappingSettleInterval = 100
    
    OSWin = True

elif OSname.find("linux")  > -1  :
    
    #NengoDir = '/home/ctnuser/Pete/nengo' 
    projectdir = './ratmaze1'
    tracedir = './ratmaze1/Log'
    NEFCSVdir =  tracedir

    tracefilename = tracedir + '/RatMaze_learn' + str(ttimestamp) + '_'   # trace files for .txt output of object trace messages...
    NEFCSVFileName = '/RatMaze_learn' + ttimestamp + '_log.csv'   # CSV Data: logging files for .csv output
    weightsFile = projectdir +  '/weightsDump.pic'

    # Number of neurons               
    N_err = 1000  # Number of neurons in the error population for the learned termination
    N_default = 1000 # number of neurons for all other populations...
    learnRate =  5.00000e-05  # values of 5 x 10^-5 to 5 x 10^-7
    
    train_time = 5 * 60 * 1000  # = minutes * seconds * 1000ms/s ; time training is turned on in ms
    mappingSettleInterval = 100
    
    fileSep = "/"

    OSLinux = True

elif OSname.find("mac") > -1 :

    #NengoDir = '/Applications/nengo-e6343ec'
    projectdir = '.'
    tracedir = projectdir + '/Log'
    NEFCSVdir =  tracedir

    tracefilename = tracedir + '/RatMaze_learn' + str(ttimestamp) + '_'   # trace files for .txt output of object trace messages...
    NEFCSVFileName = '/RatMaze_learn' + ttimestamp + '_log.csv'   # CSV Data: logging files for .csv output
    weightsFile = projectdir +  '/weightsDump.pic'

    # Number of neurons               
    N_err = 200  # Number of neurons in the error population for the learned termination
    N_default = 200 # number of neurons for all other populations...
    learnRate =  5.00000e-05  # values of 5 x 10^-5 to 5 x 10^-7
    
    train_time = 1 * 60 * 1000  # = minutes * seconds * 1000ms/s ; time training is turned on in ms
    mappingSettleInterval = 100

    fileSep = "/"
    
    OSMac = True
    
else:
    print 'RatMazeLearn14.py: No mathcing OS found.'
    exit()
    
#sys.path.append(NengoDir)  # should already be in path...
sys.path.append(projectdir)
import TrainSimpleNode
import Maze 


# TraceData : Logger
OneLogger = tracefilename  # set to '' if trace per object is desired, give a name (ie: 'SomeTraceFileName' ) if output to one file for all objects is desired...


# simulation time parameter
redrop_time = 125   # time in ms the mouse has at each position to learn the best next move
selfMoveTime = 125 # time to let netowrk stabiklize on a post-learning move made before taking output from thalamus and using it to move the rat

# what to do when there is an error...
retrain_time = 250  # (ms); time to retrain when it gets lost
reset_on_error = False # whether to start again or retrain if rat gets lost
hints = True   #is rat given a hint, and learning on that hint goes on for relearn ms, if it makes a mistake..ie: the current position is set back to where it made the mistake and then the training signal is turned on and the BestNextTrainingMove is fed to the trainingError ensemble,
               #  re-inforcing the correct action; if False, the training is turned on again (if rese_on_error is False) and the error is ignored and the rat is left to find the next move again

# Cheese (reward)...
cheese_lever = 5 # is the cheese under left lever (action = 4) or right lever (action = 5)
cheese_train_percent = 0.01  # the last x percent (expressed as 0.1 for 10% is used to specifically train on the goal cell, to emphasize the cheese lever to press to get the reward...

# Training & Action choices...
decision_tolerance = 0.001 # value (not percent) differnce required between the action showing maximum value from the thalamus and the next largest action to consider it a decision made...

# Maze parameters...
mazex = 10 # absolute width of the maze 0...mazex-1
mazey = mazex  # absolute height of the maze 0...mazey-1
startCell = [0,0]  # where to start from 
cheeseCell = [mazex - 1, mazey - 1]  # where is the cheese?

if OneLogger != '':
    logger = logging.getLogger( OneLogger )
    logger.setLevel(logging.DEBUG)

    logfile = OneLogger + '.txt'
    logfileHandler = logging.FileHandler(logfile)
    logfileHandler.setLevel(logging.DEBUG)

    consolelogfilehandler = logging.StreamHandler()
    consolelogfilehandler.setLevel(logging.DEBUG)

    #logformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # full format...
    logformatter = logging.Formatter('%(asctime)s - %(message)s')  # wihtout logname and DEBUG easier to read...
    consolelogfilehandler.setFormatter(logformatter)
    logfileHandler.setFormatter(logformatter)

    logger.addHandler(consolelogfilehandler)
    logger.addHandler(logfileHandler)
    
else:
    logger = ''



# BUILD THE MODEL IN NENGO....

##
## NENGO MODEL BUILD......................................................................................................................
##

# Network RatMazeLearn Start
net_RatMazeLearn = nef.Network('RatMazeLearn', quick = True)

# RatMazeLearn - Nodes
net_RatMazeLearn.make('ActionValuesEnsemble', N_default, 6, tau_rc=0.020, tau_ref=0.002, max_rate=(200.0, 500.0), intercept=(-1.0, 1.0), radius=1.00, seed=5)
placeEnPtr = net_RatMazeLearn.make('PlaceEnsemble', N_default, 2, tau_rc=0.020, tau_ref=0.002, max_rate=(200.0, 500.0), intercept=(-1.0, 1.0), radius=10.00)

#
# Create simple node to generate training information (random position and best next move)
#
# Start (0,0) goal (5,5) cheese_lever=5
LearnSimpleNodeEnsemble = TrainSimpleNode.TrainSimpleNode('LearnSimpleNodeEnsemble', redrop_time, train_time, reset_on_error, retrain_time, tracefilename, startCell[0] , startCell[1], cheeseCell[0], 
                                                          cheeseCell[1], cheese_lever, selfMoveTime, cheese_train_percent, decision_tolerance, walls, hints, mazex, mazey, RandomTraining, logger, net_RatMazeLearn,
                                                          weightsFile, projectdir, mappingSettleInterval=100, useQLearn = useQLearn, runName=runName)    # create the training node
net_RatMazeLearn.add(LearnSimpleNodeEnsemble)  # add it to the network

# RatMazeLearn - Templates
nef.templates.basalganglia.make(net_RatMazeLearn, name='ActionDecisionBG', dimensions=6, neurons=N_default, pstc=0.020, same_neurons=True)

nef.templates.thalamus.make(net_RatMazeLearn, name='Thalamus', dimensions=6, neurons=N_default)

nef.templates.learned_termination.make(net_RatMazeLearn, errName='NextMoveErro', N_err=N_err, preName='PlaceEnsemble', postName='ActionValuesEnsemble', rate=learnRate)  # was 5.00000e-07

# termination to shut off learning with
net_RatMazeLearn.get('NextMoveErro').addTermination('LearnInhibitionTermination', [[-1.5]] * N_err, 0.003, False)  # false = non-modulatory, we want to change the values there not the connection weights
net_RatMazeLearn.connect(LearnSimpleNodeEnsemble.getOrigin('LearnInhibitionOrigin'), net_RatMazeLearn.get('NextMoveErro').getTermination('LearnInhibitionTermination'))

net_RatMazeLearn.connect('ActionValuesEnsemble', 'ActionDecisionBG.input')

net_RatMazeLearn.connect('ActionValuesEnsemble', 'NextMoveErro', weight=-1)  # subtract the error from the position feed from simple node
net_RatMazeLearn.connect(LearnSimpleNodeEnsemble.getOrigin('BestNextTrainingMoveOrigin'), 'NextMoveErro')
net_RatMazeLearn.connect(LearnSimpleNodeEnsemble.getOrigin('RatPositionOrigin'), 'PlaceEnsemble')

net_RatMazeLearn.connect(net_RatMazeLearn.get('ActionDecisionBG').getOrigin('output'), net_RatMazeLearn.get('Thalamus').getTermination('bg_input') )
net_RatMazeLearn.connect(net_RatMazeLearn.get('Thalamus').getOrigin('xBiased'), LearnSimpleNodeEnsemble.getTermination('thalamus_move_mask_termination'))

# logging to CSV file...
logger = nef.Log(net_RatMazeLearn, NEFCSVFileName, dir = NEFCSVdir, tau = 0.02)
logger.add('LearnSimpleNodeEnsemble', origin = 'RatPositionOrigin')   # Record the position the SimpleNode training signal sends the rat to (input to place ensemble)
logger.add('LearnSimpleNodeEnsemble', origin = 'BestNextTrainingMoveOrigin')  # Record the BestNextTrainingMoveAction the SimpleNode training signal tells the rat to take 
logger.add('PlaceEnsemble', origin = 'X')  # Record position Rat thinks it is in
logger.add('Thalamus', origin='xBiased')   # Record the action the Rat chooses 

##
## Network & Visualization..........................................................................................................................
##

if OSname.find("win") > -1 or OSname.find("mac") > -1 and not runBatch:
    timeview.view.watches.append(Maze.DemoWatch())  # add the watcher class, note this nengo 1.4 syntax
elif OSname.find("linux")  > -1 :
    pass
    
net_RatMazeLearn.add_to_nengo()

# Screen layout for interactive mode
net_RatMazeLearn.set_layout
({'state': 6, 'height': 966, 'width': 1696, 'x': -8, 'y': -8},
 [(u'LearnSimpleNodeEnsemble', None, {'label': False, 'height': 32, 'width': 251, 'x': 467, 'y': 4}),
  (u'LearnSimpleNodeEnsemble', 'display', {'label': False, 'height': 1079, 'width': 580, 'x': 759, 'y': 1}),
  (u'ActionDecisionBG', None, {'label': False, 'height': 32, 'width': 167, 'x': 335, 'y': 588}),
  (u'Thalamus', None, {'label': False, 'height': 32, 'width': 94, 'x': 603, 'y': 589}),
  (u'ActionValuesEnsemble', None, {'label': False, 'height': 32, 'width': 209, 'x': 112, 'y': 303}),
  (u'PlaceEnsemble', None, {'label': False, 'height': 32, 'width': 145, 'x': 126, 'y': 4}),
  (u'ActionValuesEnsemble', 'value|X', {'label': True, 'sel_dim': [0, 1, 2, 3, 4, 5], 'last_maxy': 2.0000000000000013, 'sel_all': True, 'height': 200, 'width': 300, 'x': 66, 'fixed_y': None, 'autozoom': False, 'y': 360}),
  (u'PlaceEnsemble', 'XY plot|X', {'label': True, 'sel_dim': [0, 1], 'last_maxy': 20.000000000000014, 'height': 200, 'width': 200, 'x': 103, 'autohide': True, 'autozoom': False, 'y': 48}),
  (u'ActionDecisionBG', u'value|output', {'label': True, 'sel_dim': [0, 1, 2, 3, 4, 5], 'last_maxy': 1.0000000000000007, 'sel_all': True, 'height': 200, 'width': 300, 'x': 2435, 'fixed_y': None, 'autozoom': False, 'y': 41}),
  (u'Thalamus', u'value|xBiased', {'label': True, 'sel_dim': [0, 1, 2, 3, 4, 5], 'last_maxy': 2.0000000000000013, 'sel_all': True, 'height': 200, 'width': 300, 'x': 385, 'fixed_y': None, 'autozoom': False, 'y': 632}),
  (u'LearnSimpleNodeEnsemble', u'value|LearnInhibitionOrigin', {'label': True, 'sel_dim': [0], 'last_maxy': 1.0000000000000007, 'sel_all': True, 'height': 125, 'width': 300, 'x': 381, 'fixed_y': None, 'autozoom': False, 'y': 269}),
  (u'LearnSimpleNodeEnsemble', u'XY plot|RatPositionOrigin', {'label': True, 'sel_dim': [0, 1], 'last_maxy': 10.000000000000007, 'height': 200, 'width': 200, 'x': 423, 'autohide': True, 'autozoom': True, 'y': 46}),
  (u'ActionDecisionBG', u'value|output', {'label': True, 'sel_dim': [0, 1, 2, 3, 4], 'last_maxy': 1.0000000000000007, 'sel_all': False, 'height': 200, 'width': 300, 'x': 54, 'fixed_y': None, 'autozoom': False, 'y': 625})],
 {'dt': 0, 'show_time': 2.0, 'sim_spd': 0, 'filter': 0.03, 'rcd_time': 30.0}) 

try:
    if not runBatch:
        currview=net_RatMazeLearn.view()
    else:
        net_RatMazeLearn.run(2000)  # run the model, it will throw a fatal exception when done and stop itself...
        
except CheeseFoundException:
    print "Cheese found exception caught."

