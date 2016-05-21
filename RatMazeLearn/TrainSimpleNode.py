from __future__ import division
import AStarPathFinder
import copy
import string
import random
import logging
import cPickle as pickle
import codecs
import os
import sys
from array import *
from subprocess import call
import java.lang

def fatal_error ( caller, msg ):
    msg = 'ERROR: '+ caller + ' - ' + msg    
    java.lang.System.exit(0)
    #sys.exit(0)
    #raise Exception(msg)

nefOn = True   # set to false and comment both following lines out and uncomment last line to use TestMaze.py to test...

import nef

#nefOn = False
#class TrainSimpleNode():  # non NEF inheritance for testing before training network in NENGO

class TrainSimpleNode(nef.SimpleNode):

    """TrainingInput SimpleNode Class simulates dropping the rat in the maze at a random location and then projects
       computes the right move for that location and then projects this location into the Place population and the
       correct move in response to the rat finding himself at this location into the Error population.

       The idea is that this node creates the training signal into the whole circuit, basically 'if you find yourself here, the
       next right move is to take this action".

       The world is composed of a 3 by 3 grid where the positions are labelled as 1 to 9 starting from the upper left
       and counting horizontally then vertically. One square has two levers on it where one of the levers results in cheese
       for our simulated rat and the other nothing.

       There are 6 actions possible; move north, move south, move east, move west, pull lever 1, pull lever 2

    """
    
    def __init__(self, name, redrop_time, train_time, reset_on_error, retrain_time, tracefilename, sx, sy, ex, ey, cl, selfMoveTime, \
                 cheese_train_percent, decision_tolerance, walls, hints, mazex, mazey, RandomTraining, OneLogger, pNetwork, WeightsFile, \
                 projectdir, mappingSettleInterval, useQLearn, runName):

        self.TraceOn = True
        self.runName = runName
        
        self.OneLogger = OneLogger
        self.projectdir =  projectdir        
        
        self.OSname = java.lang.System.getProperty("os.name").lower()
        if self.OSname.find("win")  > -1 :
            self.OSname = "win"
            self.fileSep = "\\"
        else:
            self.OSname = 'linux'
            self.fileSep = r"/"
        
        # logger implementation
        if OneLogger ==  '':
            self.logger = logging.getLogger('TrainSimpleNodeInstance' + '_' + str(id(self)) )
            self.logger.setLevel(logging.DEBUG)
            
            self.logfile = tracefilename + '_' + str(id(self)) + '_TrainSimpleNodeInstance.txt'
            self.logfileHandler = logging.FileHandler(self.logfile)
            self.logfileHandler.setLevel(logging.DEBUG)

            self.consolelogfilehandler = logging.StreamHandler()
            self.consolelogfilehandler.setLevel(logging.DEBUG)
            
            self.logformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            self.consolelogfilehandler.setFormatter(self.logformatter)
            self.logfileHandler.setFormatter(self.logformatter)
            
            self.logger.addHandler(self.consolelogfilehandler)
            self.logger.addHandler(self.logfileHandler)
            
        else:
            self.logger = OneLogger
                    
        self.MovesDict = { 'Forward' : 0, 'Back' : 1, 'Left' : 2, 'Right' : 3, 'PressLeftLever' : 4, 'PressRightLever' : 5 }

        self.pNetwork = pNetwork
        self.WeightsFile = WeightsFile
        
        self.mappingDataFile =  self.projectdir + self.fileSep + r"mappingdata.pic"
        
        self.time = 0
        self.hints = hints  # if after learning over the rat makes a mistake, give it a hint? a short burst of learning on the problem area 
           # stores the movements under self motion that have been made, used to implment the self.use_second_best_decisions behaviour above

        # list of corresponding coordinate changes for each direction
        self.x_moves = [0,0,-1,1,0,0]
        self.y_moves = [1,-1,0,0,0,0]
            
        self.maze_x = mazex  # sizes of maze
        self.maze_y = mazey

        self.MapTrainedNet = False
        self.mappingStarted = False
        self.mappingResults = []
        self.mapSettleTime = 0  # counter to let the network settle before reading the answer during mapping...
        self.mappingSettleInterval = mappingSettleInterval
                
        self.sx = sx    # start position for rat
        self.sy = sy

        self.ex = ex   # stop position for rat
        self.ey = ey

        self.thalamus_move_mask = [0,0,0,0,0,0]
        self.action_number = -1
        self.cheese_action = cl # should be either 5 or 6 (pull left lever or right lever for cheese)
        self.cheese_train_percent = cheese_train_percent
        self.train_cheese_only = False
        self.AccummulateSettleTime = 0

        self.noMovesInaRow = 0
        
        self.reset_to_start_on_error = False
        self.retrain_time = retrain_time
        self.reTraining = False
        
        self.useQLearn = useQLearn

        self.InhibitLearning = False  # a flag to turn off learning while the position of the rat is being moved, stops the network from learning the repositioning movements as real movements
        
        # example for walls: walls = ( (1, 1), (2, 2), (0,1) )
        self.walls = walls
        # create the best next moves list and maze objects...
        if self.useQLearn:  # choose which class of BestNextMoves, with or without qlearning...
            self.BestNextTrainingMoves = AStarPathFinder.qlearn_NextMovesList (self.maze_x, self.maze_y, self.sx, self.sy, self.ex, self.ey, self.walls, tracefilename, self.cheese_action, self.OneLogger)  # creates and populates itself...

            # Call matplotlib process to generate the qlearn accuracy graph and display it...
            self.writePrint ( 'Maze.paintComponent: Now calling [%s].' % ( "python generateQLearnPlot.py" ) )                                
            call (r'python "' + self.projectdir + self.fileSep + r'generateQLearnPlot.py"', shell=True)
            self.writePrint ( 'Maze.paintComponent: Returned from calling [%s].' % ( "python generateQLearnPlot.py" ) )                                                
            
        else:
            self.BestNextTrainingMoves = AStarPathFinder.NextMovesList (self.maze_x, self.maze_y, self.sx, self.sy, self.ex, self.ey, self.walls, tracefilename, self.cheese_action, self.OneLogger)  # creates and populates itself...
        
        # Time is counted as a series of ticks 
        self.time_since_last_drop = 0
        self.redrop_time = redrop_time  # every choose_time number of ticks choose a new place to drop the rat in the maze

        # no minutes (in ms) to train before running itself
        self.RandomTraining = RandomTraining
        # when not RandomTraining use path walking to train, walk in order (in theory, since learning is continuous and the assocaition of position to action is not random over the continuum, this should produce better training than random jumps
        self.pathTraining_CurrentPath = 0  # current path being trained on
        self.pathTraining_CurrentCell = 0   # current cell in current path being trained on

        self.PathsWalkIndex = 0
        self.learn_time = train_time
        self.time_learning = 0
        self.hint_learning = False
        self.PathTrainingDone = False

        self.ConsequtiveNoActionsChoosen = 0

        self.current_x = 0
        self.current_y = 0
        
        self.goal_path = self.BestNextTrainingMoves.get_goal_path() # path from startXY to endXY 
        self.current_path = self.goal_path  # stores the current path we are working on, used to display the right maze visually

        self.failed_moves_stack = []  # a list of moves tried but that resulted in an error; structure is [ [(x,y), actionNumber],  [(x1,y1), actionNumber], [(x2,y2), actionNumber], ... ]
        
        self.settle_time = 25     # (ms)
        self.decision_tolerance = decision_tolerance # differnce required between the action showing maximum value from the thalamus and the next largest action to consider it a decision made...

        self.post_action_x = 0    # stores the next position
        self.post_action_y = 0

        self.best_next_move_x = -1 # stores the best next move x and y; one level ahead of current best next move being applied
        self.best_next_move_y = -1
        self.AlternateMovesAfterTraining = True # controls whether or not moves are choosen via alternates or retraining is initiated on errors when moving by self...

        self.thinkingOfMoving_x = -1  # tracks the first reaction of the network to a new position input...
        self.thinkingOfMoving_y = -1
        self.thisMoveAccumulator = [0,0,0,0,0,0]
        self.thisMoveCurrentAccumulator = [0,0,0,0,0,0]
        
        self.RandomTrainingNodeCount = 0
        
        self.useQLearn =  useQLearn
        
        self.LoadWeights = True  # should we attempt to load the weights from the previous learning run?
        self.saveWeights = True

        self.oldActionState = [-2,-2,[-2,-2,-2,-2,-2,-2]]
        
        self.selfMoveTime = selfMoveTime  # how long the network is given to settle after a self directed move before reading the thalamus' output and using it to execute  the command represented there
        
        # Populate initial value of best next moves list...
        self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)

        if nefOn:
            nef.SimpleNode.__init__(self, name) # call superclass constructor...

        self.data = { 'mazeX' : self.maze_x, 'mazeY' : self.maze_y, 'sx' : self.sx, 'sy' : self.sy,\
                      'ex' : self.ex, 'ey' : self.ey,
                      'RatX' : self.current_x, 'RatY' : self.current_y , 'walls' : self.walls, \
                      'path' : self.current_path, 'BestNextTrainingMoveX' : self.best_next_move_x, 'BestNextTrainingMoveY' : self.best_next_move_y,\
                      'cheeseLever' : self.cheese_action, 'LeverRatPulled' : self.action_number}    

    def writePrint ( self, msg ):
        if self.TraceOn:
            self.logger.debug (msg)
    
    def reset(self, randomize=False):
        self.writePrint ("TrainSimpleNode.reset: Reset function called. Reset not supported in this version. Restart NENGO and this application.")
        self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)
        #nef.SimpleNode.reset(self, randomize)

    def ThinkingOfActionLookAheadToMove (self, currx, curry, last_action, thalamus_move_mask ):
        # called just after a move has changed the current_x and current_y. looks at the new state of the thalamus and projects ahead what the move currently being contemplated
        # would mean for the rat. Does a few checks on that move and logs whether it looks like a good move or not. All done to provide the graphical interface, via the get_data()
        # calls, the ability to project the next possible state on the display. Note there will be many of these calls between the last action and the next choosen action
        # which averages across all outputs from thalamus
        
        #self.writePrint ("TrainSimpleNode.actionToMove: Type of thalamus_move_mask is [%s]." % type(thalamus_move_mask))

        traceStr = 'Time=[%f], XY[%f,%f],actionNum N/A,thalamus_move_mask[%s,].' % (self.time, currx, curry, thalamus_move_mask,)
        try:
            action_number = thalamus_move_mask.index(max(thalamus_move_mask))  # find the location of the maximum value, this is the command to then execute
        except ValueError:          
            msg = 'TrainSimpleNode.ThinkingOfActionLookAheadToMove: No command found, all zeros or same.' + traceStr
            self.writePrint (msg)
            return [-1,-1]

        # now that action_number is known re-assign the trace string
        traceStr = 'XY[%f,%f],actionNum[%s], thalamus_move_mask[%s,].' % (currx, curry, str(action_number), thalamus_move_mask,)

        msg = ( 'TrainSimpleNode.ThinkingOfActionLookAheadToMove: last action was [%f] Indexed into thalamus_accumulated_mask (rat now thinking of this for next action): ' % last_action ) + traceStr
        self.writePrint (msg)
        
        if  action_number >= 0 and action_number <= (len(thalamus_move_mask)-1):  # see if there is a valid thalamus_move_mask, at start there is only zeros so skip that case (do nothing till next cycle)        

            post_action_x = currx + self.x_moves[action_number]   # indexes into the move list x and takes the same element from the x_moves list and adds it to x
            post_action_y = curry + self.y_moves[action_number]   # same for y
            lever = 0

            lLever = (round(float(thalamus_move_mask[4]),0) == 1)
            rLever = (round(float(thalamus_move_mask[5]),0) == 1)

            # Check to see if something changed before we print out more trace messages...
            if self.oldActionState == [ currx, curry, thalamus_move_mask ]:
                Changes = False
            else:
                Changes = True
                
            self.oldActionState = [ currx, curry, thalamus_move_mask ]   

            if (currx == self.ex and curry == self.ey):  # we are at the end cell...check levers...
            
                if lLever and not(rLever):
                    lever = 4
                    if Changes:
                        msg = 'TrainSimpleNode.ThinkingOfActionLookAheadToMove: All good. Next action being thought of Left is lever pull.' + traceStr
                        self.writePrint (msg)

                elif rLever and not(lLever):
                    lever = 5
                    if Changes:
                        msg = 'TrainSimpleNode.ThinkingOfActionLookAheadToMove: All good. Next action being thought of is Right lever pull.' + traceStr
                        self.writePrint (msg)

                elif lLever and rLever:
                    # at end cell both levers being pulled, this is an error...
                    if Changes:                    
                        msg = 'TrainSimpleNode.ThinkingOfActionLookAheadToMove: At END cell Next action being thought of is  BOTH levers pulled. Error.' + traceStr
                        self.writePrint (msg)

                else:
                    # at end cell but NO levers being pulled...
                    if Changes:                    
                        msg = 'TrainSimpleNode.ThinkingOfActionLookAheadToMove: At end cellNext action being thought of is NO levers pulled. Error.' + traceStr
                        self.writePrint (msg)
            
            else:   # we are not at the end cell...
                if lLever or rLever:
                    if Changes:                    
                        msg = 'TrainSimpleNode.ThinkingOfActionLookAheadToMove: Not at end cell, but next action being thought of is  pulling a lever.  Error.'+ traceStr
                        self.writePrint (msg)
                else:
                    # not at end cell, no levers being pulled, all OK, just move on...
                    if Changes:                    
                        msg = 'TrainSimpleNode.ThinkingOfActionLookAheadToMove: Not at end cell, Next action being thought of is no levers pulled. All Ok.' + traceStr
                        self.writePrint (msg)

            return [post_action_x, post_action_y, lever]
        
        else:
            # action number bad, happens at startup, log and move on...
            if Changes:            
                msg = 'TrainSimpleNode.ThinkingOfActionLookAheadToMove: Invalid action command [%f]' + traceStr       
                self.writePrint (msg)
                return [-1,-1,0]      

    def isValidMove (self, currx, curry, action_number_choosen):
        # check if proposed action selected is allowable, ie: doesnt hit a wall

        post_action_x = currx + self.x_moves[action_number_choosen]   # indexes into the move list x and takes the same element from the x_moves list and adds it to x
        post_action_y = curry + self.y_moves[action_number_choosen]   # same for y
               
        if  action_number_choosen in (0,1,2,3) and (post_action_x, post_action_y) not in self.walls and ( post_action_x in range(self.maze_x) and post_action_y in range(self.maze_y) ):
            self.writePrint ("TrainSimpleNode.isValidMove: Action [%f] on cell [%f, %f] is valid." % ( action_number_choosen, currx, curry ) ) 
            return True

        elif action_number_choosen in (4,5) and (currx == self.ex and curry == self.ey):  # we are at the end cell...lever pulls are allowed moves (this does not mean it is correct lever though, it is just that is a valid move, not a wall etc...)
            self.writePrint ("TrainSimpleNode.isValidMove: Action [%f] on cell [%f, %f] is valid." % ( action_number_choosen, currx, curry ) )            
            return True
            
        else:
            self.writePrint ("TrainSimpleNode.isValidMove: Action [%f] on cell [%f, %f] is NOT valid." % ( action_number_choosen, currx, curry ) )                        
            return False

    def UpdateTraceStr (self):
        return ( 'time[%f], XY[%f,%f],action[%f],postXY[%f,%f],\nactionMask[%f,%f,%f,%f,%f, %f],BestNextTrainingMove=[%f,%f,%f,%f,%f, %f].' \
        % (self.time, self.current_x, self.current_y, self.action_number, self.post_action_x, self.post_action_y, \
            self.thalamus_move_mask[0],self.thalamus_move_mask[1],self.thalamus_move_mask[2],self.thalamus_move_mask[3], self.thalamus_move_mask[4],self.thalamus_move_mask[5], \
            float(self.best_next_move_training_mask[0]),float(self.best_next_move_training_mask[1]), float(self.best_next_move_training_mask[2]),float(self.best_next_move_training_mask[3]),\
            float(self.best_next_move_training_mask[4]),float(self.best_next_move_training_mask[5]) ) )

    def GetActionChoosen (self):
        # determine if there is a clear decision
        actions = self.thalamus_move_mask[:]  # take a copy of the current actions... # TODO
        actions.sort(reverse=True)  # sort the copy from highest to lowest
        if actions[0] - actions[1] >= self.decision_tolerance:  # check if there is really a decision here by comparing strongest signal to second strongest...
            # decision is made, find which command it was
            try:
                action_number = round(self.thalamus_move_mask.index(actions[0]),0)  # find the location of the maximum value, this is the command to then execute
            except ValueError:
                msg = 'TrainSimpleNode:GetActionChoosen: No command found. ' + traceStr
                self.writePrint (msg)
                action_number = -1    # error could not find the max...
        else:
            # confused, decisions too close to call...
            action_number = -1    # no clear decision at this time...    
    
        return action_number
    

    def tick (self):
        
        # if it is time to shut off learning then 
        #   see if rat can navigate the maze
        #   send rat back to starting point
        # elif learning is over and time to move again (network has settled from last move) then
        #   move rat based on output from thalamus
        # elif learning not over
        #   randomly drop rat every redrop_time milliseconds
        # end

        self.time += 1
        traceStr = self.UpdateTraceStr()
        
        self.writePrint("TrainSimpleNode.tick: Entering tick() call : time_learning = learn_time : time_spent_learning=[%f] of total_time_to_learn=[%f]." % (self.time_learning, self.learn_time) )
        
        # path walking and random drop training...
        if self.MapTrainedNet:  # Maps out the paths in a network that is already trained...this happens after training...flag is turned on once training done...
            
            self.writePrint("TrainSimpleNode.tick: MAPPING trained network.")
            
            if not self.mappingStarted:
                # first time through kick it off...
                self.current_x = self.sx * 1
                self.current_y = self.sy * 1
                self.mappingStarted = True  # start mapping...
                self.mapSettleTime = 0
                self.writePrint ( 'TrainSimpleNode.tick: STARTING Mapping out the trained network for (x,y)=[%f,%f].' % (self.current_x, self.current_y) )
                
                self.InhibitLearning = True    
                
            else:

                if self.mapSettleTime >= self.mappingSettleInterval:                    

                    self.mapSettleTime = 0

                    # record the response to the current (x,y) pair for all (x,y) 
                    ac = self.GetActionChoosen()  # decode the action choosen from the value in the thalamus_move_mask
                    mappingbestMove  =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y).index("1")
                    self.mappingResults.append([self.current_x, self.current_y, mappingbestMove, ac, self.thisMoveAccumulator ])
    
                    # find the next non-wall cell to map...
                    xx = round(self.current_x, 0)
                    yy = round(self.current_y, 0)            
                    self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)  # Learning inhibition is on, project to display in logs only
                    
                    while True:
                        
                        if xx >= self.maze_x - 1 and yy >= self.maze_y - 1:
                            
                            # we are done, save results from mapping and generate data file and graph and exit...
                            self.MapTrainedNet = False  # turn off mapping permanently
                            
                            # Save the data to a pickle file
                            mappingDataFileHndl = open( self.mappingDataFile,'wb')
                            pickle.dump(self.mappingResults, mappingDataFileHndl, -1)  # set to save in binary mode (0=ASCII, > 1 = binary mode; avoids CR/LF problem decoding)
                            #weightSaveFile.write(pickle.dumps(learnedWeights, 0))
                            mappingDataFileHndl.close()
                            self.writePrint ( 'Maze.paintComponent: Pickled mapped responses [%s].' % ( self.mappingDataFile) )                
                            
                            # Call matplotlib process to generate a graph and display it
                            self.writePrint ( 'Maze.paintComponent: Now calling [%s].' % ( "python generateMazePlot.py" ) )                                
                            call (r'python "' + self.projectdir + self.fileSep + r'generateMazePlot.py"', shell=True)
                            self.writePrint ( 'Maze.paintComponent: Returned from calling [%s].' % ( "python generateMazePlot.py" ) )                                                
                                         
                            # go back to the start...
                            xx = self.sx * 1
                            yy = self.sy * 1

                            self.thisMoveAccumulator = [0,0,0,0,0,0] # reset for use in post learning moves...
                            
                            break
                            
                        elif yy >= self.maze_y - 1 and xx < self.maze_x - 1:
                            xx += 1
                            yy = 0
        
                        elif yy < self.maze_y - 1:
                            yy += 1
                        
                        # Check to make sure we did not land on a wall...
                        if (xx, yy) in self.walls:
                            self.mappingResults.append([xx, yy, -1, -1, self.thisMoveAccumulator ])  # log it as a wall and move on...
                            
                        else:
                            break  # we found an xy pair that was not in walls
                        
                        self.writePrint ("TrainSimpleNode.tick: Mapping loop (x,y)=[%f,%f]." % (self.current_x, self.current_y))
    
                    # set x and y to the next point that is not a wall...
                    self.current_x = round(xx, 0)
                    self.current_y = round(yy, 0)                            
                    self.writePrint ( 'TrainSimpleNode.tick: Mapping out the trained network for (x,y)=[%f,%f], BestMove=[%f], Choosen=[%f]' \
                                     % (self.current_x, self.current_y, float(mappingbestMove), float(ac)) )

                    self.thisMoveAccumulator = [0,0,0,0,0,0]
                    
                else:
                    self.mapSettleTime += 1                    
                    if self.mapSettleTime > self.settle_time :  # ignore first 25 ms or so...
                        # acummulate : ie: self.thisMoveAccumulator += self.thalamus_move_mask
                        self.thisMoveAccumulator = [ self.thisMoveAccumulator[i] + self.thalamus_move_mask [i] for i in range (len(self.thalamus_move_mask)) ]
                        
        
        elif (self.RandomTraining == False and not self.PathTrainingDone) or (self.RandomTraining == True and self.time_learning < self.learn_time):
            # execute learn instructions if we have not run out the time for learning and we are random training, or we are doing path training and we are not done...
            
            self.writePrint("TrainSimpleNode.tick: TRAINING network, id=[%f] time_spent_learning=[%f] of total_time_to_learn=[%f]." % (id(self), self.time_learning, self.learn_time) )

            # load weights from a file if it is there
            self.writePrint("TrainSimpleNode.tick: Checking for presence of weights file [%s]." % (self.WeightsFile) )
            if self.LoadWeights and os.path.isfile(self.WeightsFile):
                
                self.LoadWeights = False
                self.writePrint ( '\n\nTrainSimpleNode.tick: Loading saved weights file [%s] in instance_id=[%f].' % (self.WeightsFile, id(self)) )
                weightLoadFile = open(self.WeightsFile,'rb')
                lw = pickle.load (weightLoadFile) # load the weights variable back into memory (note: determines binary or ASCII mode itself        
                self.pNetwork.get('ActionValuesEnsemble').getTermination("PlaceEnsemble_00").setTransform(lw, True)  # set the learned connection termination's weight matrix
                weightLoadFile.close()
                self.saveWeights = False # we have just loaded them, they won't change so do not save these same ones...
                self.writePrint ( 'TrainSimpleNode.tick: Saved weights loaded from [%s].\n\n' % self.WeightsFile )

                # Shut off training
                self.time_learning = self.learn_time *  1 # set the learning time to the finish
                self.PathTrainingDone = True      
                self.writePrint("TrainSimpleNode.tick: Finished TRAINING network by weights loading, time_spent_learning=[%f] of total_time_to_learn=[%f]." % (self.time_learning, self.learn_time) )
                
            else:
                
                self.writePrint("TrainSimpleNode.tick: TRAINING network, id=[%f], random training =[%i], pathTrainingDone=[%i], loadweights=[%i]." % (id(self), self.RandomTraining, self.PathTrainingDone, self.LoadWeights) )
                
                # run the training, not using saved weights...

                if not self.PathTrainingDone:  # if we are still doing the very first training (not re-training with hints on errors) then 
                    self.current_path = self.BestNextTrainingMoves.get_best_paths(self.pathTraining_CurrentPath) # default is the path computed for us to solve globally, used for display updating inside the DemoView class
                else:
                    # if training is called after initial path training is done, then this is a hint trainin
                    self.current_path = self.goal_path

                # we are learning still...
                self.time_learning += 1  # increment global counter, counts up to learn time and then turns off learning

                if not self.hint_learning:  # when hint learning is on, the right answer is injected once from the code in the post-training area, but learning is not restarted
                    
                    if self.time_since_last_drop > self.redrop_time:  # still learning and it is time to drop the rat again....continue training                
                        # we are training and time to get new drop, so choose new spot and then project the best_next_move to the error population

                        self.InhibitLearning = True  # turn of learning as we move mouse and reset the bestmovesarray
                        
                        if  self.train_cheese_only == True:
                            # the rat keeps pulling the wrong lever, so reinforce strongly the cheese behaviour (problem found is that with simple
                            # learned connections is that the behaviour competes with all actions which are largely "MOVE RIGHT" or "MOVE UP")
                        
                            self.current_x = round(self.ex,0)
                            self.current_y = round(self.ey,0)

                        else:
                            
                            # normal training, not special handler for lever problem...    
                            if (self.time_learning > self.learn_time * ( 1 - self.cheese_train_percent ) ):
                                # for last 5% of the learning time, train on the cheese cell only, this proxies for the high emotional reward the cheese cell would have
                                # since we are using simple learning connection, need a stronger salience for the cheese cell
                                self.current_x = round(self.ex,0)
                                self.current_y = round(self.ey,0)
                               
                            else:
                                
                                if self.RandomTraining:
                                    # else randomly choose new spot to drop rat and set current position, avoid walls...
                                    while True:
                                        xtemp = random.randint(0,self.maze_x - 1)
                                        ytemp = random.randint(0,self.maze_y - 1)
                                        
                                        if not ( (int(xtemp),int(ytemp)) in self.walls ):
                                            self.current_x = round(xtemp,0)
                                            self.current_y = round(ytemp,0)
                                            break  # leave loop when a random point found that is not a wall...

                                    self.RandomTrainingNodeCount += 1
                                    self.writePrint ( '\n\n\nTRACE: TrainSimpleNode:tick- Randomly choose new cell to train on [%f, %f].' % ( self.current_x, self.current_y ) )
                                    
                                else:
                                    # non-random, path-walking training: walk paths in order from start of maze to end, train on all cells this way...
                                    msg = ('\n\n\nTRACE: TrainSimpleNode:tick- Path Walking Training On CurrPath[%i of %i paths]; self.BestNextTrainingMoves.get_best_paths(%i)=[%s]], CurrCell[%f of %f] XY[%f,%f], BestMoves[%s].' \
                                           % (self.pathTraining_CurrentPath, len(self.BestNextTrainingMoves.get_best_paths()), self.pathTraining_CurrentPath, \
                                              self.BestNextTrainingMoves.get_best_paths(self.pathTraining_CurrentPath), 
                                              self.pathTraining_CurrentCell, len(self.BestNextTrainingMoves.get_best_paths(self.pathTraining_CurrentPath)), \
                                              self.current_x, self.current_y, self.best_next_move_training_mask) ) + self.UpdateTraceStr() + '\n\n\n'
                                    self.writePrint ( msg )
                                    
                                    if self.pathTraining_CurrentPath <= len(self.BestNextTrainingMoves.get_best_paths())-1:
                                        if self.pathTraining_CurrentCell <= len(self.BestNextTrainingMoves.get_best_paths(self.pathTraining_CurrentPath))-1:
                                            self.current_x = self.BestNextTrainingMoves.get_best_paths(self.pathTraining_CurrentPath)[self.pathTraining_CurrentCell][0]  # x
                                            self.current_y = self.BestNextTrainingMoves.get_best_paths(self.pathTraining_CurrentPath)[self.pathTraining_CurrentCell][1]  # y
                                            self.pathTraining_CurrentCell += 1
                                            self.time_learning = 0 # keep forcing time backwards until all paths trained on...
                                            self.writePrint("TrainSimpleNode.tick: Reset 001 time_learning : time_spent_learning=[%f] of total_time_to_learn=[%f]." % (self.time_learning, self.learn_time) )
                                            
                                        else:
                                            # reached end of this path, now train on the next path
                                            self.pathTraining_CurrentPath += 1  # this path trained on completely, go to next path...
                                            self.pathTraining_CurrentCell = 0
                                            if self.pathTraining_CurrentPath < len(self.BestNextTrainingMoves.get_best_paths()):
                                                self.current_x = self.BestNextTrainingMoves.get_best_paths(self.pathTraining_CurrentPath)[self.pathTraining_CurrentCell][0] # x
                                                self.current_y = self.BestNextTrainingMoves.get_best_paths(self.pathTraining_CurrentPath)[self.pathTraining_CurrentCell][1] # y
                                                self.pathTraining_CurrentCell += 1
                                                self.time_learning = 0 # keep forcing time backwards until all paths trained on...
                                                self.writePrint("TrainSimpleNode.tick: Reset 002 time_learning : time_spent_learning=[%f] of total_time_to_learn=[%f]." % (self.time_learning, self.learn_time) )
                                                
                                            else:
                                                msg = ('\n\n\nTRACE: TrainSimpleNode:tick (1)- All paths walked Training On CurrPath[%f], CurrCell[%f]. XY[%f,%f], BestMoves[%s].' \
                                                       % (self.pathTraining_CurrentPath, self.pathTraining_CurrentCell, self.current_x, self.current_y, self.best_next_move_training_mask) ) + self.UpdateTraceStr() + '\n\n\n'
                                                self.writePrint ( msg )                                                      
                                                self.RandomTraining = True  # turn off path walking...if burst training is engaged later it will be random (all paths take too long)
                                                self.PathTrainingDone = True
                                                self.current_path = self.goal_path # go back to displaying main path
                                                self.pathTraining_CurrentPath = 0
                                                self.time_learning = self.learn_time * 1 # force end of learning... we have trained on all paths and all cells
                                                self.writePrint("TrainSimpleNode.tick: Set 003 time_learning = learn_time : time_spent_learning=[%f] of total_time_to_learn=[%f]." % (self.time_learning, self.learn_time) )
                                                
                                    else:
                                        msg = ('\n\n\nTRACE: TrainSimpleNode:tick (2)- All paths walked Training On CurrPath[%f], CurrCell[%f]. XY[%f,%f], BestMoves[%s].' \
                                               % (self.pathTraining_CurrentPath, self.pathTraining_CurrentCell, self.current_x, self.current_y, self.best_next_move_training_mask) ) + self.UpdateTraceStr() + '\n\n\n'
                                        self.writePrint ( msg )                        
                                        self.RandomTraining = True  # turn off path walking...if burst training is engaged later it will be random (all paths take too long)
                                        self.PathTrainingDone = True
                                        self.pathTraining_CurrentPath = 0                                    
                                        self.current_path = self.goal_path # go back to displaying main path 
                                        self.time_learning = self.learn_time * 1 # force end of learning... we have trained on all cells
                                        self.writePrint("TrainSimpleNode.tick: Set 004 time_learning = learn_time : time_spent_learning=[%f] of total_time_to_learn=[%f]." % (self.time_learning, self.learn_time) )
                                        
                        self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)
                        self.action_number = self.best_next_move_training_mask.find('1')  # trace string printing update action choosen...
                        self.InhibitLearning = False  # now that position and bestMoves are set, turn on learning again...
                        self.time_since_last_drop = 0  # reset tick counter...

                        # rat dropped to new spot...
                        msg = ('\n\n\nTRACE: TrainSimpleNode:tick- Random [%i] Training still ON. XY[%f,%f], BestMoves[%s].' % (self.RandomTraining, self.current_x, self.current_y, self.best_next_move_training_mask) ) + self.UpdateTraceStr() + '\n\n\n'
                        self.writePrint ( msg )
                                
                    else:
                        # we are still learning the last bestmove for the last drop
                        self.time_since_last_drop += 1  # advance time

                else:
                    # let the time wind down, but leaving the current position and BestNextTrainingMoves feeding in...trying to relearn the correct to the mistake just made for a period = self.learn_time 
                    self.time_since_last_drop += 1  # advance time

        elif self.time_learning == self.learn_time:  # time to turn off learning

            self.writePrint ('\n\n\nTRACE: TrainSimpleNode:tick- Training turned OFF!! saveWeights=[%i]. XY[%f,%f].\n\n\n' % (self.saveWeights, self.current_x, self.current_y))

            # Training is now at an end...store a copy of the weights in a file...
            if self.saveWeights:

                self.writePrint ('\n\n\nTRACE: TrainSimpleNode:tick- Starting save of weights saveWeights=[%i] to file [%s].\n\n\n' % (self.saveWeights, self.WeightsFile))

                lw = self.pNetwork.get('ActionValuesEnsemble').getTermination("PlaceEnsemble_00").getTransform() # get the learned connection termination's weight matrix
                lw2 = []
                for i in range(len(lw)):
                    self.writePrint ('\nTrainSimpleNode.tick: lw[%i][len=%i]=[%s].\n' % ( i, len(lw), lw[i] ) )
                    lw2.append(lw[i][:])  # this seems redundant but it cleans up a header problem with the list returned from getTransform() in NENGO v1.4...
                                    
                weightSaveFile = open( self.WeightsFile, 'wb' )
                self.writePrint ( 'TrainSimpleNode.tick: opened weightfile [%s].' % self.WeightsFile )                
                pickle.dump(lw2, weightSaveFile, -1)  # set to save in binary mode (0=ASCII, > 1 = binary mode; avoids CR/LF problem decoding)                
                weightSaveFile.close()
                self.writePrint ( 'TrainSimpleNode.tick: Dumped learnedWeights to weightsFile [%s]' % self.WeightsFile )
                self.LoadWeights = False
                
            self.current_path = self.goal_path  # go back to displaying main path
            self.pathTraining_CurrentPath = 0
            
            if not self.reTraining:  # if this is the first time through this code then clear the self-move stack
                self.self_move_stack = []  # clear the self movement stack
                self.reTraining = True 
            
            # send rat to start of maze and see if it can now find the cheese by itself without the training signal
            self.train_cheese_only = False # in case this was on, reset now...
            self.time_learning += 1  # increment once more to allow condition for post learning below to trip...
            self.time_since_last_drop = 0  # reset tick counter...
                
            # where to send rat after learning is done...
            if self.hint_learning:
                # do not send back to start, leave rat where it is
                self.hint_learning = False # reset hint learning flag in case it was on...        TODO-- leave it on?
            
            else:
                
                # stop learning and reset rat to start of maze
                self.time_since_last_drop = 0  # reset tick counter...
                self.InhibitLearning = True              

                self.current_x = round(self.sx,0)
                self.current_y = round(self.sy,0)

                self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)  # kick off rat again what it should have done...to reset signal from cheese lever training or last error
                self.InhibitLearning = False

            # record end of learning in all logs...
            self.BestNextTrainingMoves.GoalMaze.LogLearningOver()  # log through the AStar logging instance so the log can be split easily...
            msg = ('\n\n\nTRACE: TrainSimpleNode:tick- Training turned OFF. XY[%f,%f], BestMoves[%s].\n\n\n' % (self.current_x, self.current_y, self.best_next_move_training_mask) ) 
            self.writePrint ( msg )
                
            self.MapTrainedNet = True      # now mapout how we did on training...
            self.InhibitLearning = True    # turn off learning...
            
        elif self.time_learning > self.learn_time:
            # learning is off, rat moves on its own now...

            self.writePrint("TrainSimpleNode.tick: MOVING by self.")

            self.InhibitLearning = True  
            self.current_path = self.goal_path  # go back to displaying main path
            
            if self.time_since_last_drop > self.selfMoveTime:  # make own moves after training off but wait for network to settle between redrop times...

                self.thisMoveCurrentAccumulator = self.thisMoveAccumulator[:] # make a copy
                self.thisMoveAccumulator = [0,0,0,0,0,0]  # reset the counter...
                self.AccummulateSettleTime = 0

                msg = (("\n\nTRACE: TrainSimpleNode:tick: Accumulated Move Votes: [%s,]. \n\n" ) % (self.thisMoveCurrentAccumulator))
                self.writePrint (msg)                  

                # learning stopped, now at every redrop_time interval, compute the new position from the current and the action the rat chooses as found in thalamus output
                self.time_since_last_drop = 0 # reset drop counter...
                
                # try to apply the action in self.thalamus_move_mask to the (self_current_x, self_current_y) resulting in (post_action_x, post_action_y)
                self.action_number = -1                
                self.writePrint ( 'TrainSimpleNode.Tick: Thalamus output ' +  "%s" %  (self.thisMoveCurrentAccumulator,) + ' Type of thalamus_move_mask:' + "%s" % (type(self.thisMoveCurrentAccumulator),) )

                # determine if there is a clear decision
                actions = self.thisMoveCurrentAccumulator[:]  # take a copy of the current actions... # TODO
                actions.sort(reverse=True)  # sort the copy from highest to lowest
                if actions[0] - actions[1] >= self.decision_tolerance:  # check if there is really a decision here by comparing strongest signal to second strongest...
                    # decision is made, find which command it was
                    try:
                        self.action_number = round(self.thisMoveCurrentAccumulator.index(actions[0]),0)  # find the location of the maximum value, this is the command to then execute
                    except ValueError:
                        msg = 'TrainSimpleNode:tick: No command found. ' + traceStr
                        self.writePrint (msg)
                        self.action_number = -1    # error could not find the max...
                else:
                    # confused, decisions too close to call...
                    self.action_number = -1    # no clear decision at this time...

                msg = ('TRACE: TrainSimpleNode.tick: Current action choosen after learning off is [' + "%s] " % (self.thisMoveCurrentAccumulator, ) + ', Rat should do this action:[' + str(self.action_number,)) + '].'
                self.writePrint ( msg )

                oldActionNum = self.action_number * 1
                
                # if we are to use alternate moves and this cell and move were tried already and it failed then find another move to make...
                if self.AlternateMovesAfterTraining and  [(self.current_x, self.current_y), self.action_number] in self.failed_moves_stack:  # we are to try alternates and this move was already tried here
                    
                    novelMoveFound = False
                    
                    for i in range(1, len(actions)-1):  # loop through available actions to find a movement that has not been tried on this cell before and that is the best choosen (by descending order of thalamus outputs)

                        # Use Second Choice Action? Check if we are in a movement loop, have we tried this before?
                        # Check if there are at least any previous commands, if so were we here and did this same command before, if so choose the next most supported command in the action array...
                        if  ([(self.current_x, self.current_y), self.action_number] in self.failed_moves_stack) or (oldActionNum == self.action_number): # this move has resulted in an error before so choose new one...
                                                
                            # actions list (output of the thalamus) is still sorted by value, so choose the next element and find its action number
                            try:
                                self.action_number = self.thisMoveCurrentAccumulator.index(actions[i])  # try choice i, here we do not concern ourselves with clear choices, any choice will do now as we know the last move failed so we must use another one
                            except ValueError:
                                msg = 'TrainSimpleNode:tick: Error, no alternate choice command found. ' + traceStr
                                self.writePrint (msg)
                                self.action_number = -1    # error could not find the second choice...

                            msg = ('TRACE: TrainSimpleNode.tick: Alternate action choosen, action changed  to [' + "%s] " % (self.thisMoveCurrentAccumulator, ) + ', Rat should do this action:[' + str(self.action_number,)) + '].'
                            self.writePrint ( msg )
                                                
                        if self.isValidMove (self.current_x, self.current_y, self.action_number) and not(oldActionNum == self.action_number):
                            novelMoveFound = True
                            break # this move is new on this cell and valid, so try it...
                        else:
                            pass # go around again and try to find another move to do that is valid...

                    # check if valid move found...
                    if not novelMoveFound:
                        self.action_number = -1 # so report a no move...let cycle from here 
                
                # process action requested...
                if self.action_number == -1:

                    self.ConsequtiveNoActionsChoosen += 1  # keep track of number of no moves, to detect a complete failed situation...
                    
                    # self.action_number == -1 : no command to execute was found, this is caused at startup before the command has settled out \
                    # and also as an error when there is no decision, either way log and ignore and hope network settles out...
                    msg = "TRACE: TrainSimpleNode:tick: NO command to execute found." + traceStr
                    self.writePrint (msg)                                 
                    # do nothing, wait for next command cycle do not move rat, leave current position alone
                    if self.ConsequtiveNoActionsChoosen > 3: # if rat is cycling in place then give a hint or it will loop forever...
                        self.time_since_last_drop = 0  # reset tick counter...
                        self.InhibitLearning = True                                
                        self.current_x = round(self.current_x,0)  # forced exact position cell to end cell...
                        self.current_y = round(self.current_y,0)       
                        self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)  # tell rat again what it should have done...
                        self.InhibitLearning = False

                else:
                    # an action was found to execute
                    
                    self.ConsequtiveNoActionsChoosen = 0
                    
                    if round(self.action_number,0) >= 4 and round(self.action_number,0) <= 5:
                        # rat has requested to pull a lever...

                        if  round(self.current_x,0) == self.ex and round(self.current_y,0) == self.ey:
                            # valid action and we are at the end cell, check if the rat found the cheese...does it pull the correct lever?
                            
                            if round(self.action_number,0) == self.cheese_action:
                                self.self_move_stack.append( [(self.current_x, self.current_y), self.action_number] )
                                # Rat found the cheese!!!
                                self.writePrint ('\n\nSUCCESS: Cheese found by learned behaviours at (x=[%f], y=[%f]) leftLever=[%f], RightLever=[%f]' % ( self.current_x, self.current_y, self.thisMoveCurrentAccumulator[4], self.thisMoveCurrentAccumulator[5] ))
                                self.writePrint("\nTrainSimpleNode:tick: Number of self moves made, succesful=[%f], failed=[%f].\n" % ( len(self.self_move_stack), len(self.failed_moves_stack) ))                            
                                self.writePrint ('\nTrainSimpleNode.tick: Printing moves list used by self-moving to get to the cheese cell [%s]\n' % (self.self_move_stack, ) )
                                self.writePrint("\nTrainSimpleNode:tick: Printng failed moves made=[%s].\n" % ( self.failed_moves_stack) )
                                
                                # pickle final results
                                resultsDataFileName =  self.projectdir + self.fileSep + self.runName + 'SelfMoveResults.pic'
                                resultsDataFileHndl = open( resultsDataFileName,'wb')
                                pickle.dump(self.mappingResults, resultsDataFileHndl, -1)  # set to save in binary mode (0=ASCII, > 1 = binary mode; avoids CR/LF problem decoding)
                                resultsDataFileHndl.close()
                                self.writePrint ( 'TrainSimpleNode:tick: Pickled self move results [%s].' % (resultsDataFileName) )                

				# Close all logger files before trying to copy them...
				self.writePrint ( 'TrainSimpleNode:tick: Closing all logging handlers, preparing to exit jython.' )                
				x = logging._handlers.copy()
				for i in x:
				    self.logger.removeHandler(i)
				    i.flush()
				    i.close()                                                          

                                # Save results files in thier own directory for this run...

                                if self.OSname == 'win':
                                    call ([self.projectdir + self.fileSep + "StoreCheeseResults.bat", self.runName])
                                else:
                                    call ([self.projectdir + self.fileSep + "StoreCheeseResults.sh", self.runName])
                                                                                                                                                            
                                #raise CheeseFoundException                            
                                fatal_error ( 'TrainSimpleNode:tick', 'Success: Cheese found by learned behaviours.')  # stop here by throwing exception...
                                
                            else:
                                #  we are at end cell but rat pulled the wrong lever... :-(...
                                self.self_move_stack.append( [(self.current_x, self.current_y), self.action_number] )
                                self.failed_moves_stack.append ([(self.current_x, self.current_y), self.action_number])  #push on the stack; the current cell, the action intended

                                if not self.AlternateMovesAfterTraining:
                                    if self.hints:
                                        # turn back on training for a short period on this cell
                                        self.train_cheese_only = True
                                        self.time_since_last_drop = 0  # reset tick counter...
                                        self.train_cheese_only = True
                                        
                                        self.InhibitLearning = True
                                        self.current_x = round(self.ex,0)  # forced exact position cell to end cell...
                                        self.current_y = round(self.ey,0)
                                        self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)  # tell rat again what it should have done...
                                        self.InhibitLearning = False

                                        self.hint_learning = True
                                        self.time_learning = 0  # turn learning on again
                                        self.writePrint("TrainSimpleNode.tick: Reset 005 time_learning = learn_time : time_spent_learning=[%f] of total_time_to_learn=[%f]." % (self.time_learning, self.learn_time) )
                                        self.learn_time = self.retrain_time * 1  # set it to learn for a short period of time
                                        
                                    else:
                                        # not to give hints, so simply reinforce where we already are but do not turn on hints_learning
                                        self.time_since_last_drop = 0  # reset tick counter...
                                        self.InhibitLearning = True                                
                                        self.current_x = round(self.current_x,0)  # forced exact position cell to end cell...
                                        self.current_y = round(self.current_y,0)       
                                        self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)  # tell rat again what it should have done...
                                        self.InhibitLearning = False                                

                                msg = "\n\nTRACE: TrainSimpleNode:tick: Rat found cheese cell but pulled wrong lever, turning ON end cell ONLY training again.\n\n " + traceStr
                                self.writePrint (msg)                            
                                
                        else:
                            # we are not at end cell, but rat trying to pull the lever here...
                            # leave current x,y alone, but reinforce the right move again... did not turn on training again here could or could not...experimenting with not...
                            self.failed_moves_stack.append ([(self.current_x, self.current_y), self.action_number])  #push on the stack; the current cell, the action intended
                            self.self_move_stack.append( [(self.current_x, self.current_y), self.action_number] )
                            if not self.AlternateMovesAfterTraining:                          
                                if self.hints:
                                    # turn back on training for a short period on this cell
                                    
                                    self.train_cheese_only = False
                                    self.time_since_last_drop = 0  # reset tick counter...                            

                                    self.InhibitLearning = True
                                    self.current_x = round(self.current_x,0)  # forced exact position cell to end cell...
                                    self.current_y = round(self.current_y,0)                            
                                    self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)  # tell rat again what it should have done...
                                    self.InhibitLearning = False
                                    
                                    self.hint_learning = True
                                    self.time_learning = 0  # turn learning on again
                                    self.writePrint("TrainSimpleNode.tick: Reset 006 time_learning = learn_time : time_spent_learning=[%f] of total_time_to_learn=[%f]." % (self.time_learning, self.learn_time) )                                    
                                    self.learn_time = self.retrain_time * 1  # set it to learn for a short period of time
                                else:
                                    # not to give hints, so simply reinforce where we already are but do not turn on hints_learning
                                    self.time_since_last_drop = 0  # reset tick counter...                                

                                    self.InhibitLearning = True
                                    self.current_x = round(self.current_x,0)  # forced exact position cell to end cell...
                                    self.current_y = round(self.current_y,0)       
                                    self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)  # tell rat again what it should have done...
                                    self.InhibitLearning = False
                            
                            msg = "\n\nTRACE: TrainSimpleNode:tick: Rat tried to pull lever but not at the cheese cell." + traceStr
                            self.writePrint (msg)
                        
                    elif round(self.action_number,0) >= 0 and round(self.action_number,0) <= 3:
                        # it was a movement command; one of (Up/Down/Left/Right = 0/1/2/3)

                        if  round(self.current_x,0) == self.ex and round(self.current_y,0) == self.ey :
                            # rat action is valid movement action (not lever pull), but rat is at the end cell but is trying to move away from the end cell...error!!
                            
                            self.self_move_stack.append( [(self.current_x, self.current_y), self.action_number] )
                            self.failed_moves_stack.append ([(self.current_x, self.current_y), self.action_number])  #push on the stack; the current cell, the action intended                            

                            if not self.AlternateMovesAfterTraining:   
                                    
                                if self.hints:
                                    self.train_cheese_only = True
                                    self.time_since_last_drop = 0  # reset tick counter...

                                    self.InhibitLearning = True                                
                                    self.current_x = round(self.ex,0)  # forced exact position cell to end cell...
                                    self.current_y = round(self.ey,0)
                                    self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)  # tell rat again what it should have done...
                                    self.InhibitLearning = False
                                    
                                    self.hint_learning = True                                
                                    self.time_learning = 0  # turn learning on again
                                    self.writePrint("TrainSimpleNode.tick: Reset 007 time_learning = learn_time : time_spent_learning=[%f] of total_time_to_learn=[%f]." % (self.time_learning, self.learn_time) )                                                                        
                                    self.learn_time = self.retrain_time * 1 # set it to learn for a short period of time
                                    
                                else: # not to give hints, so simply reinforce where we already are but do not turn on hints_learning
                                    self.time_since_last_drop = 0  # reset tick counter...

                                    self.InhibitLearning = True
                                    self.current_x = round(self.ex,0)  # forced exact position cell to end cell...
                                    self.current_y = round(self.ey,0)
                                    self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)  # tell rat again what it should have done...
                                    self.InhibitLearning = False

                            msg = ("\n\nTRACE: TrainSimpleNode:tick: Rat found cheese cell but is trying to MOVE AWAY [action=%f] from the goal cell, turning ON end cell ONLY training again.\n\n" % self.action_number ) + traceStr
                            self.writePrint(msg)
                        
                        else: # not at end cell, so valid to have a movement command here...so move rat...
                            
                            self.self_move_stack.append( [(self.current_x, self.current_y), self.action_number] )
                            
                            self.post_action_x = round(self.current_x,0) + self.x_moves[int(round(self.action_number,0))]   # indexes into the move list x and takes the same element from the x_moves list and adds it to x
                            self.post_action_y = round(self.current_y,0) + self.y_moves[int(round(self.action_number,0))]   # same for y

                            if ( self.post_action_x > self.maze_x - 1 or self.post_action_x < 0 ) or ( self.post_action_y > self.maze_y - 1 or self.post_action_y < 0 ) \
                                or ( ( self.post_action_x, self.post_action_y) in self.walls):
                                
                                # command was processed but there was an error, we moved off the maze

                                self.failed_moves_stack.append ([(self.current_x, self.current_y), self.action_number])  #push on the stack; the current cell, the action intended                                                        
                                if not self.AlternateMovesAfterTraining:                               

                                    if self.reset_to_start_on_error:  # either go back to start and try again or start training again on this location...
                                    
                                        # go back to start when error made and try again
                                        self.post_action = round(self.sx,0)
                                        self.post_action = round(self.sy,0)

                                        self.InhibitLearning = True
                                        self.current_x = round(self.sx,0)
                                        self.current_y = round(self.sy,0)
                                        self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)
                                        self.InhibitLearning = False                                

                                        traceStr = self.UpdateTraceStr()
                                        
                                        # if resulting position is outside the maze, consider this a logic error on the mouse's part and move back to the start of the maze and try again
                                        msg = 'TrainSimpleNode:tick: ERROR : Move would have resulted in leaving maze or or moving onto a wall cell, sending back to start.' + traceStr
                                        self.writePrint (msg)

                                    else:  # not at end cell, tried to move off maze or into a wall, set to re-train on error...so re-train...
                                        
                                        # cause some more training on this location to occur
                                        # no change to current_x or current_y; leave rat in same place
                                        
                                        # turn back on training for a short period on this cell
                                        #self.time_learning = 0  # turn learning on again
                                        #self.learn_time = self.retrain_time  # set it to learn for a short period of time

                                        # round to clear confusion, and then reset training signal on this location...
                                        self.time_since_last_drop = 0  # reset tick counter...

                                        self.InhibitLearning = True
                                        self.current_x = round(self.current_x,0)
                                        self.current_y = round(self.current_y,0)
                                        self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)  # tell rat again what it should have done...
                                        self.InhibitLearning = False
                                        
                                        self.time_since_last_drop = 0  # reset tick counter...                                    
                                        
                                        self.train_cheese_only = False
                                        self.time_since_last_drop = 0  # reset tick counter...

                                        self.time_learning = 0  # turn learning on again
                                        self.writePrint("TrainSimpleNode.tick: Reset 008 time_learning = learn_time : time_spent_learning=[%f] of total_time_to_learn=[%f]." % (self.time_learning, self.learn_time) )                                                                                                                
                                        self.learn_time = self.retrain_time  # set it to learn for a short period of time                                
                                        self.hint_learning = True
                                    
                                    msg = "\n\nTRACE: TrainSimpleNode:tick: Move would have resulted in leaving maze or moving onto a wall cell, turning ON training again.\n\n" + traceStr
                                    self.writePrint(msg)

                            else:  # movement command was processed and rat is still on maze, there was no error, a valid action command, simply update position and best_next_move

                                # VALID ACTION COMMAND..................
                                
                                self.failed_moves_stack = []  # clear the bad moves stack once we have made a succesful move, we start again...
                                self.self_move_stack.append( [(self.current_x, self.current_y), self.action_number] )
                                
                                # move rat to new position now...
                                self.InhibitLearning = True
                                self.current_x = round(self.post_action_x,0)
                                self.current_y = round(self.post_action_y,0)
                                self.time_since_last_drop = 0  # reset tick counter...                         
                                self.best_next_move_training_mask =  self.BestNextTrainingMoves.get_best_next_move_training_mask(self.current_x, self.current_y)  # Learning inhibition is on, project to display in logs only
                                self.InhibitLearning = False

                    else: # an action was found, but the action number returned is not in a valid range, this is a fatal programming design error as the action strings must have been incorrectly specified
                        traceStr = self.UpdateTraceStr()
                        msg = (("TRACE: TrainSimpleNode:tick: Programming error, action code [%f] out of valid range. " + traceStr) % (self.action_number)) + traceStr
                        self.writePrint (msg)                    
                        fatal_error ( 'TrainSimpleNode:tick', msg)
                        
                # log the number of moves made both failed and succesful...
                self.writePrint("TrainSimpleNode:tick: Self moves made, succesful=[%f], failed=[%f]." % ( len(self.self_move_stack), len(self.failed_moves_stack) ))
                    
            else: # learning is off, we are self-moving but it is not yet time to re-move, we are in the let the 'network settle phase' since the last self-move                
                self.time_since_last_drop += 1  # increment time...                
                self.AccummulateSettleTime += 1
                if self.AccummulateSettleTime > self.settle_time :
                    # acummulate : ie: self.thisMoveAccumulator += self.thalamus_move_mask
                    self.thisMoveAccumulator = [ self.thisMoveAccumulator[i] + self.thalamus_move_mask [i] for i in range (len(self.thalamus_move_mask)) ]                
                
        else:
            # this should never happen, programming or system error...
            traceStr = self.UpdateTraceStr()
            msg = (("TRACE: TrainSimpleNode:tick: Programming error, self.time_learning [%f], self.learn_time [%f] invalid values. " + traceStr) % (self.time_learning, self.learn_time)) + traceStr
            self.writePrint (msg)                    
            fatal_error ( 'TrainSimpleNode:tick', msg)

        traceStr = self.UpdateTraceStr()
        # Display what is happening and where we are thinking of going next...
        # Compute where best_next_move action is pointing to move to and then display current position and best next move on the graph...
        
        [ self.thinkingOfMoving_x, self.thinkingOfMoving_y, lever] = self.ThinkingOfActionLookAheadToMove ( self.current_x, self.current_y, self.action_number, self.thalamus_move_mask  )  # or use...self.thisMoveCurrentAccumulator

        bb = self.BestNextTrainingMoves.get_best_next_move_record (self.current_x, self.current_y)
        self.best_next_move_x = bb[0]
        self.best_next_move_y = bb[1]
        lever = [ bb[2] if bb[2] in (4,5) else -1 ]
        
        if [ self.thinkingOfMoving_x, self.thinkingOfMoving_y ] == [-1, -1]: # no valid command found, this can be caused during network settling, so warn and ignore...
                msg = "TRACE: TrainSimpleNode.tick: No valid command to execute found in self.best_next_move_training_mask." + traceStr
                self.writePrint (msg)                                             
        else: # valid action...print the maze out to see where we are
            self.BestNextTrainingMoves.GoalMaze.print_grid(self.current_x, self.current_y, self.best_next_move_x, self.best_next_move_y, True, self.best_next_move_training_mask)
        
        self.writePrint("TrainSimpleNode.tick: Leaving tick() call : time_learning = learn_time : time_spent_learning=[%f] of total_time_to_learn=[%f]." % (self.time_learning, self.learn_time) )
    
    def filter_non_printable(self, istr):
        return ''.join([c for c in istr if ord(c) > 31 or ord(c) == 9])

    def get_data (self):
        return (copy.deepcopy({ 'mazeX' : self.maze_x, 'mazeY' : self.maze_y, 'sx' : self.sx, 'sy' : self.sy,\
               'ex' : self.ex, 'ey' : self.ey,
               'RatX' : self.current_x, 'RatY' : self.current_y , 'walls' : self.walls[:], \
               'path' : self.current_path[:], 'BestNextTrainingMoveX' : self.best_next_move_x, 'BestNextTrainingMoveY' : self.best_next_move_y,\
               'cheeseLever' : self.cheese_action, 'LeverRatPulled' : self.action_number, \
               'CurrentPathNumber' : self.pathTraining_CurrentPath, 'NumberOfPaths' : len(self.BestNextTrainingMoves.get_best_paths()), \
               'TrainingOn' : ( (self.RandomTraining == False and not self.PathTrainingDone) or (self.RandomTraining == True and self.time_learning < self.learn_time) ), \
               'CurrentNodeNumber' :  self.RandomTrainingNodeCount, 'NumberOfNodes' :  ( self.maze_x * self.maze_y )  , 'RandomLearning' : self.RandomTraining, \
               'MappingResults' : self.mappingResults, "thinkingOfMoving_x" : self.thinkingOfMoving_x, "thinkingOfMoving_y" : self.thinkingOfMoving_y}) )
            
    def origin_LearnInhibitionOrigin (self):
        if self.time_learning > self.learn_time or self.InhibitLearning:
            return [float(1)]
        else:
            return [float(0)]
    
    def origin_RatPositionOrigin(self):
        # two dimensional output
        return [float(self.current_x), float(self.current_y)]

    def origin_BestNextTrainingMoveOrigin(self):       
        # return 6-dimensional output
        return [float(self.best_next_move_training_mask[0]), float(self.best_next_move_training_mask[1]), float(self.best_next_move_training_mask[2]),\
                float(self.best_next_move_training_mask[3]), float(self.best_next_move_training_mask[4]), float(self.best_next_move_training_mask[5]) ]

    def termination_thalamus_move_mask_termination (self, x, dimensions=6):        
        self.thalamus_move_mask = [ float(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5]) ] # 6D list of floats (range 0 to 1) for each potential command

class CheeseFoundException (Exception):
    pass
        
# Add to nengo
#inputTemp = TrainSimpleNode('RatMovesInput')
#net.add(inputTemp)

