import os
from subprocess import call

osdir = os.getcwd()  # this script is run outside of the jython environment in regular python via the call function...
print ('OSDir [%s] .' % ( osdir ) )

OSWin = False
OSLinux = False
OSMac = False

if osdir.find('\\') >= 0:
    OSWin = True
else:
    OSLinux = True   

if OSWin:
    OSWin = True
    os.system("F:")
    projectdir = 'F:\\Peter\\Dropbox\\CS 750 - Eliasmith\\Project\\Solution'
    nengoDir = 'F:\\Peter\\Dropbox\\CS 750 - Eliasmith\\Nengo\\nengo-1.4\\nengo-e6343ec'
    nengoExe =  nengoDir + '\\nengo-cl'
    ratMazePy =  projectdir +  '\\RatMazeLearn14.py'
       
elif OSLinux:
    OSLinux = True
    projectdir = '/home/ctnuser/Pete/ratmaze1'
    nengoDir = 'home/ctnuser/Pete/nengo'
    nengoExe =  nengoDir + '/nengo-cl'
    ratMazePy =  projectdir +  '/RatMazeLearn14.py'
    
os.system("cd " + projectdir)    

#
# RatMazeLearn.py - Command line arguments:
#
# ie: for Qlearning with easy walls :
#              nengo-cl RatMazeLearn.py QLearnEasyWalls B Q E
#
# [0] = name of nengo script "RatMazeLearn.py"
# [1] = a name given to this run ie: "MediumWallsWithQLearn", final results file will be saved with this name as a prefix, so no special characters or spaces
# [2] = "B" or "I" (BatchMode or Interactive[default])
# [3] = "Q" or "-Q" (Qlearn or no QLearn[default])
# [4] = "N" or "E" or "M" or "H" (walls None, Easy[default], Medium or Hard)

# With QLearning
print "Example command line:"
print nengoExe, ratMazePy, "QlearnNoWalls", "B", "Q", "N"

call([nengoExe, ratMazePy, "QlearnNoWalls", "B", "Q", "N"], shell=True)
call([nengoExe, ratMazePy, "QlearnEasyWalls", "B", "Q", "E"], shell=True)
call([nengoExe, ratMazePy, "QlearnMediumWalls", "B", "Q", "M"], shell=True)
call([nengoExe, ratMazePy, "QlearnHardWalls", "B", "Q", "H"], shell=True)

# Without QLearning
call([nengoExe, ratMazePy, "QlearnNoWalls", "B", "-Q", "N"], shell=True)
call([nengoExe, ratMazePy, "QlearnEasyWalls", "B", "-Q", "E"], shell=True)
call([nengoExe, ratMazePy, "QlearnMediumWalls", "B", "-Q", "M"], shell=True)
call([nengoExe, ratMazePy, "QlearnHardWalls", "B", "-Q", "H"], shell=True)

