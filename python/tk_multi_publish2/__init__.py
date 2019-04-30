# Copyright (c) 2017 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

from time import time
import sgtk

from .api import PublishManager
from . import base_hooks
from . import util

def show_dialog(app):
    """
    Show the main dialog ui

    :param app: The parent App
    """
    # defer imports so that the app works gracefully in batch modes
    from .dialog import AppDialog

    display_name = sgtk.platform.current_bundle().get_setting("display_name")
    
    #store publish logs alongside other phosphene logs, enable bug submit
    logger = sgtk.platform.get_logger(__name__)
    try:
	    phospheneDebugHandler=sgtk.custom_debug_handler
	    print "hooking phosphene logs into "+str(logger)
	    logger.addHandler(phospheneDebugHandler)
    except:
		pass
    
    logger.info('Phosphene Elements Ingest loaded')
    
	#in order to fix the context_widget, we need to snychronize our local cache now
	#unfortunately this is probably going to be very slow
	#when they fix the context widget requiring a name (that is not retrieved by the default query)
	#we should probably remove this to speed things up
	
    logger.info('Synchronzing path cache....')
    start=time()
    app.sgtk.synchronize_filesystem_structure(full_sync=True)
    end=time()
    logger.info('....complete sync took '+str(end-start)+' seconds.')

    # start ui
    app.engine.show_dialog(display_name, app, AppDialog)




