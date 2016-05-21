echo on
f:
cd "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution"

REM   nengoDir = 'F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec'
REM    nengoExe =  nengoDir + '\nengo-cl'
REM ratMazePy =  projectdir +  '\RatMazeLearn14.py'

REM
REM RatMazeLearn.py - Command line arguments:
REM
REM ie: for Qlearning with easy walls :
REM              nengo-cl RatMazeLearn.py QLearnEasyWalls B Q E
REM
REM [0] = name of nengo script "RatMazeLearn.py"
REM [1] = a name given to this run ie: "MediumWallsWithQLearn", final results file will be saved with this name as a prefix, so no special characters or spaces
REM [2] = "B" or "I" (BatchMode or Interactive[default])
REM [3] = "Q" or "-Q" (Qlearn or no QLearn[default])
REM [4] = "N" or "E" or "M" or "H" (walls None, Easy[default], Medium or Hard)

REM  Example command line:"
REM      nengo-cl ratMazePy.py QlearnNoWalls B Q N

REM RANDOM TRAINING...........................

REM With QLearning 
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" RandomQlearnNoWalls B Q N R
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" RandomQlearnEasyWalls B Q E R
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" RandomQlearnMediumWalls B Q M R
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" RandomQlearnHardWalls B Q H R

REM without Qlearning
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" RandomNoQlearnNoWalls B -Q N R
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" RandomNoQlearnEasyWalls B -Q E R
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" RandomNoQlearnMediumWalls B -Q M R
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" RandomNoQlearnHardWalls B -Q H R



REM PATH TRAINING...........................

REM With QLearning 
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" PathQlearnNoWallsPathTrain1000N B Q N P
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" PathQlearnEasyWalls B Q E P
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" PathQlearnMediumWalls B Q M P
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" PathQlearnHardWalls B Q H P

REM without Qlearning
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" PathNoQlearnNoWalls B -Q N P
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" PathNoQlearnEasyWalls B -Q E P
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" PathNoQlearnMediumWalls B -Q M P
"F:\Peter\Dropbox\CS 750 - Eliasmith\Nengo\nengo-1.4\nengo-e6343ec\nengo-cl" "F:\Peter\Dropbox\CS 750 - Eliasmith\Project\Solution\RatMazeLearn14.py" PathNoQlearnHardWalls B -Q H P

