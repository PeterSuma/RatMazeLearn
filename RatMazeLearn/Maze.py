from __future__ import division
import nef

# this is the actual view object.  It is a standard Swing component, so it has
#  a paintComponent() method that handles whatever drawing you need.  It uses this
#  weird data/watcher system to grab the actual relevant data that should be shown
#  right now (which isn't necessarily the data in the actual object, since we need
#  to handle rewinding the simulation to previous points in time).

from javax.swing import *
from javax.swing.event import *
from java.awt import *
from java.awt.event import *

from javax import imageio
from java import io
import java.lang

import logging
import timeview.components.core as core
import sys
import copy
import os

OSname = java.lang.System.getProperty("os.name").lower()
if OSname.find("win")  > -1 :
    sourcedir = 'F:\\Peter\\Dropbox\\CS 750 - Eliasmith\\Project\\Solution'
elif OSname.find("linux")  > -1 :
    sourcedir = '/home/ctnuser/Pete/ratmaze1'
elif OSname.find("mac") > -1 :
    sourcedir = '/Users/petersuma/Dropbox/CS 750 - Eliasmith/Project/Solution'

# append the working directory to the path to locate AStarPathFinder.py and TrainSimpleNode.py
sys.path.append(sourcedir)
import TrainSimpleNode


class DemoView(core.DataViewComponent):
    
    def __init__(self,view,name,func,args=(),label=None):

        core.DataViewComponent.__init__(self,label)

        self.OSname = java.lang.System.getProperty("os.name").lower()
        if OSname.find("win")  > -1 :
            self.sourcedir = 'F:\\Peter\\Dropbox\\CS 750 - Eliasmith\\Project\\Solution'
            self.graphicsDir = "F:\\Peter\\Dropbox\\CS 750 - Eliasmith\\Project\\Solution"
            self.fileSep = "\\"
        elif OSname.find("linux")  > -1 :
            self.sourcedir = r'/home/ctnuser/Pete/ratmaze1'
            self.graphicsDir = r'/home/ctnuser/Pete/ratmaze1'
            self.fileSep = "/"
            
        #logging.warning("\\n\\n\\n CREATED ANOTHER DEMO VIEW INSTANCE!!! -------------[%s]---------------\\n\\n" % (id(self)) )

        self.view=view
        self.name=name
        self.func=func
        self.show_label=False
        self.update_label()

        self.TraceOn = False

        self.data = self.view.watcher.watch(name,func,args=args)
        
        # icons...
        self.ratFile = io.File(self.graphicsDir + self.fileSep + "Rat.png")
        self.ratImage = imageio.ImageIO.read(self.ratFile)
        
        self.cheeseLeversFile = io.File(self.graphicsDir + self.fileSep + "cheeseLevers.png")
        self.cheeseLeversImage = imageio.ImageIO.read(self.cheeseLeversFile)
        
        self.goLightfile = io.File(self.graphicsDir + self.fileSep + "golight.png")
        self.goLightImage = imageio.ImageIO.read(self.goLightfile)

        self.RatWinsfile = io.File(self.graphicsDir + self.fileSep + "RatWins.png")
        self.RatWinsImage = imageio.ImageIO.read(self.RatWinsfile)
        
        self.TrainingGraphFile = self.graphicsDir + self.fileSep + "MappedMoves.png"
        
        self.QLearnTrainingGraphFile = self.graphicsDir + self.fileSep + "qlearn_decodedMoves.png"
               
        self.trainedCells = []
        self.selfMoves = []
        
        self.TrainingImageFound = False
        self.TrainingGraphImage = None
        
        self.QLearnTrainingImageFound = False
        self.QLearnTrainingGraphImage = None
                
        self.SelfMovesMade = 0

    def XYtoPix (self, x, y, mazeY):
        cellBuffer = 20
        mazeBuffer = 30
        cellSize = 50
        cellSpacing = 2
        cellSpace = cellSize +  cellSpacing
        
        xpix = int(round(mazeBuffer + (x * cellSpace),0))
        ypix = int(round(mazeBuffer + ( ((mazeY) - (y) ) * cellSpace),0))  # y increases from top to bottom, logicals are reverse order
        return (xpix, ypix)

    def writePrint ( self, msg ):
        if self.TraceOn:
             logging.warning (msg)
 
    def paintComponent(self,g):  
        
        core.DataViewComponent.paintComponent(self,g) # call base class paint...

        cellBuffer = 20
        mazeBuffer = 30
        cellSize = 50
        cellSpacing = 2
        cellSpace = cellSize +  cellSpacing

        #TraceOn = True
        
        # grab the current stored data for the time tick being shown
        paintData = self.data.get(start=self.view.current_tick,count=1)[0]

        # we only paint if one of these changes, walls, the base maze and the start/end do not change during the runs
        path = paintData["path"]
        
        RatX = paintData['RatX']  # need to convert to int and round (can't display partial coordinates and jython drawimage calls below need explicit int's
        RatY = paintData['RatY']

        BestNextTrainingMoveX = paintData['BestNextTrainingMoveX']
        BestNextTrainingMoveY = paintData['BestNextTrainingMoveY']

        thinkingOfMoving_x = paintData["thinkingOfMoving_x"]
        thinkingOfMoving_y = paintData["thinkingOfMoving_y"]

        LeverRatPulled = paintData['LeverRatPulled']  # lever the rat pulls...
        
        # load rest of values, note these don't change but cannot be loaded in constructor (that I know of due to callbacks)
        mazeX = paintData['mazeX'] 
        mazeY = paintData['mazeY'] 

        sx = paintData['sx']
        sy = paintData['sy']

        ex = paintData['ex']
        ey = paintData['ey']

        self.oldXY = (-1,-1)
      
        cheeseLever = paintData['cheeseLever']  #the lever where the cheese is
        walls = paintData["walls"]
        CurrentPathNumber = paintData["CurrentPathNumber"]
        NumberOfPaths = paintData["NumberOfPaths"]
        CurrentNodeNumber = paintData["CurrentNodeNumber"]
        NumberOfNodes = paintData["NumberOfNodes"]        
        TrainingOn = paintData["TrainingOn"]
        RandomLearning = paintData["RandomLearning"]
        mappingResults = paintData["MappingResults"]
        mappingResultsXY = [ (x[0], x[1]) for x in mappingResults ]  # just the XY coordinates for indexing 
        
        # Background box...
        g.color = Color(0,255,255)  # light blue
        mazeMaxX = (cellSize * mazeX) + cellBuffer
        mazeMaxY = mazeY - (cellSize * mazeY) + cellBuffer

        # set size of the component on the screen, note cannot be minimized past this        
        self.setSize( int(round(((cellSize * (mazeX)) + cellBuffer + (mazeBuffer * 2)), 0)), 
                      int(round(((cellSize * (mazeY+5)) + cellBuffer + (mazeBuffer * 2))*1.3, 0)) )   

        g.fill3DRect(0 , 0, ((cellSize + cellBuffer) * (mazeX+1)) + mazeBuffer, 
                     ((cellSize + cellBuffer) * (mazeY))-80,   True)

        titleMsg = ''
        
        # Show learning status and progress...
        if TrainingOn:
            
            if not RandomLearning:
                titleMsg = 'Path Learning is ON, Processed %i of %i paths.' % ( CurrentPathNumber, NumberOfPaths )
                
            else:
                titleMsg = 'Random cell learning is ON, Processed %i of %i cells.' % ( CurrentNodeNumber, NumberOfNodes )

            self.trainedCells.append(path[0])  # todo change this to the start of path...
            
        else:
            # training is off...
            
            # plot the results of the training map...
            g.color =  Color(255,255,255) # white
            pwidth = ((cellSize + cellBuffer) * (mazeX+1)) + mazeBuffer
            pheight =  ((cellSize + cellBuffer) * (mazeY+1)) + mazeBuffer

            if not(self.TrainingImageFound):  # try to locate it...
                if os.path.isfile(self.TrainingGraphFile):
                    # image found
                    mapResImage = io.File(self.TrainingGraphFile)
                    self.TrainingGraphImage = imageio.ImageIO.read(mapResImage)
                    self.TrainingImageFound = True
                    
            if not(self.QLearnTrainingImageFound):  # try to locate it...
                if os.path.isfile(self.QLearnTrainingGraphFile):
                    # image found
                    QmapResImage = io.File(self.QLearnTrainingGraphFile)
                    self.QLearnTrainingGraphImage = imageio.ImageIO.read(QmapResImage)
                    self.QLearnTrainingImageFound = True                                
                            
            if ( path[0] ) != self.oldXY: 
                self.SelfMovesMade += 1

                titleMsg = 'Rat navigating on it''s own. %i moves made self navigating so far, %i moves in optimal path.' % ( self.SelfMovesMade, len(path)-1 ) 
                self.oldXY = (path[0]) # store (x,y) of the cell we have processed

                self.selfMoves.append( path[0] )  # todo change this to the start of path...
            else:
                # we have seen this move before, just repaint the screen
                pass
            
        g.color = Color(0,0,0)  # black
        g.drawString(titleMsg, 20, 50)  # put title over the maze...
        
        for x in range (mazeX):
            for y in range (mazeY):

                (xp, yp) = self.XYtoPix(x,y, mazeY)

                if (x, y) == (sx, sy):
                    # go/start cell
                    g.color =  Color(50,205,50) # green
                    g.fill3DRect(xp , yp, cellSize, cellSize, True)
                    (xpi, ypi) = self.XYtoPix(x,y, mazeY)                   
                    g.drawImage(self.goLightImage, xpi+10, ypi+10, self)
                    
                if (x, y) == (ex, ey):
                    # color cheese end cell red to be background for other information icons... 
                    g.color = Color(255,0,0)  # red color
                    g.fill3DRect(xp , yp, cellSize, cellSize, True)
                    
                elif (x, y) in walls:                    
                    # fill in the walls 
                    g.color =  Color(0,0,255) # dark blue
                    g.fill3DRect(xp , yp, cellSize, cellSize, True)
                                     
                else:
                    # check if this cell is in the mapping results and if so change the background color to show if it is a training error or not...
                    
                    try:                    
                        ii =  mappingResultsXY.index((x, y))
                    except:
                        ii = -1
                    
                    if ii >= 0 and mappingResults[ii][2] !=  mappingResults[ii][3]:
                        # this cell was not learned properly, show in red color
                        g.color = Color(255,99,71)  # tomato / light-red color    
                    else:
                        # empty cells where training was correct are just yellow...
                        g.color =  Color(255,255,0) # yellow
                        
                    g.fill3DRect(xp , yp, cellSize, cellSize, True)

                # seperately show the best next move cell 
                if (x, y) == (BestNextTrainingMoveX, BestNextTrainingMoveY):
                    # paint the best next move with a "B"
                    g.color =  Color(0,191,255)    # medium blue color
                    g.fill3DRect(xp + 5 , yp + 5, cellSize - 10, cellSize - 10, True)
                    g.color = Color(0,0,0) # black                    
                    g.drawString("B", xp + cellSize/2, yp + cellSize/2)  # put B in centre...              

                # seperately ontop of whatever is there overlay a bextNextMove marker
                if (x, y) in path:
                    # draw the path and then put the number on top...
                    pNum = [i for i, v in enumerate(path) if v == (x,y)]
                    pNumT = str(pNum) # if len(str(pNum))==1 else " " + str(pNum)
                    g.color =   Color(124,252,0) # light green
                    g.fill3DRect(xp+10 , yp+10, cellSize-20, cellSize-20, True)  # make smaller to show background, shows visually if it thinks to move to a wall for example this way 
                    g.color = Color(0,0,0)  # black
                    g.drawString(pNumT, xp + cellSize/2 - 4, yp + cellSize/2)  # put path number on top...                    

                # seperately show the thinking next cell...
                if (x, y) == (thinkingOfMoving_x, thinkingOfMoving_y):
                    # paint the next thinking of move with a "T"
                    #g.fill3DRect(xp + 5 , yp + 5, cellSize - 10, cellSize - 10, True)
                    #g.color = Color(0,0,0) # black
                    g.color =  Color(255,140,0)    # light orange
                    g.drawString("TnM", xp + cellSize/2 - 20, yp + cellSize/2 + 20)  # put TnM = Thinking of Next Move in centre...      

                if (x, y) == (ex, ey):
                    # cheese end cell sits on top of whatever is there...
                    (xpi, ypi) = self.XYtoPix(x,y, mazeY)                   
                    g.drawImage(self.cheeseLeversImage, xpi+8, ypi+10, self)
                    
                if (x,y) in self.trainedCells:
                    g.color = Color(0,0,0)  # black
                    g.drawString('.', xp + 4, yp + cellSize - 3)  # put a dot at bottom of maze if the rat has trained on this cell already...                    
                    
        # show the self movement history
        if not TrainingOn:
            smi = 1
            for m in self.selfMoves:
                g.color = Color(0,0,0)  # black
                (xpP, ypP) = self.XYtoPix(x,y, mazeY)                
                g.drawString(str(smi), xpP + 4, ypP + cellSize - 3)  # put a number at bottom of maze cell if the rat has moved this way already...
                smi += 1            

        # paint the rat last so it ends up on top of whatever cell it is in
        if type(RatX) in (int, float) and type(RatY) in (int, float) and type(mazeY) in (int, float):
            self.writePrint ( "Maze.DemoView: Rat moving to [%f, %f], pixel coordinates[%f,%f], maze(X,Y)=[%f, %f]." % (RatX, RatY, xpi, ypi, mazeY, mazeX) )    
            g.color =  Color(255,255,255) # white
            (xpi, ypi) = self.XYtoPix(RatX, RatY, mazeY)
            g.drawImage(self.ratImage, int(round(xpi+7,0)), int(round(ypi+7,0)), None)
            
        else:
            self.writePrint("Maze.DemoView: Type mismatch in parameters Rat(X,Y) types[%s, %s], pixel coordinates types[%s,%s], maze types(x,y)=[%s, %s]." %  
                (type(RatX), type(RatY), type(xpi), type(ypi), type(mazeY), type(mazeX)) )
            
        # Paint legend at bottom of screen
        g.color = Color(0,0,0) # black
        (xpi, ypi) = self.XYtoPix(0,0, mazeY)
        
        g.drawString("[x] shows the best next moves path the rat is/was trained on.", xpi + 20, ypi + 68 )
        
        # Check for success: is the rat at the end cell and did it pull the right lever, if so success!
        if ((RatX, RatY) == (ex, ey)) and (LeverRatPulled == cheeseLever):
            g.color =  Color(255,255,255) # white
            g.fill3DRect(0 , 0, ((cellSize + cellBuffer) * (mazeX+1)) + mazeBuffer,
                         ((cellSize + cellBuffer) * (mazeY+1)) + mazeBuffer,   True)            
            g.drawImage(self.RatWinsImage, 0, 0, self)
        
        # draw the graph of the results of training...
        if self.TrainingImageFound:
            g.drawImage(self.TrainingGraphImage, 30, pheight-180, self)
            
        if self.QLearnTrainingImageFound:
            g.drawImage(self.QLearnTrainingGraphImage, 30, pheight-20, self)


# this code adds tells interactive mode to add an option to the right-click menu
#  for any object that passes the check() call.  The views() method gives the
#  text to display in the right-click menu, the type of display to create, 
#  and configures that display.        
class DemoWatch:

    #def __init__ (self):
    #    logging.warning("\\n\\n\\n CREATED ANOTHER DEMO WATCH INSTANCE!!! --------------[%f]--------------\\n\\n" % (id(self)) )

    def check(self, obj):
        return isinstance(obj, TrainSimpleNode.TrainSimpleNode)

    def get_data(self,obj):  # here is how you get data out of the DemoNode
        aa = copy.deepcopy(obj.get_data())
        return aa
    
    def views(self,obj):
        return [('display',DemoView,dict(func=self.get_data,label=obj.name)),
               ]    

