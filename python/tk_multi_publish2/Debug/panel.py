'''

bug report panel (entirely QT based)

'''

from traceback import format_exc
from os.path import join

from sgtk.platform.qt import QtCore, QtGui
		
QPalatte=QtGui.QPalette
QPixmap=QtGui.QPixmap
		
#Nuke11 fix
try:
	QWidget=QtGui.QWidget
	QFrame=QtGui.QFrame
	QDialog=QtGui.QDialog
	QGridLayout=QtGui.QGridLayout
	QLabel=QtGui.QLabel
	QPlainTextEdit=QtGui.QPlainTextEdit
	QDialogButtonBox=QtGui.QDialogButtonBox
	QPushButton=QtGui.QPushButton
	QApplication=QtGui.QApplication
	qApp=QtGui.qApp
	QSpacerItem=QtGui.QSpacerItem
except:
	QWidget=QtWidgets.QWidget
	QFrame=QtWidgets.QFrame
	QDialog=QtWidgets.QDialog
	QGridLayout=QtWidgets.QGridLayout
	QLabel=QtWidgets.QLabel
	QPlainTextEdit=QtWidgets.QPlainTextEdit
	QDialogButtonBox=QtWidgets.QDialogButtonBox
	QPushButton=QtWidgets.QPushButton
	QApplication=QtWidgets.QApplication
	qApp=QtWidgets.qApp
	QSpacerItem=QtWidgets.QSpacerItem
	
from . import currentRoot
		
class QHLine(QFrame):
	def __init__(self):
		super(QHLine, self).__init__()
		self.setFrameShape(QFrame.HLine)
		self.setFrameShadow(QFrame.Sunken)
		
def _nuke_main_window():
	"""Returns Nuke's main window"""
	for obj in qApp.topLevelWidgets():
		if obj.inherits('QMainWindow') and obj.metaObject().className() == 'Foundry::UI::DockMainWindow':
			return obj
	else:
		return None
		
##############
###
### panel
###
##############

class BugSubmitPanel(QDialog):
	
	def acceptor(self):
		self.accepted=True
		self.close()
		#submit the report
		
	def cancellor(self):
		self.accepted=False
		self.close()
	
	def __init__(self, toolName, extraInfo, parent=None):
		
		QDialog.__init__(self, parent=_nuke_main_window())
		
		self.accepted=False
		
		layout=QGridLayout()
		
		print 'bug submit window loading from '+str(currentRoot)
		
		bgPath=join(currentRoot,'assets','header.png')
		print "loading bg image from "+bgPath
		background=QPixmap(bgPath)
		bgPalatte=QPalatte()
		bgPalatte.setBrush(QPalatte.Background, background)
		self.setPalette(bgPalatte)
		
		#space for header
		spacer=QSpacerItem(360,100)
		layout.addItem(spacer, 0, 0)
		
		self.extraInfo=extraInfo
		self.toolName=toolName
	
		self.errorTitle=QLabel("<b>"+toolName+' has encountered an error.</b><br /><br />')
		layout.addWidget(self.errorTitle, 1, 0)
		
		if extraInfo:
			infoText=extraInfo+"\n\n"
			infoText=infoText.replace('\n', '<br />')
			self.extraInfoKnob=QLabel("<br />".join(infoText.split("<br />")[:25]))
			self.extraInfoKnob.setWordWrap(True)
			layout.addWidget(self.extraInfoKnob, 2, 0)
			i=1
		else:
			i=0
			
		horiz=QHLine()
		layout.addWidget(horiz, 3+i, 0)
			
		self.label=QLabel('Please briefly describe what you were doing:')
		layout.addWidget(self.label, 4+i, 0)
		
		self.description=QPlainTextEdit()
		layout.addWidget(self.description, 5+i, 0)
		
		self.instructions=QLabel('Press \'OK\' to submit bug report, \'Cancel\' to cancel.')
		layout.addWidget(self.instructions, 6+i, 0)
		
		#add ok/cancel
		dialogButtons=QDialogButtonBox()
		self.okButton=QPushButton('OK')
		self.okButton.clicked.connect(self.acceptor)
		self.okButton.setDefault(True)
		cancelButton=QPushButton('Cancel')
		cancelButton.clicked.connect(self.cancellor)
		dialogButtons.addButton(self.okButton, QDialogButtonBox.AcceptRole)
		dialogButtons.addButton(cancelButton, QDialogButtonBox.RejectRole)
		
		layout.addWidget(dialogButtons, 7+i, 0)
	
		
		self.setLayout(layout)
		
		self.setWindowFlags(QtCore.Qt.Tool)
		self.setWindowTitle('Submit to Render')


def launchBugSubmitPanel(toolName, extraInfo, debugQueue=None, parentPanel=None):
	'''get info from the user (if any), return user-entered description'''
	
	#setup debugging
	if not debugQueue:
		def debug(inter, stringer):
			print stringer
	else:
		def debug(inter, stringer):
			debugQueue.put_nowait((inter, stringer))
			
	try:
		if parentPanel:
			results=showPanel(toolName, extraInfo, parent=parentPanel)
		else:	
			app = QApplication.instance()
			if app is None:
				#it does not exist then a QApplication is created
				debug(3, "no qapp available, creating one before displaying bug submit")
				app = QApplication([])
				results=showPanel(toolName, extraInfo, parent=app)
			else:
				#here we'll check if we're in a gui instance or a simple qcore instance (such as nuke -t)
				if type(app)==QtCore.QCoreApplication:
					#we're in a terminal instance without access to a gui, so we'll just send the report
					debug(2, "NO GUI AVAILABLE - sending bug report as-is")
					return "TERMINAL SESSION"
				else:
					#if app is nuke, we need to launch in main thread or else it will lock
					#the function name is different in qt 4 and 5
					if qtVersion==4:
						function=app.applicationName
					else:
						function=app.applicationDisplayName
					try:
						if "Nuke" in function():
							debug(3, "found nuke gui session")
							from nuke import executeInMainThreadWithResult #@UnresolvedImport
							results=executeInMainThreadWithResult(showPanel, args=(toolName, extraInfo))
						else:
							#other applications can be handled here specially here
							debug(3, "displaying panel in application: "+app.applicationDisplayName())
							results=showPanel(toolName, extraInfo, parent=app)
					except:
						debug(2, 'unknown error attempting to determine gui context (nuke or otherwise)')
						debug(2, format_exc())
						results=showPanel(toolName, extraInfo, parent=app)
					
		if results:
			accepted=results[0]
			description=results[1]
			if accepted:
				return description
			else:
				return None
		else:
			return None
	except:
		#if for some reason, we failed to open the bug submit panel, we might be in an environment without it
		#so we'll just submit the bug silently
		message="Error launching bug submit panel: <br /><br />"+format_exc()
		print message
		return message
	
def showPanel(toolName, extraInfo, parent=None):
	panel=BugSubmitPanel(toolName, extraInfo, parent)
	panel.exec_()
	return (panel.accepted, panel.description.toPlainText())
		
		
		
		
		
		