'''

thread to submit metrics

'''
from __future__ import print_function
from multiprocessing import Queue
try:
	from Queue import Empty, Full
except:
	#python3
	from queue import Empty, Full
from threading import Thread, Event
from time import sleep
from os.path import join
from os import environ
from sys import path
from getpass import getuser
from socket import gethostname
from datetime import datetime

from . import currentRoot

#metrics must be specificially enabled by setting an environment variable TD_METRICS
try:
	environ['TD_METRICS']
	metricsEnabled=True
except:
	metricsEnabled=False
	
login=getuser()
hostname=gethostname()
mongoServer="192.168.0.4"
mongoPort=27017

if metricsEnabled:
	
	mongoDir=join(currentRoot, "include", "util", "pymongo")
	path.append(mongoDir)
	
	metricsQueue=Queue()
	
	#store it at nuke for convenience
	try:
		import nuke #@UnresolvedImport
		nuke.metricsQueue=metricsQueue
	except:
		pass
	
	class MongoThread(Thread):
		def __init__(self):
			Thread.__init__(self)
			
			self.name="MongoSubmitThread"
			
			self._stopevent=Event()
			
			print("mongo submit thread starting")
			
			#create mongo connection
			import pymongo #@UnresolvedImport
			self.pymongo=pymongo
			
			self.client=pymongo.MongoClient(mongoServer, mongoPort, serverSelectionTimeoutMS=200)
			

			
		def run(self):
			
			#check if the server is available
			try:
				self.client.admin.command('ismaster')
				self.db=self.client['metrics']
				
			except self.pymongo.errors.ConnectionFailure: #@UndefinedVariable
				print("mongo server not available, no metrics submission will occur")
				self.db=None
				self._stopevent.set()

			while not self._stopevent.isSet():
				
				try:
					metricDict=metricsQueue.get_nowait()
					self.submitMetric(metricDict)
				except (Empty, Full):
					pass
				
				sleep(.25)
				
				
		def submitMetric(self, metricDict):
			
			artistName=login
				
			metricData={'label':metricDict['label'],
						'duration':metricDict['totalTime'],
						'hostname':hostname,
						'login':login,
						'username':artistName,
						'logs':metricDict['log'],
						'date':datetime.now()}
			
			
			if self.db:
				
				collection=self.db[metricDict['program']]
				
				collection.insert_one(metricData)
			else:
				
				print("metric discarded")
				
		def join(self, timeout=None):
			'''stop the thread'''
			self._stopevent.set()
			Thread.join(self, timeout)
			
	mongoSubmit=MongoThread()
	mongoSubmit.start()
else:
	metricsQueue=None





			
