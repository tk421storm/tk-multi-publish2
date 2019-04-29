'''

a custom python logging handler that submits bug messages to millspaugh logs

'''

from logging import StreamHandler
from . import debug

class DebugHandler(StreamHandler):
	
	def __init__(self, label=None):
		
		StreamHandler.__init__(self)
		
		self.label=label

		
	def emit(self, record):
		'''only log warning and above'''
		
		logLevel=record.levelname
		
		if logLevel in ['DEBUG', 'INFO']:
			inter=3
		elif logLevel=='WARNING':
			inter=2
		else:
			inter=1
			
		debug(inter, self.format(record), label=self.label)