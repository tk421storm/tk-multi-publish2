'''

bug report panel (entirely QT based)

'''

from traceback import format_exc
from os.path import join

from sgtk.platform.qt import QtCore, QtGui #@UnresolvedImport
		
QPalatte=QtGui.QPalette
QPixmap=QtGui.QPixmap
QCoreApplication=QtCore.QCoreApplication
		
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
	qAppCore=QtGui.qApp
	QApplication=QtGui.QApplication
except:
	QWidget=QtWidgets.QWidget #@UndefinedVariable
	QFrame=QtWidgets.QFrame #@UndefinedVariable
	QDialog=QtWidgets.QDialog #@UndefinedVariable
	QGridLayout=QtWidgets.QGridLayout #@UndefinedVariable
	QLabel=QtWidgets.QLabel #@UndefinedVariable
	QPlainTextEdit=QtWidgets.QPlainTextEdit #@UndefinedVariable
	QDialogButtonBox=QtWidgets.QDialogButtonBox #@UndefinedVariable
	QPushButton=QtWidgets.QPushButton #@UndefinedVariable
	qAppCore=QtWidgets.qApp #@UndefinedVariable
	QApplication=QtWidgets.QApplication #@UndefinedVariable
	qApp=QtWidgets.qApp #@UndefinedVariable
	QSpacerItem=QtWidgets.QSpacerItem #@UndefinedVariable
	QApplication=QtWidgets.QApplication #@UndefinedVariable
	
from . import currentRoot
		
class QHLine(QFrame):
	def __init__(self):
		super(QHLine, self).__init__()
		self.setFrameShape(QFrame.HLine)
		self.setFrameShadow(QFrame.Sunken)
		
def _nuke_main_window():
	"""Returns Nuke's main window"""
	
	#nuke 12.1, qApp is None-type
	
	qApp=qAppCore
			
	if str(qApp) is 'None':
		#this is also none
		#qApp=QApplication
		qApp=QCoreApplication
		print('using QApplication ('+str(qApp)+')for qApp')
	else:
		print('using qApp ('+str(qApp)+') for qApp')
	
	try:
		#3dsmax, convert to QApplication
		import PySide2 #@UnresolvedImport
		
		if isinstance(qApp, PySide2.QtCore.QCoreApplication):
			import shiboken2 #@UnresolvedImport
			qApp=shiboken2.wrapInstance(shiboken2.getCppPointer(QApplication.instance())[0], QApplication)
	except:
		print(format_exc())
	
	
	for obj in qApp.topLevelWidgets():
		if obj.inherits('QMainWindow'):
			print(obj.metaObject().className())
			if obj.metaObject().className() == 'Foundry::UI::DockMainWindow':
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
		self.userDescription=self.description.toPlainText()
		self.close()
		#submit the report
		
	def cancellor(self):
		self.accepted=False
		self.userDescription=self.description.toPlainText()
		self.close()
	
	def __init__(self, toolName, extraInfo, parent=None):
		
		QDialog.__init__(self, parent=_nuke_main_window())
		
		self.accepted=False
		self.userDescription=''
		
		#these two lines are critical to prevent segfaults on cleanup
		self.setWindowModality(QtCore.Qt.ApplicationModal)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		
		layout=QGridLayout()
		
		#print('bug submit window loading from '+str(currentRoot))
		
		bgPath=join(currentRoot,'assets','header.png')
		#print("loading bg image from "+bgPath)
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
		self.setWindowTitle('Phosphene Bug Submitter')


def launchBugSubmitPanel(toolName, extraInfo, debugQueue=None, parentPanel=None):
	'''get info from the user (if any), return user-entered description'''
	
	#setup debugging
	if not debugQueue:
		def debug(inter, stringer):
			print(stringer)
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
		print(message)
		return message
	
def showPanel(toolName, extraInfo, parent=None):
	panel=BugSubmitPanel(toolName, extraInfo, parent)
	panel.exec_()
	return (panel.accepted, panel.userDescription)
		
		
		
		
		
		