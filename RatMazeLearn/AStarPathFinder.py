from __future__ import division
import cPickle as pickle
import logging
import heapq
import qlearn
import os
from subprocess import call

def fatal_error ( caller, msg ):
    msg = 'ERROR: '+ caller + ' - ' + msg
    raise Exception(msg)

class Cell(object):
    
    def __init__(self, x, y, reachable):
        """
        Initialize new cell

        @param x cell x coordinate
        @param y cell y coordinate
        @param reachable is cell reachable? not a wall?
        """
        self.reachable = reachable
        
        self.x = x
        self.y = y
        self.parent = None
        self.g = 0  # the past path-cost function, which is the known distance from the starting node to the current node
        self.h = 0  # heuristic score ( direct distance to goal cell * 10 )
        self.f = 0  # a future path-cost function, which is an admissible "heuristic estimate" of the distance from  to the goal

class AStar(object):
    
    def __init__(self, gh, gw, sx, sy, ex, ey, walls=[], tracefilename='', cheeseAction=-1, OneLogger=''):

        self.TraceOn = True   

        # logger implementation
        if OneLogger == '':
            self.logger = logging.getLogger('AStarInstance' + '_' + str(id(self)) )
            self.logger.setLevel(logging.DEBUG)
            
            self.logfile = tracefilename + '_' + str(id(self)) + '_AStarInstance.txt'
            self.logfileHandler = logging.FileHandler(self.logfile)
            self.logfileHandler.setLevel(logging.DEBUG)
            self.writePrint('AStar.__init__: Constructor called. tracefilename[%s] paased in. Creating logger[%s].' % (tracefilename, self.logfile))        

            self.consolelogfilehandler = logging.StreamHandler()
            self.consolelogfilehandler.setLevel(logging.DEBUG)
            
            self.logformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            self.consolelogfilehandler.setFormatter(self.logformatter)
            self.logfileHandler.setFormatter(self.logformatter)
            
            self.logger.addHandler(self.consolelogfilehandler)
            self.logger.addHandler(self.logfileHandler)
            
        else:
            self.logger = OneLogger

        self.cheeseAction = cheeseAction  # stores where the cheese is (leftlever=4, rightlever=5)
        
        self.MovesDict = { 'Forward' : 0, 'Back' : 1, 'Left' : 2, 'Right' : 3, 'PressLeftLever' : 4, 'PressRightLever' : 5 }

        self.pathCellList = []

        self.path_found = False

        self.DetailedTraceOn = False

        # debug output control variables; these help to generate useable debug movement output; used by print_grid()
        self.lastPosition = [-1,-1]  # used to track where we were last time print_grid was called, can turn off printing again unless position changes...
        self.callsToPrintGrid = 0  # tracks calls to show time between calls
        self.BestNextTrainingMove = [-1,-1]
              
        self.op = []
        heapq.heapify(self.op)  # turn our list into a heap
        self.cl = set()
        self.cells = []
        
        self.gridHeight = gh
        self.gridWidth = gw

        self.startx = sx
        self.starty = sy
    
        self.endx = ex
        self.endy = ey

        self.walls = walls

        if self.DetailedTraceOn:
            self.writePrint ( 'Model: height=' + str(gh) + 'Width=' + str(gw) + 'StartX=' + str(sx) + 'StartY=' + str(sy) +'EndX=' + str(ex) + 'EndY=' + str(ey) )

        # create the list of cells representing the maze, flag walls as unreaschable...
        for x in range(self.gridWidth):
            for y in range(self.gridHeight):
                if (x, y) in walls:
                    reachable = False
                else:
                    reachable = True
                self.cells.append(Cell(x, y, reachable))
                
        # Assign start cell and end cell...
        self.start = self.get_cell(sx, sy) # create pointers to the start and end cells
        self.end = self.get_cell(ex, ey)
    
    def writePrint ( self, msg ):
        if self.TraceOn:
            self.logger.debug(msg)
                
    def get_heuristic(self, cell):
        """
        Compute the heuristic value H for a cell: distance between
        this cell and the ending cell multiply by 10.

        @param cell
        @returns heuristic value H
        """
        return 10 * (abs(cell.x - self.end.x) + abs(cell.y - self.end.y))

    def get_cell(self, x, y):
        """
        Returns a cell from the cells list

        @param x cell x coordinate
        @param y cell y coordinate
        @returns cell
        """
        if self.DetailedTraceOn:
            self.writePrint ('AStar.get_cell: Fetching cell x=' + str(x) + 'y=' + str(y) + 'gridheight=' + str(self.gridHeight)     + 'cell index=' +  str(x) * self.gridHeight + str(y) )
        # TODO: Return cell that matches x,y...check it...
        return self.cells[x * self.gridWidth + y]

    def get_adjacent_cells(self, cell): 
        """
        Returns adjacent cells to a cell. Clockwise starting
        from the one on the right.

        @param cell get adjacent cells for this cell
        @returns adjacent cells list 
        """
        cells = []

        if cell.x < self.gridWidth - 1:
            xx = cell.x+1
            yy = cell.y
            c = self.get_cell(xx,yy)            
            if (xx,yy) not in self.walls and c.reachable:
                cells.append(c)

        if cell.y > 0:
            xx = cell.x
            yy = cell.y-1
            c = self.get_cell(xx,yy)            
            if (xx,yy) not in self.walls and c.reachable:
                cells.append(c)

        if cell.x > 0:
            xx = cell.x-1
            yy = cell.y
            c = self.get_cell(xx,yy)            
            if (xx,yy) not in self.walls and c.reachable:
                cells.append(c)

        if cell.y < self.gridHeight - 1:
            xx = cell.x
            yy = cell.y+1
            c = self.get_cell(xx,yy)            
            if (xx,yy) not in self.walls and c.reachable:
                cells.append(c)

        return cells

    def generate_path_list(self):
        #self.writePrint ( 'Astar.generate_path_list: Display path:.......' )

        self.pathCellList = []
        cell = self.end
        
        #while cell.parent is not self.start and cell.parent is not None:
        while cell.parent is not None:
            self.pathCellList.append(cell)
            cell = cell.parent
            
        self.pathCellList.append(self.start)

        #self.writePrint ('Astar.generate_path_list: Path...')
        self.pathCellList = self.pathCellList[::-1]  # reverse the list
        
    
    def print_path (self):       
        for p in self.pathCellList:
            if p.reachable:
                self.writePrint ( 'AStar.print_path: cell: (%d,%d), Reachable=True' % (p.x, p.y) )
            else:
                self.writePrint ( 'AStar.print_path: cell: (%d,%d), *******ERRROR *********** Cell is path is NOT REACHABLE!.' % (p.x, p.y) )

    def update_cell(self, adj, cell):
        """
        Update adjacent cell

        @param adj adjacent cell to current cell
        @param cell current cell being processed
        """
        adj.g = cell.g + 10  # update the past path-cost (ie: add 10 as this node cell is now 1 step more away from the start on this path
        adj.h = self.get_heuristic(adj)  # find the cost of the adjacent cell to the finish using the heuristic algorithm
        adj.parent = cell
        adj.f = adj.h + adj.g  # the future cost function is the sum of the past cost (to get to this cell plus the cost to get to the end cell for this adj cell of cell)

    def get_next_best_move (self):
        # First entry is start cell, second is first best move for this maze
        if len(self.pathCellList) >= 2 :
            return self.pathCellList[1]
        else:
            return None   # no moves in best path...

    def print_grid(self, currx = -1, curry = -1, bmx = -1, bmy = -1, newOnly = False, actionmask=[-1,-1,-1,-1,-1,-1], lever=0):
        
        # valid next move found so print the maze with the current position C and the best_next_move B but do not print if position or bnm has not changed           
        if actionmask[4] == 1:
            lever = 4
        elif actionmask[5] == 1:
            lever = 5
        else:
            lever = -1
            
        self.callsToPrintGrid += 1

        if newOnly and ( (self.lastPosition == [currx, curry]) and self.BestNextTrainingMove == [bmx, bmy] ):   # if nothing has changed then don't print...makes logfile easier to read...
            return

        self.lastPosition = [currx, curry]
        self.BestNextTrainingMove = [bmx, bmy]
        
        self.writePrint ('Displaying maze solution (call #[%i]).' % (self.callsToPrintGrid))

        pline = self.gridHeight * [None] # allocate the list ahead of time
        ln = 0
        
        for y in range(self.gridHeight):

            pline[y] = ('\t\t' + str(ln) + '\t')  # put Y axis labels in...
            ln += 1  # decrement Y axis labels down the side
            
            for x in range(self.gridWidth):
                
                p = self.get_cell(x,y)
                if (x, y) in self.walls:
                    onWall = True
                else:
                    onWall = False

                if self.DetailedTraceOn:
                    self.writePrint ( "\n\nAStar.print_grid: PrintLine xy(%f,%f), Current xy(%f, %f), BestNextTrainingMove=(%f,%f), Walls[%s] onWall[%i].\n\n" % (x, y, currx, curry, bmx, bmy, (self.walls,), onWall ) )
                
                if not (currx == -1 or curry == -1) and ( x == currx and y == curry ):
                    # if we are asked to print current position then output a 'C' for current location and do not put other character here 
                    pline[y] += self.formatCellPrint('C', onWall)  # '*C|'= prints C with an * and a | showing it is on a wall, this is an error...
                    
                elif not (bmx == -1 or bmy == -1) and ( x == bmx and y == bmy ):
                    # if we are asked to print best next move position then output a 'B' for current location and do not put other character here
                    pline[y] += self.formatCellPrint('B', onWall)  # '*B|'= prints B with an * and a | showing it is on a wall, this is an error...
                    
                else:
                    
                    if p is self.end:    # if we are now printing out the End cell (note if start and end are same cell, then prints an E for end cell and no S)
                        # display the lever to be pressed (we do not check for walls here, they are not supposed to be on the goal cell :-) )
                        if self.cheeseAction == 4:
                            pline[y] += self.formatCellPrint('EL', onWall)

                        elif self.cheeseAction == 5:
                            pline[y] += self.formatCellPrint('ER', onWall)

                        else:
                            # the cheese lever is not specified yet, just output an E for the end cell...
                            pline[y] += self.formatCellPrint('E', onWall)   # end spot (note: one of the lever commands should have been printed, legacy code)
                            
                            if actionmask[4] != -1:  # only -1 if not supplied by caller to print_grid
                                # if we have no actionmask (ie: called in AStar's constructor where we are path finding not training or navigating) then do not output one...cleans up debug log...
                                self.writePrint ( "\n\nAStar.print_grid: print actionmask [%s].\n\n" % (actionmask,) )
                                msg =  "AStar.print_grid: No cheee lever specified for end cell. [%f, %f, %f, %f, %f, %f]" \
                                   % ( float(actionmask[0]), float(actionmask[1]), float(actionmask[2]), float(actionmask[3]), float(actionmask[4]), float(actionmask[5]) )
                                self.writePrint ( msg )
                            
                    elif p is self.start:
                        # start cell
                        pline[y] += self.formatCellPrint('S', onWall)
                        
                    elif p in self.pathCellList:
                        # cell is on the path
                        ppos = self.pathCellList.index(p)
                        pline[y] += self.formatCellPrint(str(ppos), onWall)
                            
                    elif (x, y) in self.walls:
                        # wall cell
                        pline[y] += self.formatCellPrint('||', False)  # prints a normal wall character '|' with no extra '*||'
                        
                    else:
                        # blank cell
                        pline[y] += self.formatCellPrint('  ', onWall)


        # print in normal order 0 at bottom and left
        for ll in reversed(pline):
            self.writePrint (ll )   # print the maze out...

        # print X axis labels...
        xlab = ''
        for xl in range(self.gridWidth):
            if len(str(xl)) == 1:
                xlab += '_' + str(xl) + '__'
            elif len(str(xl)) == 2:
                xlab += '_' + str(xl) + '_'

        self.writePrint ( '\t\t' + '  ' +  '\t' + ('-' * self.gridWidth * 4 ) )
        self.writePrint ( '\t\t' + 'Y/X' +  '\t' + xlab + '\n' )

        self.writePrint ('List of Walls: [%s].\n' % (self.walls,) )
        self.writePrint ('\nLegend: S=start, E=end/cheese, number=path cell to cheese, |=wall, *=error, B=best next move, R=right lever for cheese, L=left lever for cheese.\n' )
        
        self.writePrint ('End of maze printout.')

    def LogLearningOver (self):
        self.writePrint ('\n\n\n **** Learning Over. Starting self guided mode.\n\n\n')

    def formatCellPrint (self, cellChar, onWall):
        if onWall:
            startChar = '*'
            endChar = '|'
        else:
            startChar = ' '
            endChar = ' '

        cellOut = startChar + cellChar + endChar

        if len(cellOut) == 3:
            padChar = ' '
        else:
            padChar = ''

        return (cellOut + padChar)
                
    def process(self):
        # generates the best path through a maze
        
        self.writePrint ('Start: X=' + str(self.start.x) + 'Y=' + str(self.start.y) )
        
        # add starting cell to open heap queue
        heapq.heappush(self.op, (self.start.f, self.start))  # push the (future cost, start cell) item tuple onto the empty heap of open cells
                                                             # the heap is therefore ordered in such a way that at any gien point the lowest future cost forward is at the top of the heap 
        
        while len(self.op):
            
            # pop cell from heap queue 
            f, cell = heapq.heappop(self.op)  # pop the lowest future cost cell from the top of the heap
            
            # add cell to closed list so we don't process it twice
            self.cl.add(cell)
            
            # if ending cell, display found path
            if cell is self.end:

                self.writePrint ('AStar.process(): Found target cell, path found, calling display_path...')

                self.path_found = True
                self.generate_path_list()
                self.print_path()
                self.print_grid()
                
                break

            # get adjacent cells for cell
            if self.DetailedTraceOn:
                self.writePrint ('Getting adjcents for: X=' + str(cell.x) + 'Y=' + str(cell.y))

            adj_cells = self.get_adjacent_cells(cell)  # find all cells adjacent to cell 
            for c in adj_cells:

                if not(c in self.walls):  # skip walls as starting or path cells...
                        
                    if self.DetailedTraceOn:
                        self.writePrint ( 'X=' + str(c.x) + 'Y=' + str(c.y) )

                    if c.reachable and c not in self.cl:
                        
                        if (c.f, c) in self.op:
                            # if adj cell in open list, check if current path is
                            # better than the one previously found for this adj
                            # cell.
                            if c.g > cell.g + 10:
                                self.update_cell(c, cell)
                                
                        else:
                            self.update_cell(c, cell)
                            # add adj cell to open list
                            heapq.heappush(self.op, (c.f, c))
                        

class NextMovesList (object):

    def __init__(self, gh, gw, sx, sy, ex, ey, walls, tracefilename, cl, OneLogger):

        # logger implementation
        if OneLogger == '':
            self.logger = logging.getLogger('NextMovesListInstance' + '_' + str(id(self)) )
            self.logger.setLevel(logging.DEBUG)

            self.OneLogger = self.logger
            
            self.logfile = tracefilename + '_' + str(id(self)) + 'NextMovesListInstance.txt'
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
            self.OneLogger = OneLogger
            self.logger = OneLogger

        self.TraceOn = True # UNDO
        
        self.MovesDict = { 'Forward' : 0, 'Back' : 1, 'Left' : 2, 'Right' : 3, 'PressLeftLever' : 4, 'PressRightLever' : 5 }

        self.action_mask = '000000'
        
        osdir = os.getcwd()  # this script is run outside of the jython environment in regular python via the call function...
        self.writePrint ( 'OSDir [%s] .' % ( osdir ) )
        if osdir.find('\\') >= 0:
            OSname = 'win'
            graphicsDir = "F:\\Peter\\Dropbox\\CS 750 - Eliasmith\\Project\\Solution\\"
            self.BestMovesCSVFile = graphicsDir + "BestMovesCSVFile.csv"
        else:
            OSname = 'linux'
            graphicsDir = '/home/ctnuser/Pete/ratmaze1/'
            self.BestMovesCSVFile = graphicsDir + "BestMovesCSVFile.csv"        
        
        self.gridHeight = gh
        self.gridWidth = gw

        self.cheeselever = cl  # cheese is under leftlever=4, rightlever=5
        self.startx = sx
        self.starty = sy
    
        self.endx = ex
        self.endy = ey

        self.walls = walls

        self.NextMovesList = {}   # a dict keyed on start pairs [(xs,ys)] with members being the best_next_move cell as Cell object instances [(x1, y1)] on the path to the goal cell from [(xs,ys)]
        self.best_paths = []      # a list of lists; start pairs [(xs,ys)] with members being the whole path to the goal cell as (x,y) pairs  ie: [ [(x1,y2), ((x11, y11), ...)], [(x2,y2), ((x21, y21), ...)] ]
        
        self.tracefilename = tracefilename

        self.cheese_lever = cl

        self.x_moves = [0,0,-1,1,0,0]
        self.y_moves = [1,-1,0,0,0,0]               
                
        self.GoalMaze =  None  #AStar(self.gridHeight, self.gridWidth, self.startx, self.starty, self.endx, self.endy  self.walls, self.tracefilename, self.cheese_lever )

        self.writePrint ('List of best next moves...')

        foundSolution = False

        Nattempts = 4   # number of attempts to construct a non-circular best moves training set list...

        for i in range(1, Nattempts):
            # try x times to create a non-circular list...if not fail....
            # Store the result of the overall start to goal for printing by caller

            if not ( self.GoalMaze == None ):
                del self.GoalMaze
                
            # Compute BestNextTrainingMove list for whole maze from start to end cell...
            self.GoalMaze = AStar(self.gridHeight, self.gridWidth, self.startx, self.starty, self.endx, self.endy, self.walls, self.tracefilename, self.cheese_lever, self.OneLogger )
            self.GoalMaze.process()
            
            for x in range(self.gridWidth):
                for y in range(self.gridHeight):
                    
                    if not((x,y) in self.walls):

                        if not ([x,y] == [ex, ey]):

                            # make sure this cell is not the end cell...
                            
                            self.writePrint ( 'Building maze for position X=' + str(x) + ' Y=' + str(y) )

                            # for every point in the graph find the optimal path to the end and then store the next move found there in self.NextMovesList...
                            # a = AStar(gh, gw, x, y, ex, ey, walls)
                            a = AStar (self.gridHeight, self.gridWidth, x, y, self.endx, self.endy, self.walls, self.tracefilename, self.cheese_lever, self.OneLogger )
                            a.process()  # compute the best path from start to goal
                            bm = a.get_next_best_move()
                            
                            if bm is not None:                            
                                mv = self.convert_xy_to_move(x, y, bm.x, bm.y) 
                                self.NextMovesList[(x, y)] = (bm.x, bm.y, mv)  # mv is the move required to get from (x,y) to (bm.x, bm.y)

                                # Now store whole path from this cell to the goal cell...
                                # append a new paths entry, format is  [ [(x1,y2), ((x11, y11), ...)], [(x2,y2), ((x21, y21), ...)] ]

                                # turn list of path cells into a list of lists for training algorithm to walk in ordered fashion...
                                pTemp = [None for xx in range(len(a.pathCellList))]
                                #pTemp[0] = (x,y)  # put first point in which is start of path
                                for j in range(len(a.pathCellList)):
                                    #pTemp[j+1] = (a.pathCellList[j].x, a.pathCellList[j].y)
                                    pTemp[j] = (a.pathCellList[j].x, a.pathCellList[j].y)

                                self.best_paths.append((pTemp))  # add completed path to bestpathslist
                                
                                self.writePrint ( 'For x=' + str(x) + 'y=' + str(y) + ' best next move is ' + 'x=' + str(bm.x) + 'y=' + str(bm.y) + 'move=' + str(mv) )
                            else:
                                self.writePrint ( 'For x=' + str(x) + 'y=' + str(y) + ' already at goal cell.')
                        else:
                            # we have randomly choosen the goal cell, do not create a rule for this cell as we will manually add a rule below for the cheese lever to pull when we land here
                            pass
                    else:
                        # wall cell, do not make starting path here...
                        pass

            # Add move for the cheese when at the goal cell, pull the left or lever...
            # Move = 4 = cheese on left, move = 5 = cheese on right
            self.NextMovesList[(ex, ey)] = (ex, ey, self.cheeselever)

            # Check for circularity in list...if so abort and do again...
            if not self.findCircular ():
                foundSolution = True
                self.writePrint ( 'NextMovesList.Init(): Found non-circular training matrix on attempt [%i], shown below:' % (i))
                self.print_best_next_moves() # dump the best moves matrix
                self.GoalMaze.print_path()  # dump the path
                self.GoalMaze.print_grid()  # print the maze
                self.writePrint ( 'NextMovesList.Init(): End of non-circular training matrix printout......')          
                break  # the list is good, so break out of this attempts loop 
            elif i == Nattempts:
                # we have tried x times stop now with error...
                self.writePrint ( 'NextMovesList.Init(): ****** Tried to create a non-circular training set of best next moves and failed at attempt [%i], throwing exception to end.. ****' % (i) )               
                self.print_best_next_moves() # dump the best moves matrix
                self.GoalMaze.print_path()  # dump the path
                self.GoalMaze.print_grid()  # print the maze
                fatal_error("NextMovesList.Init()", "Tried to create a non-circular training set of best next moves and failed.")
            else:
                self.print_best_next_moves() # dump the best moves matrix
                self.GoalMaze.print_path()  # dump the path
                self.GoalMaze.print_grid()  # print the maze
                self.writePrint ( 'NextMovesList.Init(): Found circular best next moves set on attempt [%i], trying again..' % (i) )
                
        if not foundSolution:
            self.writePrint ( 'NextMovesList.Init(): ****** Tried to [%i] attempts to create a non-circular training set of best next moves and failed, throwing exception to end.. ****' % (Nattempts) )
            self.print_best_next_moves() # dump the best moves matrix
            self.GoalMaze.print_path()  # dump the path
            self.GoalMaze.print_grid()  # print the maze
            fatal_error("NextMovesList.Init()", "Tried to create a non-circular training set of best next moves and failed.")
        
        # if we get to here we have a non-circular solution set to now train on...so print out the list of best next moves found...
        self.writePrint ( 'NextMovesList.Init(): Summary print out of the BestNextTrainingMovesList...')
        self.print_best_next_moves()
        self.GoalMaze.print_path()  # dump the path
        self.GoalMaze.print_grid()  # print the maze        
        self.writePrint ('NextMovesList.Init(): End of best next moves list...')
        
        # Write out a copy to CSV of the self.NextMovesList data
        import csv        
        csvfileHndl = open(self.BestMovesCSVFile, 'wb')
        spamwriter = csv.writer(csvfileHndl, dialect='excel', quoting=csv.QUOTE_MINIMAL)
        for key, value in self.NextMovesList.iteritems():
            spamwriter.writerow( [key, value] )
        csvfileHndl.close

    def isValidMove (self, currx, curry, post_action_x, post_action_y, action_number_choosen):
        # check if proposed action selected is allowable, ie: doesnt hit a wall
        
        #post_action_x = currx + self.x_moves[action_number_choosen]   # indexes into the move list x and takes the same element from the x_moves list and adds it to x
        #post_action_y = curry + self.y_moves[action_number_choosen]   # same for y
               
        if  action_number_choosen in (0,1,2,3) and (post_action_x, post_action_y) not in self.walls and ( post_action_x in range(0, self.endx+1) and post_action_y in range(0,self.endy+1) ):
            self.writePrint ("TrainSimpleNode.isValidMove: Action [%f] on cell [%f, %f] is valid." % ( action_number_choosen, currx, curry ) ) 
            return True

        elif action_number_choosen in (4,5) and (currx == self.endx and curry == self.endy):  # we are at the end cell...lever pulls are allowed moves (this does not mean it is correct lever though, it is just that is a valid move, not a wall etc...)
            self.writePrint ("TrainSimpleNode.isValidMove: Action [%f] on cell [%f, %f] is valid." % ( action_number_choosen, currx, curry ) )            
            return True
            
        else:
            self.writePrint ("TrainSimpleNode.isValidMove: Action [%f] on cell [%f, %f] is NOT valid." % ( action_number_choosen, currx, curry ) )                        
            return False        
        
    def MakeMoveOnXY (self, x, y, a):
        xx = x + self.x_moves[a]
        yy = y + self.y_moves[a]
        
        if self.isValidMove(x, y, xx, yy, a):
            return (xx, yy)
        else:
            return (-1, -1)
        
    def ComputeActionFromPath (self, x, y, x1, y1):
        if y1 == y + 1 and x1 == x:
            return ([1, 0, 0, 0, 0, 0])  # Up
        elif y1 == y - 1 and x1 == x:
            return ([1, 0, 0, 0, 0, 0])  # Down
        elif x1 == x - 1 and y1 == y:
            return ([1, 0, 0, 0, 0, 0])  # Down
        elif x1 == x + 1 and y1 == y:
            return ([1, 0, 0, 0, 0, 0])  # Down
        elif x == self.endx and y == self.endy and x1 == self.endx and y1 == self.endy:
            # at end cell, correct move is to pull the proper lever
            if self.cheeselever == 4:
                return ( [0, 0, 0, 0, 1, 0] )
            elif self.cheeselever == 5:
                return ( [0, 0, 0, 0, 0, 1] )
        else:
            return -1
    
    def findCircular(self):
   
        # loop over all items in the best moves list
        # follow the path down for each to a maximum of numSpots on grid and see if they all result in finding the goal cell

        # note cannot use normal linked list find circular paths algorithm (fast, slow pointer method) as this is not a linked list,
        # it is a tree structure which has branches leading to same cells but should not them circle regardless of start position.

        for x in range(self.gridWidth):
            for y in range(self.gridHeight):
                if not ((x,y) in self.walls):
                    self.writePrint ( 'Checking best moves path from position X=' + str(x) + ' Y=' + str(y) )
                    nm = [x,y]
                    for m in range(self.gridWidth * self.gridHeight + 2):  # allow up to the number of moves as there are cells in the maze plus 2 for R&L lever pull on last cell....if not found goal by then declare circular best moves array and fail
                        nm = self.get_best_next_move(nm[0], nm[1])
                        foundGoal = False
                        if nm[0] == self.endx and nm[1] == self.endy:
                            foundGoal = True
                            break  # this path is ok so go to next (x,y) pair...

                    if not foundGoal:
                        self.writePrint ("BestNextTrainingMoves.findCircular : Found circular reference in best moves list for path starting at [%f, %f] ending with [%f,%f]." % ( x, y, nm[0], nm[1] ) )
                        return True
                else:
                    pass  # wall cell...
                
        if foundGoal:
            self.writePrint ("BestNextTrainingMoves.findCircular : No circular references found in best moves list." )
            return False

    def writePrint ( self, msg ):
        if self.TraceOn:
            self.logger.debug(msg)
            
    def print_best_next_moves (self):
        
        for key, value in sorted(self.NextMovesList.items()):
            msg = ( 'NextMovesList.print_best_next_moves: %s' % (key,) )  + ( '%s' % (value,) ) 
            self.writePrint ( msg )

    def convert_xy_to_move(self, cx, cy, mx, my):
        
        if not ( (cx == mx) or (cy == my) ):
            self.writePrint ('convert_xy_to_move' + ': Best next move ({0}, {1}) for start cell ({2}, {3}) is not one cell away from start cell.'.format(mx, my, cx,cy))
            fatal_error ('convert_xy_to_move', 'Best next move ({0}, {1}) for start cell ({2}, {3}) is not one cell away from start cell.'.format(mx, my, cx,cy))

        if  ( (cx == mx) and (cy == my) ) and not ( mx == self.endx and my == self.endy ) :
            self.writePrint ('convert_xy_to_move' + \
            ': Best next move ({0}, {1}) is same as cell moving from ({2}, {3}) and not at end cell, if end of moves should be no next move in NextMoves for start cell'.format(mx, my, cx,cy))

            fatal_error ('convert_xy_to_move' + \
            ': Best next move ({0}, {1}) is same as cell moving from ({2}, {3}) and not at end cell, if end of moves should be no next move in NextMoves for start cell'.format(mx, my, cx,cy))
         
        if (cx == mx):  # x is same so look for move up or down in y
            if ( my < cy ):  # move Back/Down
                return self.MovesDict['Back']
            if ( my > cy ):  # move Forward/Up
                return self.MovesDict['Forward']

        if (cy == my):  # y is same so look for move left or right in x
            if ( mx < cx ):  # move left
                return self.MovesDict['Left']
            if ( mx > cx ):  # move Right
                return self.MovesDict['Right']

        self.writePrint ('convert_xy_to_move: Move from ({0}, {1}) to ({2}, {3}) is invalid.'.format(cx, cy, mx, my))

        return -1  # if not returned by now...there is an error..
        
    def mask_action (self, actionid):
        mask_out = ''
        for i in range (len(self.action_mask)):
            if i == actionid:
                tc = '1'
            else:
                tc = self.action_mask[i]
            mask_out += tc
            
        return mask_out
    
    def get_best_path_for_XY (self, x, y):
        for i in range(len(self.best_paths)):
            if self.best_paths[i][0] == (x, y):
                return self.best_paths[i]
        return([(-1,-1)])

    def get_goal_path (self):
        for i in range(len(self.best_paths)):
            if self.best_paths[i][0] == (self.startx, self.starty):
                return self.best_paths[i]
        return([(-1,-1)])    
    
    #
    # AStar Best Moves Path methods used by TrainSimpleNode
    #

    def get_best_paths (self, pathNum=None):
        if pathNum != None:
            return self.best_paths[pathNum]
        return self.best_paths
    
    def get_best_next_move (self, x, y):
        
        bm = self.NextMovesList[(x,y)]        
        if  (x == bm[0] and y == bm[1]) and not ( x == self.endx and y == self.endy ):  # we have found a circle in the best next moves list, but it is not the end cell, this is a fatal error
            self.writePrint("NextMovesList.get_best_next_move()", "Best next moves list returned a circular entry not at the end position for [%f, %f]." % (x,y) )
            fatal_error("NextMovesList.get_best_next_move()", "Best next moves list returned a circular entry not at the end position for xy path=[%f, %f], at bestMove=[%f, %f], path=[%f,]"
                        % ( x, y, bm[0], bm[1], self.NextMovesList(x, y) ) )

        return bm

    def get_best_next_move_record (self, x, y):        
        # self.NextMovesList structure is {(startX,startY), bestNextMovex, bestNextMovey, actionNumberToGetThereFromXY}
        return self.NextMovesList[(x,y)]

    def get_best_next_move_training_mask (self, x, y):
        nm  = self.NextMovesList[(x,y)]
        return self.mask_action(nm[2])  # action number is the 3rd element in the vector, from that number call mask_action to create a mask (ie: mask_action(3) = '000100')

#
#
#  qlearn_NextMovesList Class: qlearn version of NextMovesList class
#
#
class qlearn_NextMovesList (object):

    def __init__(self, gh, gw, sx, sy, ex, ey, walls, tracefilename, cl, OneLogger):

        # logger implementation
        if OneLogger ==  '':
            self.logger = logging.getLogger('qlearn_NextMovesList' + '_' + str(id(self)) )
            self.logger.setLevel(logging.DEBUG)
            
            self.logfile = tracefilename + '_' + str(id(self)) + 'qlearn_NextMovesList.txt'
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
        
        self.useQLearn = True
        self.TraceOn = True
        self.loadQWeights = True
        
        self.action_mask = '000000'          
        
        self.walls = walls
        
        self.gridHeight = gh
        self.gridWidth = gw
        
        self.ex = ex
        self.ey = ey
        
        self.sx = sx
        self.sy = sy
        
        self.BestNextTrainingMoves = NextMovesList (gh, gw, sx, sy, ex, ey, walls, tracefilename, cl, OneLogger)  # create the embedded BestNextMovesList class instance

        self.GoalMaze = self.BestNextTrainingMoves.GoalMaze

        # qlearned values...
        self.useQLearn = True
        
        # Qlearn Parameters:
        #
        # epsilon = chance of random move choosen as opposed to best move
        # alpha = percentage of each trial's reward value that is accumulated for each trial to compose the reward value (smaller = slower, finer learning, larger = faster, coarser learning)
        # gamma = each trial the reward stored is composed of the reward for the current state plus gamma times the reward for the next state...gamma is the reward look-ahead weight effectively
        self.q = qlearn.QLearn([0, 1, 2, 3, 4, 5], epsilon=0.05,alpha=0.9,gamma=0.4, tracefilename=tracefilename, OneLogger=OneLogger, loadQWeights=self.loadQWeights)  # instance of the QLearn class...pass it the range of actions we need...

        # self.NextMovesList structure is {(startX,startY), bestNextMovex, bestNextMovey, actionNumberToGetThereFromXY}   
        self.qlearn_NextMovesList = {}   # a dict keyed on start pairs [(xs,ys)] with members being the best_next_move cell as Cell object instances [(x1, y1)] on the path to the goal cell from [(xs,ys)]
        
        # self.qlearn_best_paths structure is a list of lists; start pairs [(xs,ys)] with members being the whole path to the goal cell as (x,y) pairs  ie: [ [(x1,y2), ((x11, y11), ...)], [(x2,y2), ((x21, y21), ...)] ]
        self.qlearn_best_paths = []      
        
        self.cheeseReward = 5
            
        pathsGood = False
        pathTries = 1
        
        osdir = os.getcwd()  # this script is run outside of the jython environment in regular python via the call function...
        self.writePrint ( 'OSDir [%s] .' % ( osdir ) )
        if osdir.find('\\') >= 0:
            OSname = 'win'
            graphicsDir = "F:\\Peter\\Dropbox\\CS 750 - Eliasmith\\Project\\Solution\\"
        else:
            OSname = 'linux'
            graphicsDir = '/home/ctnuser/Pete/ratmaze1/'
        
        self.qlearn_DataFile =  graphicsDir + r"qlearn_data.pic"               
        self.qlearn_ImageFile =  graphicsDir + r"qlearn_decodedMoves.png"
        self.qlearn_makeImageScript = graphicsDir + "generateQLearnPlot.py"
        self.qlearn_QFile = graphicsDir + "qlearnRawQ.pic"
        self.QBestMovesWeightFile = graphicsDir + "qlearnBestMovesQ.pic"
        
        self.loadQWeights = True
        self.saveQWeights = True
        
        if self.loadQWeights and os.path.isfile(self.qlearn_QFile):
            self.q.unpickleQ()         # unpickles the file self.qlearn_QFile, loads into qLearn.q
            self.unpickleQBestMoves()
            #pathsGood = self.qlearn_create_best_moves_and_paths() # using the populated qLearn object, try to reconstruct the paths from it...
            #self.pickleQBestMoves()
            
        else:            
            for i in range (pathTries):
                self.qlearn_create_reward_matrix()  # train qLearn on the right moves for each cell, 500x per cell...
                pathsGood = self.qlearn_create_best_moves_and_paths() # using the populated qLearn object, try to reconstruct the paths from it...
                if pathsGood:
                    break # if it works stop, else try again...
                else:
                    # try again to build the path...
                    pass
            self.q.pickleQ()  # save the weights calculated...
            self.pickleQBestMoves()
            self.generate_qlearn_move_set_graph()

        # print out the results...        
        self.q.print_qlearn_reward_matrix()        
        self.print_qlearn_best_next_moves()                        
        self.print_qlearn_best_paths()

        if not (pathsGood):
            self.writePrint ('\n\n qlearn_NextMovesList.constructor: ERROR: After [%f] attempts qLearn could not properly learn the paths to the cheese cell from all cells or could not pull the right lever when at the cheese cell.' % (pathTries) )
            #fatal_error('qlearn_NextMovesList.constructor', 'After [%f] attempts qLearn could not properly learn the paths to the cheese cell from all cells or could not pull the right lever when at the cheese cell.' % (pathTries))
        
        else:
            # all good, paths qlearned properly            
            self.writePrint ('\n\n qlearn_NextMovesList.constructor: qlearned paths created without error:\n')            

    def pickleQBestMoves (self):
        fg = open(self.QBestMovesWeightFile, "wb")
        pickle.dump([self.qlearn_NextMovesList, self.qlearn_best_paths], fg, -1)
        fg.close()       
    
    def unpickleQBestMoves (self):
        if self.loadQWeights and os.path.isfile(self.QBestMovesWeightFile):
            fg = open(self.QBestMovesWeightFile, "rb")
            BMunpickle = pickle.load(fg)
            self.qlearn_NextMovesList = BMunpickle[0]
            self.qlearn_best_paths =  BMunpickle[1]
            fg.close()
    
    def writePrint ( self, msg ):
        if self.TraceOn:
            self.logger.debug(msg)
    
    #
    # qlearning methods
    #

    def qlearn_create_reward_matrix (self):

        """        
         - self.NextMovesList now contains a list of [(x,y), bestAction] where bestAction is (0,1,2,3,4,5) = (Up, Down, Left, Right, LeftLever, RightLever)
         - self.best_paths now contains a list of [(x,y), (x1,y1), (x2,y2),...(GoalX, GoalY) ] which is the path from (x,y) to the cheese cell (GoalX, GoalY)
         - need to convert this to the form ((x,y), action, reward, (xNew, yNew))
         - reward is higher if less moves to the goal cell
         - maximum reward should be a function of the maze size
         - reward = maximum reward - cost of getting to cheese cell and pulling the lever
         - cost = number of moves to get to the cheese cell, exponentially rising
         - final output is a matrix of [[x,y], [MoveUpReward, MoveDownReward, MoveLeftReward, MoveRightReward, PullLeftLeverReward, PullRightLeverReward] ]
           with all rewards normalized to a scale from -1...1 so that it can be used as a replacement for the get_best_moves_mask()
         - Rewards:
              self.maxMoveReward = self.gridHeight * self.gridWidth
              self.cheeseReward = self.maxMoveReward
              self.maxQReward = self.cheeseReward + self.maxMoveReward        
         
        """              
       
        trainingCycles = 100
        actionsChoosenPerXY = 10
        
        for t in range (trainingCycles):  # run 500 training cycles...qlearning is incremental
            
            self.writePrint ('\n\n qlearn_NextMovesList.qlearn_create_reward_matrix: Training reward matrix iteration [%f] of [%f].\n' % (t, trainingCycles) ) 
            
            for x in range(self.BestNextTrainingMoves.gridWidth):
                
                for y in range(self.BestNextTrainingMoves.gridHeight):

                    self.writePrint ('\n\n qlearn_NextMovesList.qlearn_create_reward_matrix: Creating reward matrix for (x,y)=[%f, %f].\n' % (x, y) ) 
                    
                    if self.isValidPoint(x, y) and not ((x,y) in self.walls):
                                                
                        # Loop through all actions...                        
                        for i in range (actionsChoosenPerXY):                
                            
                            state =  self.qlearn_ComputeStateFromXY (x, y)
                            
                            if i <= 5:
                                a = i  # run through all actions first once, then choose from qlearn, ensures we explore all first then choose best from there...speeds up learning and is same method we use on learned connection training to compare to later...
                            else:
                                a = self.q.chooseAction(state)
                            
                            (xx, yy) = self.BestNextTrainingMoves.MakeMoveOnXY(x, y, a)
                            
                            # filter if action results in a wall or off the board...skip those...
                            reward = self.qlearn_ComputeRewardFromXYLever (x, y, a, xx, yy)                          
                            newstate =  self.qlearn_ComputeStateFromXYLever (x, y, a, xx, yy)

                            if -1 in (xx, yy, state, a, reward, newstate):
                                self.writePrint ('\n\n qlearn_NextMovesList.qlearn_create_reward_matrix: Invalid qLearn combination for (x,y)=[%f, %f]=state[%f], action=[%f], reward=[%f], newXY=[%f,%f]=newstate=[%f].\n' \
                                                 % (x, y, state, a, reward, xx, yy, newstate) )                            
                            else:
                                self.writePrint ('\n\n qlearn_NextMovesList.qlearn_create_reward_matrix: Valid qLearn combination for (x,y)=[%f, %f]=state[%f], action=[%f], reward=[%f], newXY=[%f,%f]=newstate=[%f].\n' \
                                                 % (x, y, state, a, reward, xx, yy, newstate) )                            
                                #self.q.learn(state, a, reward, newstate)  # q.learn(old_state, action, reward, state)
                            
                            # learn mistakes and all...
                            self.q.learn(state, a, reward, newstate)  # q.learn(old_state, action, reward, state)                            
                            
                    else:
                        # this (x,y) starting cell is a wall or invalid, ignore it, we don't allow the start of paths to be in a wall...moving to a wall is handled above with reward = -1
                        self.writePrint ('qlearn_NextMovesList.qlearn_create_reward_matrix: Skipping wall or invalid cell (x,y)=[%f, %f]' % (x, y) )

        
    # generates a list of the actions the q learn object thinks are the best actions for each (x,y) cell...used to graph the training accuracy of the qlearn class...
    def generate_qlearn_move_set_graph (self):
        
        qlearnActions = []
        for x in range(self.BestNextTrainingMoves.gridWidth):
            for y in range(self.BestNextTrainingMoves.gridHeight):
                if (x, y) not in self.BestNextTrainingMoves.walls:                    
                    state = self.qlearn_ComputeStateFromXY(x, y)
                    qLearn_action = self.q.chooseBestAction(state)
                    bnm = self.BestNextTrainingMoves.get_best_next_move(x, y) 
                    #bestMoveAction = self.BestNextTrainingMoves.convert_xy_to_move(x, y, bnm[0], bnm[1])
                    qlearnActions.append([ x, y, bnm[2], qLearn_action])
                else:
                    # walls; do not start paths from walls
                    qlearnActions.append([ x, y, -1, -1 ])
        """
        # Flatten all paths out to plot paths graph...
        j = 1
        qlbpn = []
        for p in self.qlearn_best_paths:
            for i in range(len(p)):
                qlbpn.append((j, i, p[0], p[1]))
        """                
                    
        # Save the data to a pickle file
        qlearn_DataFileHndl = open( self.qlearn_DataFile,'wb')
        pickle.dump(qlearnActions, qlearn_DataFileHndl, -1)  # set to save in binary mode (0=ASCII, > 1 = binary mode; avoids CR/LF problem decoding)
        qlearn_DataFileHndl.close()
        self.writePrint ( 'qlearn_NextMovesList.generate_qlearn_move_set: Pickled mapped responses [%s].' % ( self.qlearn_DataFile) )                
        
        # Call matplotlib process to generate a graph and display it
        self.writePrint ( 'qlearn_NextMovesList.generate_qlearn_move_set: Now calling [%s].' % ( "python generateQLearnPlot.py" ) )                                
        call ('python "' + self.qlearn_makeImageScript + '"', shell=True)
        self.writePrint ( 'qlearn_NextMovesList.generate_qlearn_move_set: Returned from calling [%s].' % ( "python generateQLearnPlot.py" ) )                     

        return qlearnActions


    def qlearn_create_best_moves_and_paths (self):

        FailOnOneBadPath = False
        
        foundEndCell = True  # flag must live at this level for break out checking...

        for x in range(self.BestNextTrainingMoves.gridWidth):
            
            for y in range(self.BestNextTrainingMoves.gridHeight):
                
                self.writePrint ('\n\n qlearn_NextMovesList.qlearn_create_best_moves_and_paths: Creating best moves and paths for (x,y)=[%f, %f].\n' % (x, y) ) 

                if not ((x,y) in self.BestNextTrainingMoves.walls) and self.isValidPoint(x, y):

                    foundEndCell = False  # reset each completed path per (x,y) cell 
                    
                    # compute and store the first best next move for each location in self.qlearn_NextMovesList
                    actionNum = self.q.chooseBestAction( self.qlearn_ComputeStateFromXY (x, y) )
                    if -1 == actionNum or not ( actionNum <= 5 and actionNum >= 0 ):
                        self.writePrint ('\n\nERROR: qlearn_NextMovesList.qlearn_create_best_moves_and_paths: qlearned path has bad action number on path from start cell (%f, %f) [BestMove Returned (%f,%f)] with qlearned action = [%f].' 
                                         % (x, y, bmXY[0], bmXY[1], actionNum))
                        foundEndCell = False
                        ibestPath = []  # cancel this path out                        

                    else:
                        
                        # apply action number Qlearn says to use...
                        bmXY = self.BestNextTrainingMoves.MakeMoveOnXY(x,y,actionNum)  
                        if -1 in bmXY:
                            self.writePrint ('\n\nERROR: qlearn_NextMovesList.qlearn_create_best_moves_and_paths: qlearned path has bad first move from start cell (%f, %f) [BestMove Returned (%f,%f)] with qlearned action = [%f].' 
                                             % (x, y, bmXY[0], bmXY[1], actionNum))
                            foundEndCell = False
                            ibestPath = []  # cancel this path out                        
    
                        else:
                            self.writePrint ('qlearn_NextMovesList.qlearn_create_best_moves_and_paths: qlearn choose action [%f] from starting cell (%f, %f) which results in cell (%f, %f).' % (actionNum, x, y, bmXY[0], bmXY[1]))
                            
                            self.qlearn_NextMovesList[(x,y)] = [bmXY[0], bmXY[1], actionNum]  #ToDo
                            
                            # populate start of path
                            ibestPath = [(x, y)]
                            
                            # Now populate the path from this cell (x,y): reset to start of path to trace path to the end...
                            nxtX = x + 0
                            nxtY = y + 0                
                            for i in range( int(round(self.BestNextTrainingMoves.gridWidth * self.BestNextTrainingMoves.gridHeight + 1,0)) ):  # allow maximum of mazeX * mazeY + 1 moves to get from start to end on this path...if not then this path fails...
        
                                if self.isValidPoint (nxtX, nxtY):                                                        
                                    s1 = self.qlearn_ComputeStateFromXY (nxtX, nxtY)
                                        
                                    actionNum = self.q.chooseAction( s1 )  # ask qlearn what action to take from this cell...
                                    
                                    if -1 == actionNum or not ( actionNum <= 5 and actionNum >= 0 ):
                                        self.writePrint ('\n\nERROR: qlearn_NextMovesList.qlearn_create_best_moves_and_paths: qlearned path has bad action number on path from start cell (%f, %f) [BestMove Returned (%f,%f)] with qlearned action = [%f].' 
                                                         % (x, y, bmXY[0], bmXY[1], actionNum))
                                        foundEndCell = False
                                        #ibestPath = []  # cancel this path out                        
                                        break
                                    
                                    bmXY = self.BestNextTrainingMoves.MakeMoveOnXY(nxtX,nxtY,actionNum)  # apply the action choosen and compute new cell location...
            
                                    self.writePrint ('\n: qlearn_NextMovesList.qlearn_create_best_moves_and_paths: qlearn choose action [%f] for path with start at (%f, %f) and next cell (%f, %f). ' % (actionNum, x, y, bmXY[0], bmXY[1]))
            
                                    # check for a circle in the path...
                                    if -1 in bmXY:
                                        self.writePrint ('\n\nERROR: qlearn_NextMovesList.qlearn_create_best_moves_and_paths: qlearned path has bad move on path from start cell (%f, %f) [BestMove Returned (%f,%f)] with qlearned action = [%f].' 
                                                         % (x, y, bmXY[0], bmXY[1], actionNum))
                                        foundEndCell = False
                                        #ibestPath = []  # cancel this path out                        
                                        break
                                    
                                    elif (bmXY) in ibestPath and not( len(ibestPath) == 1 and ibestPath[0] == bmXY and actionNum in (4, 5)) :
                                        self.writePrint ('\n\nERROR: qlearn_NextMovesList.qlearn_create_best_moves_and_paths: qlearned path has loop in best_path=(%f, %f) at cell (%f, %f) but did not have correct action to pull cheese lever. Action = [%f]. Maze will not be solved.\n\n' 
                                                         % (x, y, bmXY[0], bmXY[1], actionNum))
                                        foundEndCell = False
                                        #ibestPath = []  # cancel this path out
                                        break # breaks out of path loop
                                    
                                    else:
                                        # this next cell in the path is not a circle so add it to the path...
                                        if not( len(ibestPath) == 1 and ibestPath[0] == bmXY and actionNum in (4, 5)):  # check if this is the last lever pull, do not add to path if so as it is already there...
                                            ibestPath.append(bmXY)  # store this action in qlearn_best_paths()  #TODO: check structure here of records...
                                        else:
                                            # we are already at the end cell and it is in the path, do not add the end cell again...
                                            pass
                                            
                                        # Check for cheese lever pull if we are at the end cell..
                                        if (nxtX, nxtY) == (self.BestNextTrainingMoves.endx, self.BestNextTrainingMoves.endy):
                
                                            # we are at the end cell, check for next action being lever pull
                                            actionNum = self.q.chooseAction( self.qlearn_ComputeStateFromXY (bmXY[0], bmXY[1]) )
                
                                            if actionNum != self.BestNextTrainingMoves.cheeselever:
                                                # this run will fail send warning about it...but log it so it shows in experimental results later...
                                                self.writePrint ('\n\n\ERROR: qlearn_NextMovesList.qlearn_create_best_moves: qlearned path got to end cell for path (%f, %f) at cell (%f, %f) but did not have correct action to pull cheese lever. Action = [%f]. Maze will not be solved.\n\n\n'
                                                                 % (x,y, bmXY[0], bmXY[1], actionNum))
                                                foundEndCell = False  # we found the end cell but did not pull the right cheese lever...
                                                #ibestPath = []  # cancel this path out                                                                                                    

                                            else:
                                                # store the lever pull action for the end cell and end path search...
                                                self.qlearn_NextMovesList[(nxtX, nxtY)] = [bmXY[0], bmXY[1], actionNum]
                                                foundEndCell = True
                                                #ibestPath = []  # cancel this path out     
                                            
                                            break # breaks out of path loop
        
                                        else:
                                            # we are not at the end cell, we are at a cell along the path, so set this cell as the new start and get next move in path...
                                            nxtX = bmXY [0] + 0
                                            nxtY = bmXY [1] + 0
                                            
                                else:
                                    # we have walked off the maze in traversing the path...this path is dead...
                                    self.writePrint ('\n\n\ERROR: qlearn_NextMovesList.qlearn_create_best_moves: qlearned path walked off the maze for path (%f, %f) at cell (%f, %f). Action = [%f]. Maze will not be solved.\n\n\n'
                                                     % (x,y, nxtX, nxtY, actionNum))                            
                                    #ibestPath = []  # cancel this path out                             
                                    break # breaks out of path loop

                    # finished walking this path for this one start cell (x,y) to endcell or we maxed out the number of moves, or the path was broken or ended in a circle...
                    if not(foundEndCell):
                        self.writePrint ('\n\n\ERROR: qlearn_NextMovesList.qlearn_create_best_moves: path loop: qlearned path (%f, %f) did not get to end cell. Path [%s,] ended at (%f, %f) last action (%f). \n\n\n'
                                         % (x, y, ibestPath, bmXY[0], bmXY[1], actionNum))
                        if FailOnOneBadPath:
                            break # breaks out of path loop
                        else:
                            pass
                            #ibestPath = []  # cancel this path out                        
                    else:
                        if ibestPath != []:
                            self.qlearn_best_paths.append(ibestPath)  # add whole path for this (x,y) cell to list of qlearn_best_paths
                        else:
                            self.writePrint ('\n\n\ERROR: qlearn_NextMovesList.qlearn_create_best_moves: path loop: qlearned path claims to have found encell but path is empty, from (%f, %f). Path [%s,] ended at (%f, %f) after (%f) moves. Retraining.\n\n\n'
                                             % (x, y, ibestPath, bmXY[0], bmXY[1], actionNum))                           
                        
                else:
                    # If wall on not valid point : this is a wall cell otr invalid point, nothing to do we just don't start paths inside a wall or invalid cells is all...
                    self.writePrint ('\n\n\ERROR: qlearn_NextMovesList.qlearn_create_best_moves: path loop: Skipping wall or invalid cell (%f, %f).\n' % (x, y))

                # inside y loop: break out if failed...
                if not(foundEndCell):
                    self.writePrint ('\n\n\ERROR: NextMovesList.qlearn_create_best_moves: y-loop: qlearned path (%f, %f) did not get to end cell. Path ended at (%f, %f) after (%f) moves. Retraining.\n\n\n'
                                     % (x, y, bmXY[0], bmXY[1], actionNum))
                    if FailOnOneBadPath:
                        break # breaks out of path loop
                    else:
                        ibestPath = []  # cancel this path out     

            # inside of x loop : break out if failed...
            if not(foundEndCell):
                self.writePrint ('\n\n\ERROR: qlearn_NextMovesList.qlearn_create_best_moves: x-loop: qlearned path (%f, %f) did not get to end cell. Path ended at (%f, %f) after (%f) moves. Retraining.\n\n\n'
                                 % (x, y, bmXY[0], bmXY[1], actionNum))
                if FailOnOneBadPath:
                    break # breaks out of path loop
                else:
                    ibestPath = []  # cancel this path out     

        if not(foundEndCell):
            # we did not find the end cell in at least one path, the path either had a circle or reached the end cell but did not pull the right lever...
            return False
        else:
            return True  # last path completed and all paths found... qlearn_best_paths is populated correctly...


    def isValidPoint (self, x, y):
        # check if proposed action selected is allowable, ie: doesnt hit a wall
        
        if (x, y) not in self.walls and ( x in range(self.gridWidth) and y in range(self.gridHeight) ):
            self.writePrint ("qlearn_NextMovesList.isValidPoint: Cell [(%f,%f)] is valid." % ( x, y) ) 
            return True
        else:
            self.writePrint ("qlearn_NextMovesList.isValidPoint: Cell [(%f,%f)] is NOT valid." % ( x, y) ) 
            return False

    def qlearn_ComputeStateFromXY (self, x, y):
        # compute the state as a sequential number, start from zero in bottom left corner
        if self.isValidPoint(x, y) and not((x, y) in self.walls):
            return (self.BestNextTrainingMoves.gridHeight * y) + x
        else:
            return -1
        
    def qlearn_ComputeStateFromXYLever (self, x, y, action, xx, yy):
        # model the lever pulls as simply two additonal cells on the maze
        if (x, y) == (self.BestNextTrainingMoves.endx, self.BestNextTrainingMoves.endy) and (xx, yy) == (self.BestNextTrainingMoves.endx, self.BestNextTrainingMoves.endy):
            # we are on the goal cell and the next action is the lever pull
            if action == self.BestNextTrainingMoves.cheeselever:
                return (self.BestNextTrainingMoves.endy * self.BestNextTrainingMoves.endx) + 2  # create the last state as the cheese reward state
            elif action != self.BestNextTrainingMoves.cheeselever and action in (4, 5):
                return (self.BestNextTrainingMoves.endy * self.BestNextTrainingMoves.endx) + 1  # one state below is the wrong action
            else:
                # we are at end cell but the action is not a lever pull...so this is an error
                return -1
        else:          
            # compute the state as a sequential number
            return (self.qlearn_ComputeStateFromXY(x, y)) # TODO: adjust for off maze moves etc...
        
    
    def qlearn_ComputeRewardFromXYLever (self, x, y, action, xNew, yNew ):

        if -1 in (x, y, action, xNew, yNew ):
            reward = -1  # failure: if any of the current state, the future state or the action are invalid, then everything is invalid in this combination
            
        elif (xNew not in range(self.BestNextTrainingMoves.gridWidth) or yNew not in range(self.BestNextTrainingMoves.gridHeight) or (xNew, yNew) in self.BestNextTrainingMoves.walls):
            reward = -1  # failure: moved off the board or walked into a wall....
        
        elif action in (4, 5) and (x, y) != (self.BestNextTrainingMoves.endx, self.BestNextTrainingMoves.endy):
            # we are not at the end cell, but using a lever pull as the action, error...
            self.writePrint ('\n\n qlearn_NextMovesList.qlearn_ComputeRewardFromXYLever: Error lever pull requested when not yet at the end cell; for move(x,y)=[%f, %f] to newXY=[%f,%f] using action [%f]. Inconsistent, action does produce this move.\n'
                             % (x, y, xNew, yNew, action) )
            reward = 0  # not a failure, just a bad move
                    
        elif (xNew, yNew) == (self.BestNextTrainingMoves.endx, self.BestNextTrainingMoves.endy) and (x, y) != (self.BestNextTrainingMoves.endx, self.BestNextTrainingMoves.endy) and action in (4, 5):
            # we are requested to move to the end cell, but using a lever pull as the action, inconsistent
            self.writePrint ('\n\n qlearn_NextMovesList.qlearn_ComputeRewardFromXYLever: Error reward requested for move(x,y)=[%f, %f] to newXY=[%f,%f] using action [%f]. Inconsistent, action does produce this move.\n'
                             % (x, y, xNew, yNew, action) )
            reward = 0  # not a failure, just a bad move
            
        elif (xNew, yNew) == (self.BestNextTrainingMoves.endx, self.BestNextTrainingMoves.endy) and (x, y) == (self.BestNextTrainingMoves.endx, self.BestNextTrainingMoves.endy):
            
            # we are standing at the end cell, check which lever pulled...            
            if action == self.BestNextTrainingMoves.cheeselever:
                #reward = self.cheeseReward
                reward = 1000
                self.writePrint ('\n\n qlearn_NextMovesList.qlearn_ComputeRewardFromXYLever: At end cell pulled right lever. FOUND CHEESE. Reward computed for move(x,y)=[%f, %f] to newXY=[%f,%f] using action [%f] is [%f].\n' % (x, y, xNew, yNew, action, reward) )
                
            else:
                reward = 0  # not a failure, just bad move; negative incentive for pulling wrong lever...
                self.writePrint ('\n\n qlearn_NextMovesList.qlearn_ComputeRewardFromXYLever: At end cell but pulled wrong lever. Reward computed for move(x,y)=[%f, %f] to newXY=[%f,%f] using action [%f] is [%f].\n' % (x, y, xNew, yNew, action, reward) )
                
        elif (xNew, yNew) == (x, y):
            # did not move and not at the end cell (caught above)
            reward = 0  # not failure, bad move though
            self.writePrint ('\n\n qlearn_NextMovesList.qlearn_ComputeRewardFromXYLever: Current and next cells are same. Reward computed for move(x,y)=[%f, %f] to newXY=[%f,%f] using action [%f] is [%f].\n' % (x, y, xNew, yNew, action, reward) )
        
        elif xNew in range(self.BestNextTrainingMoves.gridWidth) and yNew in range(self.BestNextTrainingMoves.gridHeight) \
             and (xNew, yNew) not in self.BestNextTrainingMoves.walls and action in (0, 1, 2, 3):

            bnMvXY = self.BestNextTrainingMoves.get_best_next_move(x, y)
            if (bnMvXY[0], bnMvXY[1])== (xNew, yNew):
                reward = 500
            else:
                # reward based on distance from cheese
                
                # we are not at the end cell or we are just moving to it...and the reward equals the differnece in path costs to the cheese cell...
                bpxy = self.BestNextTrainingMoves.get_best_path_for_XY (x, y)
                if -1 in bpxy:
                    currentPathCost = computePathDistance (x, y, self.ex, self.ey)
                else:
                    currentPathCost = len(bpxy)
                    
                bpNewxy = self.BestNextTrainingMoves.get_best_path_for_XY (xNew, yNew)
                if -1 in bpNewxy:
                    newPathCost = computePathDistance (xNew, yNew, self.ex, self.ey)
                else:
                    newPathCost = len(bpNewxy)
                    
                if newPathCost < currentPathCost :
                    reward = 2 * ( currentPathCost - newPathCost ) * 100 # if new is less than current; a reward is given, else reward is negative or zero if same...
                elif newPathCost > currentPathCost :
                    reward = -1000
                elif newPathCost == currentPathCost :
                    reward = -200 

            self.writePrint ('\n\n qlearn_NextMovesList.qlearn_ComputeRewardFromXYLever: Reward computed for move(x,y)=[%f, %f] to newXY=[%f,%f] using action [%f] is [%f].BestNextMove=[%s]' % (x, y, xNew, yNew, action, reward, bnMvXY))
            
        else:
            # some unacceptable move has happened...
            self.writePrint ('\n\n qlearn_NextMovesList.qlearn_ComputeRewardFromXYLever: Error reward requested for move(x,y)=[%f, %f] to newXY=[%f,%f] using action [%f].\n' % (x, y, xNew, yNew, action) )
            reward = -1
            
        return reward

    def computePathDistance (x1, y1, x2, y2):
        return (x2 - x1) + (y2 - y1)
                                                   
    def qlearn_get_best_moves_mask (self, x, y):
        return self.q.getQValuesForActionsVectorNeg11Scaled( self.qlearn_ComputeStateFromXY(x,y) )      

    #
    # overridden functions
    #    
    def get_best_paths (self, pathNum=None):
        if pathNum != None:        
            return self.qlearn_best_paths[pathNum]
        return self.qlearn_best_paths
    
    def get_best_next_move (self, x, y):
        a = self.q.chooseAction( self.qlearn_ComputeStateFromXY(x,y) )
        bm = self.MakeMoveOnXY(x,y,a)
        if  (x == bm[0] and y == bm[1]) and not ( x == self.endx and y == self.endy ):  # we have found a circle in the best next moves list, but it is not the end cell, this is a fatal error
            self.writePrint("qlearn_NextMovesList.get_best_next_move(): qlearn_Best next moves list returned a circular entry not at the end position for [%f, %f]." % (x, y) )
            fatal_error("qlearn_NextMovesList.get_best_next_move()", "qlearn_Best next moves list returned a circular entry not at the end position for [%f, %f]." % (x, y) )
        return bm

    def get_best_next_move_record (self, x, y):
        # self.NextMovesList structure is {(startX,startY), bestNextMovex, bestNextMovey, actionNumberToGetThereFromXY}                            
        return self.qlearn_NextMovesList[(x, y)] 

    def get_best_next_move_training_mask (self, x, y):
        nm  = self.qlearn_NextMovesList[(x, y)] 
        self.writePrint("qlearn_NextMovesList.get_best_next_move_training_mask: best next move record=[%s]" % nm)
        tmm = self.mask_action(nm[2])
        self.writePrint("qlearn_NextMovesList.get_best_next_move_training_mask: mask=[%s]" % tmm)
        return tmm

    def get_goal_path (self):
        for i in range(len(self.qlearn_best_paths)):
            if self.qlearn_best_paths[i][0] == (self.sx, self.sy):
                return self.qlearn_best_paths[i]
        return([(-1,-1)])    
   
    def mask_action (self, actionid):
        mask_out = ''
        for i in range (len(self.action_mask)):
            if i == actionid:
                tc = '1'
            else:
                tc = self.action_mask[i]
            mask_out += tc
            
        return mask_out   
   
    #
    # display functions...
    #
    def print_qlearn_best_paths (self):
        self.writePrint( 'qlearn_NextMovesList.print_qlearn_best_paths: Starting print out of qlearn_best_paths list. Number of paths to print [%f]' % (len(self.qlearn_best_paths)))
        i = 0
        for p in sorted(self.qlearn_best_paths ):
            self.writePrint( 'qlearn_NextMovesList.print_qlearn_best_paths: path [%f] = %s' % (i, p) )
            i += 1

    def print_qlearn_best_next_moves (self): 
        self.writePrint( 'qlearn_NextMovesList.print_qlearn_best_next_moves: Starting print out of qlearn_best_nest_moves dictionary:...')
        for key, value in sorted(self.qlearn_NextMovesList.items()):
                self.writePrint( ('qlearn_NextMovesList.print_qlearn_best_next_moves: %s,' % (key,) ) + ( '%s' % (value,)) )
