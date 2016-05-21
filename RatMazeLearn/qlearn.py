from __future__ import division
import random
import logging
import os
import cPickle as pickle

class QLearn:
  
  def __init__(self,actions,epsilon=0.05,alpha=0.2,gamma=0.9, tracefilename='', OneLogger='', loadQWeights=True):
    
    # Qlearn Parameters:
    # epsilon = chance of random move choosen as opposed to best move
    # alpha = percentage of each trial's reward value that is accumulated for each trial to compose the reward value (smaller = slower, finer learning, larger = faster, coarser learning)
    # gamma = each trial the reward stored is composed of the reward for the current state plus gamma times the reward for the next state...gamma is the reward look-ahead weight effectively
    
    self.TraceOn = True
    self.loadQWeights =  loadQWeights
    
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
        
    # set graphicsFile 
    osdir = os.getcwd()  # this script is run outside of the jython environment in regular python via the call function...
    self.writePrint ( 'OSDir [%s] .' % ( osdir ) )
    if osdir.find('\\') >= 0:
        OSname = 'win'
        graphicsDir = "F:\\Peter\\Dropbox\\CS 750 - Eliasmith\\Project\\Solution\\"
    else:
        OSname = 'linux'
        graphicsDir = '/home/ctnuser/Pete/ratmaze1/'        

    self.QWeightFile = graphicsDir + "qlearnRawQ.pic"
    
    self.q={}

    self.epsilon=epsilon
    self.alpha=alpha
    self.gamma=gamma
    self.actions=actions

  def getQ(self,state,action):
    return self.q.get((state,action),0.0)
  
  def learnQ(self,state,action,value):
    oldv=self.q.get((state,action),None)
    if oldv==None:
      self.q[(state,action)]=value
    else:
      self.q[(state,action)]=oldv+self.alpha*(value-oldv)
      
  def learn(self,state1,action1,reward,state2):
    maxqnew=max([self.getQ(state2,a) for a in self.actions])
    self.learnQ(state1,action1,reward+self.gamma*maxqnew)      

  def chooseAction(self,state):
    
    if random.random()<self.epsilon:
      action=random.choice(self.actions)
    else:
      q=[self.getQ(state,a) for a in self.actions]
      maxQ=max(q)
      count=q.count(maxQ)
      if count>1:
        best=[i for i in range(len(self.actions)) if q[i]==maxQ]
        i=random.choice(best)
      else:
        i=q.index(maxQ)

      action=self.actions[i]
    
    return action
  

  def chooseBestAction(self,state):
    
    q=[self.getQ(state,a) for a in self.actions]
    maxQ=max(q)
    count=q.count(maxQ)
    if count>1:
      best=[i for i in range(len(self.actions)) if q[i]==maxQ]
      i=random.choice(best)
    else:
      i=q.index(maxQ)
    action=self.actions[i]    
    return action 

  def getQValuesForActionsVector (self, state):
    
    # return a tuple of the q-values for each possible action
    qvs = [0] * len(self.actions)
                    
    i = 0
    for a in self.actions:

      try:
        qv = self.q[(state,a)]
      except:
        qv = 0   # this action has no qvalue so use zero for neutral...
        
      qvs[i] = qv
      
      i += 1  # next action...

    return qvs

  def getQValuesForActionsVector01Scaled (self, state):
    
    qvs = self.getQValuesForActionsVector (state)
    qvsScaled = [0] * len(qvs)
    
    qvsMax = max(qvs)
    qvsMin = min(qvs)
    
    qvsRange = qvsMax - qvsMin

    for i in range(len(qvs)):
      qvsScaled[i] = (qvs[i] - qvsMin) / qvsRange
      
    return qvsScaled

  def getQValuesForActionsVectorNeg11Scaled (self, state):
    gmax = max([value for key, value in self.q.iteritems()])
    gmin = min([value for key, value in self.q.iteritems()])
    gRange = max(abs(gmax), abs(gmin))
    
    qvs = self.getQValuesForActionsVector (state)
    qvsScaled = [0] * len(qvs)

    for i in range(len(qvs)):
      qvsScaled[i] = self.remap(qvs[i], -gRange, gRange, -1, 1)
      
    return qvsScaled


  def remap( self, x, oMin, oMax, nMin, nMax ):

    #range check
    if oMin == oMax:
        print "Warning: Zero input range"
        return None

    if nMin == nMax:
        print "Warning: Zero output range"
        return None

    #check reversed input range
    reverseInput = False
    oldMin = min( oMin, oMax )
    oldMax = max( oMin, oMax )
    if not oldMin == oMin:
        reverseInput = True

    #check reversed output range
    reverseOutput = False   
    newMin = min( nMin, nMax )
    newMax = max( nMin, nMax )
    if not newMin == nMin :
        reverseOutput = True

    portion = (x-oldMin)*(newMax-newMin)/(oldMax-oldMin)
    if reverseInput:
        portion = (oldMax-x)*(newMax-newMin)/(oldMax-oldMin)

    result = portion + newMin
    if reverseOutput:
        result = newMax - portion

    return result

  def print_qlearn_reward_matrix (self):
      self.writePrint( 'qlearn_NextMovesList.print_qlearn_reward_matrix: Starting print out of qlearn_reward_matrix:...')        
      for key, value in sorted(self.q.items()):
          self.writePrint( 'qlearn_NextMovesList.print_qlearn_reward_matrix: %s' % (key,) + ( '%s' % (value,) ) )
          
  def writePrint ( self, msg ):
      if self.TraceOn:
          self.logger.debug(msg)

  def pickleQ (self):
      fg = open(self.QWeightFile, "wb")
      pickle.dump(self.q, fg, -1)
      fg.close()
    
  def unpickleQ (self):
    if self.loadQWeights and os.path.isfile(self.QWeightFile):
      fg = open(self.QWeightFile, "rb")
      self.q = pickle.load(fg)
      fg.close()
    
    
    
    
    
    
