'''

threaded debug log

'''
from __future__ import print_function
from threading import Event
from os.path import join, dirname, isdir, exists, getsize, realpath
from os import makedirs, environ
from multiprocessing import Queue
try:
	#python2
	from Queue import Empty, Full
except:
	#python3
	from queue import Empty, Full
from time import strftime, sleep, time
from pprint import pprint
from webbrowser import open as openURL
from getpass import getuser
from socket import gethostname
from traceback import format_exc
from uuid import uuid4
from random import randint
from datetime import datetime

#get this modules install location
currentRoot=dirname(realpath(__file__))

from .killer import killer
from .metrics import metricsEnabled, metricsQueue

#dont load the panel if we're in a terminal session (say on the monitor)
try:
	from sgtk.platform.qt import QtCore, QtGui
	gui=True
except ImportError:
	#Nuke11 prep
	try:
		from PySide import QtGui, QtCore
		gui=True
	except:
		try:
			from PySide2 import QtGui, QtCore, QtWidgets
			gui=True
		except:
			print('no gui availble')
			gui=False
			
if gui:
	from .panel import launchBugSubmitPanel
from .bugStorage import storeBug, storageBase

#use a global log directory (ubuntu clears tmp too often)
#use one directory for all logs
debugRoot=join(storageBase,"logs")

#get a program name, fallback to default
programName='elementsIngest'

#setup debug file using login, machine name et al	
login=getuser()
hostname=gethostname()
debugLoc=join(debugRoot,programName, login+"@"+hostname)
debugFileName=programName+'Log.html'
fullDebugPath=join(debugLoc, debugFileName)

debugLevel=3

#maximum size for an individual log file (in bytes)
maxSize=3000000

############
###
###	Class for writing to the debug log
###
############

class DebugWriter(QtCore.QThread):
	'''
	a background process that is killable
	'''

	def __init__(self, name, debugQueue, bugSubmitQueue, killer):
		'''constructor, setting initial variables '''
		self.debugQueue=debugQueue
		self.bugQueue=bugSubmitQueue
		self._stopevent = Event()
		self._sleepperiod = .1
		self.recycle=0
		print(programName+" debugWriter starting")
		
		##check that the debug folder exists
		if not isdir(debugLoc):
			makedirs(debugLoc)
			
		self.style=("<style>"
				"/* Tooltip container */"
				".tooltip {"
				"    position: relative;"
				"    display: inline-block;"
				"    border-bottom: 1px dotted black; /* If you want dots under the hoverable text */"
				"}"
				
				"/* Tooltip text */"
				".tooltip .tooltiptext {"
				"    visibility: hidden;"
				"    width: 600px;"
				"    background-color: black;"
				"    color: #fff;"
				"    text-align: center;"
				"    padding: 5px 0;"
				"    border-radius: 6px;"
				 
				"    /* Position the tooltip text - see examples below! */"
				"    position: absolute;"
				"    z-index: 1;"
				"}"
				
				"/* Show the tooltip text when you mouse over the tooltip container */"
				".tooltip:hover .tooltiptext {"
				"    visibility: visible;"
				"}"
				"</style>")
	
		##check that the debug file exists, if not create it
		self.debugFile=join(fullDebugPath)
		if not exists(self.debugFile):
			open(self.debugFile, 'w').write("<html><body>"+self.style)
			
		print(" debugWriter outputing to "+self.debugFile)

		QtCore.QThread.__init__(self)#, name=name)
		
		#a dictionary of all current metrics
		self.metrics={}
		
		#self.killer=killer
		

	
	
	def clearDebug(self):
		'''emptys a debug file so it doesn't get huge'''
	
		##write the header into the file, overwriting everything else
		with open(self.debugFile, 'w') as fileOpen:
			fileOpen.write("<html><body>"+self.style)
			
		self.announce()
			
	def returnDebugFile(self):
		'''returns location of current debug log file'''
		return self.debugFile
	
	def announce(self):
		'''print a header into the debug file'''
		currentTime=strftime("%b %d - %I:%M:%S%p - ")
		
		announce="</pre><br /><h2>"+programName+" at "+currentTime+"</h2><br /><pre>"
		
		with open(self.debugFile, 'a') as openFile:
			openFile.write(announce)
		
	def startMetric(self, label, startTime=None):
		'''activate a metric, return the metric id number for later closing'''
		
		metricID=uuid4().hex
		
		if metricsEnabled:
			#create a color for logs
			r = lambda: randint(0,125)
			hexColor='#%02X%02X%02X' % (r(),r(),r())
			
			if not startTime:
				startTime=time()
			
			metricDict={'startTime':startTime,
						'endTime':None,
						'totalTime':None,
						'label':label,
						'color':hexColor,
						'log':[],
						'program':programName}
			
			self.metrics[metricID]=metricDict
		
		return metricID
	
	def endMetric(self, metricID, endTime=None):
		'''end a metric, and report it the global repository'''
		

		if metricsEnabled:
			if not endTime:
				endTime=time()
			
			if metricID not in self.metrics:
				self.debugQueue.put_nowait((2, "metric "+metricID+" not found in dictionary, has it already been closed?", "metrics"))
			else:
				metricDict=self.metrics[metricID]
				
				#add a final time
				metricDict['endTime']=endTime
				metricDict['totalTime']=round(metricDict['endTime']-metricDict['startTime'],3)
				
				#report
				self.debugQueue.put_nowait((3, '  METRIC: '+metricDict['label']+' took '+str(metricDict['totalTime'])+' seconds to complete'))
				
				#remove it from the dictionary of metrics
				del self.metrics[metricID]
				
				#submit it to the mongo database
				metricsQueue.put_nowait(metricDict)
		
		
			
	
	def debug(self, level, msg, label=None, timestamp=None, currentTime=None):
		'''perform debug actions (format, save to file, etc)'''
		
		if not currentTime:
			currentTime=time()
				
		##print the message to the console, if the user is interested in this debug level
		if level<=debugLevel:
			if type(msg) is not str:
				pprint(msg)
			else:
				print(str(msg))
			
		msg=str(msg)
		
		
		#add it to the log attribute of all open metrics
		if metricsEnabled:
			for metricID in self.metrics:
				self.metrics[metricID]['log'].append(msg)
		
			
		##remove carrots for html
		msg=msg.replace(">","")
		msg=msg.replace("<","")
			
		
		#apply all metric times to this message
		metrics=""
		try:
			for metricID in self.metrics:
				metricDict=self.metrics[metricID]
				color=metricDict['color']
				startTime=metricDict['startTime']
				timePassed=" <div class='tooltip'><font color='"+color+"'>["+str(round(currentTime-startTime,3))+"]</font><span class='tooltiptext'>"+metricDict['label']+"</span></div> "
				metrics+=timePassed
		except RuntimeError:
			#dictionary changed size (new metric added), just ignore metrics
			pass
		
		metrics=""
			
		if label:
			msg="<b><i>"+str(label)+"</i></b>: "+metrics+" "+msg
		else:
			msg=metrics+" "+msg
		
		##pretty formating for html
		debugHeading={1:"<font color='red'><b>CRITICAL</b></font>: ",2:"<font color='orange'><b>WARNING</b></font>: ",3:"<font color='blue'><b>DEBUG</b></font>: "}
			
		##addTimestamp (if not already applied)
		if not timestamp:
			timestamp=strftime("%b %d - %I:%M:%S%p - ")
			
		timestamp="<b>"+timestamp+"</b>"
		debugMessage=timestamp+debugHeading[level]+msg+"<br />"
		
		##write to the debug file
		with open(self.debugFile, 'a') as openFile:
			try:
				openFile.write(debugMessage)
			except IOError as e:
				print("debug error - cannot write to disk")
				print(e)
				

				
				
	def bugSubmit(self, toolName, extraInfo=None, logFile=None, parentPanel=None):
		'''
		prompt the user for a description of what they were doing when the problem occured
		then collect the logs as well as query and refresh files for the current script
		place them in a folder on the server under the bugReport directory
		store bugs for another process to monitor, email, report etc
		'''
		
		self.debugQueue.put_nowait((1, "debug thread function bug submit called from "+str(QtCore.QThread.current_thread())+", toolName: "+toolName+", extraInfo: "+str(extraInfo)+", logFile:"+str(logFile)))

		userReport=launchBugSubmitPanel(toolName, extraInfo, debugQueue)
		
		if logFile and exists(logFile):
			logFileList=[self.debugFile, logFile]
		else:
			logFileList=[self.debugFile]
	
		if userReport!=None:
			bugName="PHOSPHENE_ERROR_REPORT: "+strftime("%m-%d-%H:%M:%S (")+login+", "+hostname+"): "+toolName
	
			print("sending "+bugName)
			#since we're in a locked environment, we can't always send email
			#instead we'll store the bug in a network-accesible location
			#a threaded process can then keep tabs on that folder and perform any action (say, email) on bugs there
			storeBug(bugName, userReport+"<br /><br />"+str(extraInfo), logFileList)
		else:
			print("user cancelled bug report")
		
	

	def run(self):
		'''main loop'''
		
		#we want to make sure the queue for debug writing is empty
		#however that won't necessarily be accurate the first go-around,
		#so we'll add a few cycles after a bug is found before the submit function occurs
		foundBug=False
		bugCycles=0
		
		while not self._stopevent.isSet():# and not self.killer.kill_now:
			
			#check for debug messages
			try:
				results=self.debugQueue.get_nowait()
				#print "found item in debug queue: "+str(results)
				try:
					if len(results)>=2:
						self.debug(*results)
					else:
						print("debug received odd-sized object "+str(results))
				except:
					print("debug error")
					print(format_exc())
									
				#make sure the debug file doesn't get to big, if it does, wipe it
				#only do this every 200 times we cycle through
				if self.recycle%200==0:
					if getsize(self.debugFile)>maxSize:
						self.clearDebug()
					self.recycle=0


				#self.debugQueue.task_done()
				self.recycle+=1
			except Empty:
				#check for queued bugs
				if not foundBug:
					try:
						bug=self.bugQueue.get_nowait()
						#print "found item in bug queue: "+str(bug)
						foundBug=True
						bugCycles=0
					except:
						pass
				else:
					#cycle five times before running submit
					#print "bugCycles: "+str(bugCycles)
					if bugCycles>5:
						#try:
						self.bugSubmit(*bug)
						foundBug=False
						#except:
						#	print "debug error"
						#	print format_exc()
						
					bugCycles+=1
										
				sleep(self._sleepperiod)
			except Full:
				sleep(self._sleepperiod)
				
		print(programName+" debugWriter ending")
				
			


	def join(self, timeout=None):
		'''stop the thread'''
		self._stopevent.set()
		
		#threading.Thread.join(self, timeout)

############
###
###	log commands and responses based on 3 log levels
###
############

def debug(level,msg, label=None):
	'''logs a [msg] to the debug file, prints it if [level] is higher than user setting'''
	
	#since a multiprocessing thread will do this function on it's own (printing into the voide), we'll simply add the information to the queue,
	#and do the processing in the thread instead of here
	
	#create timestamp here, more accurate than when the queue gets to it
	timestamp=datetime.now().strftime("%b %d - %I:%M:%S.%f%p - ")
	
	#also add a time element for metric measuring
	currentTime=time()
	
	#unicode
	try:
		debugQueue.put_nowait((level, str(msg), label, timestamp, currentTime))
	except UnicodeEncodeError:
		try:
			debugQueue.put_nowait((level, msg.encode('ascii', 'ignore'), label, timestamp, currentTime))
		except:
			pass
			
	##return the result for further logging if necessary
	return msg

############
###
###	clear the log when a new query is started to prevent it from balooning continuously
###
############

def clearDebug():
	'''clear the debug log'''
	writer.clearDebug()
	
def announce():
	'''add a header to the current action'''
	writer.announce()
		
############
###
###	open current debug file
###
############

def getDebugLog():
	'''open current debug file'''
	
	debugFile=writer.returnDebugFile()
	
	try:
		openURL(debugFile)
	except:
		debug(1, 'error opening debug file '+str(debugFile))
		

def bugSubmit(toolName, extraInfo=None, logFile=None, parentPanel=None):
	'''
	prompt the user for a description of what they were doing when the problem occured
	then collect the logs as well as query and refresh files for the current script
	place them in a folder on the server under the bugReport directory
	send me an email about the problem
	
	to maintain thread safety, we'll simply pass the bug submit into the overall debug thread to handle the gui
	otherwise we won't be sure if we're in another thread or not (and we can lock up the gui)
	'''
	#here we'll just add the bug to the queue for the debug writer to handle
	
	bugSubmitQueue.put_nowait((toolName, extraInfo, logFile, parentPanel))
		
		
		

############
###
###	start debug log writer, import default python logging handler
###
############

from .pythonLogging import DebugHandler

debugQueue=Queue()
bugSubmitQueue=Queue()
		
writer = DebugWriter("debugWriter", debugQueue, bugSubmitQueue, killer)
#writer.setDaemon(True)
writer.start()
writer.announce()
		
		
		
		
		