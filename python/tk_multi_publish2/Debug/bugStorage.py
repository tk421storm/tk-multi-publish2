'''

save / load stored bug reports

'''
from __future__ import print_function
from uuid import uuid4
from os import mkdir, remove, listdir, utime
from os.path import join, isdir, exists
try:
	from cPickle import dump, load
except:
	from pickle import dump, load
from traceback import format_exc
from shutil import copy
from platform import system

if system()=="Linux":
	storageBase='/mnt/RESOURCES/dev'
elif system()=="Windows":
	storageBase='R:\\dev'
else:
	storageBase='/Volumes/resources/dev'
	
storageLocation=join(storageBase, 'bugReports')
	
print("bugReports location "+str(storageLocation))

def touch(fname, times=None):
	with open(fname, 'a'):
		utime(fname, times)


def storeBug(subject, message, attachments):
	'''store a bug report to the disk'''
	
	from . import debug
	
	bugID=uuid4().hex
	bugDirectory=join(storageLocation, bugID)
	bugFile=join(bugDirectory, 'bug.pickle')
	
	try:
		mkdir(bugDirectory)
	except:
		debug(1, "ERROR - cannot access location "+str(bugDirectory)+" - do we have write permission there?")
		return
	
	try:
		#we'll store the attachments in that location too, in case the current location is only accesible locally
		if len(attachments):
			attachmentsDirectory=join(bugDirectory, "attachments")
			mkdir(attachmentsDirectory)
			for filer in attachments:
				copy(filer,attachmentsDirectory)
				
		#update the attachments list
		attachments=[join(attachmentsDirectory, filer) for filer in listdir(attachmentsDirectory)]
	except:
		debug(2, 'unable to copy attachments to global location')
		debug(2, format_exc())
	
	bugDict={'subject':subject, 'message':message, 'attachments':attachments}
	

	
	try:
		#pickle the arguments to a file, for loading by other functions
		with open(bugFile, 'w') as myFile:
			dump(bugDict, myFile)
	except:
		debug(1, 'error writing to bug File '+str(myFile))
		debug(1, format_exc())
		
	#finally, add a "done" empty file to the directory, signaling the bug is ready to upload
	touch(join(bugDirectory, 'done'))
		
def loadBug(bugFolder, removeIfSuccesful=True):
	'''passed  a bug folder, attempt to load and return the bug dictionary stored there'''
	
	
	from . import debug
	
	try:
		if not exists(bugFolder):
			debug(2, 'bug folder '+str(bugFolder)+' does not exist')
			return None
		
		if not isdir(bugFolder):
			debug(2, 'bug Folder '+str(bugFolder)+' is not a directory')
			return None
		
		#we'll check for a "done" file here, indicating all copies are finished and the bug is ready to act upon
		if not exists(join(bugFolder, "done")):
			#since we're removing done instead of the whole folder, we'll pass by old reports silently
			#debug(3, 'bug Folder '+str(bugFolder)+' is still being written, ignoring for now')
			return None
		
		bugFile=join(bugFolder, "bug.pickle")
		with open(bugFile, 'r') as myFile:
			bugDict=load(myFile)
			
		if removeIfSuccesful:
			#remove the 'done' file, so we ignore this bug from now on (safer than deleting more)
			
			try:
				doneFile=join(bugFolder, 'done')
				remove(doneFile)
				#rmdir(bugFolder)
			except:
				debug(2, 'error removing bug/bug folder: ')
				debug(2, format_exc())
				
		return bugDict
			
	except:
		debug(1, 'error loading bugfile from '+str(bugFolder))
		debug(1, format_exc())
