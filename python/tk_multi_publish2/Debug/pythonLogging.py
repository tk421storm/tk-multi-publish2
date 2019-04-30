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
		
		#some shotgun tools can append additional data in a separate attribute on the record
		#we'll get that and include it in the logs here
		if hasattr(record, "action_show_more_info"):
			action=record.action_show_more_info
			extraInfo=action.get("text", "")
			debug(inter, extraInfo, label=self.label)