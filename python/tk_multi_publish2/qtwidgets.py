# Copyright (c) 2017 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Wrapper for the various widgets used from frameworks so that they can be used
easily from with Qt Designer
"""

from pprint import pprint


import sgtk
from tank.platform.qt import QtCore, QtGui

elided_label = sgtk.platform.import_framework("tk-framework-qtwidgets", "elided_label")
ElidedLabel = elided_label.ElidedLabel

context_selector = sgtk.platform.import_framework("tk-framework-qtwidgets", "context_selector")
ContextWidget = context_selector.ContextWidget


#Millspaugh, create a dropdown for whether to update the task status on publish creation or not
class TaskUpdate(QtGui.QWidget):
	
	taskChanged=QtCore.Signal(object)
	
	def __init__(self, parent):
		
		QtGui.QWidget.__init__(self)
		
		self.taskLayout=QtGui.QGridLayout()

		self.taskLayout.setObjectName("taskLayout")
		self.updateTaskCheckbox=QtGui.QCheckBox()
		self.updateTaskCheckbox.setChecked(True)
		self.taskLayout.addWidget(self.updateTaskCheckbox, 0, 0)
		self.taskLayout.setColumnStretch(0, 0)
		self.taskLabel=QtGui.QLabel('Update task on publish to: ')
		self.taskLayout.addWidget(self.taskLabel, 0, 1)
		self.taskLayout.setColumnStretch(1, 0)
		self.updateTaskMenu=QtGui.QComboBox()
		model=self.updateTaskMenu.model()
		for name in ['Pending Review', 'In Progress']:
			item=QtGui.QStandardItem(name)
			model.appendRow(item)
		self.taskLayout.addWidget(self.updateTaskMenu, 0, 2)
		self.taskLayout.setColumnStretch(2, 1)
		self.taskLayout.setContentsMargins(0, 0, 0, 0)
		
		self.setLayout(self.taskLayout)
		
		#set active/enabled (for use after loading stored settings, if any)
		self.enableDisable()
		self.updateTaskCheckbox.clicked.connect(self.enableDisable)

		
	def enableDisable(self):
		'''enable/disable dialog based on checkbox'''
		
		if self.updateTaskCheckbox.isChecked():
			self.taskLabel.setEnabled(True)
			self.updateTaskMenu.setEnabled(True)
			self.active=True
		else:
			self.taskLabel.setEnabled(False)
			self.updateTaskMenu.setEnabled(False)
			self.active=False
			
		#emit that something changed
		self.taskChanged.emit(self.updateTask())
			
	def updateTask(self):
		'''return False if dont do update, otherwise string of selected update type'''
		
		if self.updateTaskCheckbox.isChecked():
			return self.updateTaskMenu.currentText()
		else:
			return False
		


