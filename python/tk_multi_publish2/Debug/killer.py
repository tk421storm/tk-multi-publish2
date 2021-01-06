'''

deal with threads and parser on close

'''
from __future__ import print_function
import signal
from traceback import print_stack
from multiprocessing import Queue

class GracefulKiller:
	kill_now = False
	def __init__(self, parent):
		self.parent=parent
		#windows compatibility
		try:
			signal.signal(signal.SIGINT, self.exit_gracefully)
		except:
			pass
		#windows compatibility
		try:
			signal.signal(signal.SIGTERM, self.exit_gracefully)
		except:
			pass
		#windows compatibility
		try:
			signal.signal(signal.SIGHUP, self.exit_gracefully)
		except:
			pass
		
		self.killQueue=Queue()

	def exit_gracefully(self,signum, frame):
		print("received "+str(signum)+" under "+str(self.parent))
		print_stack(frame)
		self.exit_now()
		
	def exit_now(self):
		'''can be run by any program'''
		self.kill_now=True
		self.killQueue.put_nowait(True)
		
killer=GracefulKiller('networkCopyPaste')
