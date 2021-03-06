# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from traceback import format_exc

from .api import PublishManager  # noqa
from . import base_hooks  # noqa
from . import util  # noqa
from . import publish_tree_widget  # noqa


def show_dialog(app):
    """
    Show the main dialog ui

    :param app: The parent App
    """
    # defer imports so that the app works gracefully in batch modes
    from .dialog import AppDialog

    display_name = sgtk.platform.current_bundle().get_setting("display_name")
    
    #print "logger item: "
    #print sgtk.custom_debug_handler
    
    #store publish logs alongside other phosphene logs, enable bug submit
    logger = sgtk.platform.get_logger(__name__)
    #try:
    #    #from .Debug import DebugHandler
    #    #phospheneDebugHandler=DebugHandler()
    #    phospheneDebugHandler=sgtk.custom_debug_handler
    #    print "hooking phosphene logs into "+str(logger)
    #    logger.addHandler(phospheneDebugHandler)
    #except:
    #    print format_exc()
    
    logger.info('Phosphene publish loaded')

    if app.pre_publish_hook.validate():
        # start ui
        if app.modal:
            app.engine.show_modal(display_name, app, AppDialog)
        else:
            app.engine.show_dialog(display_name, app, AppDialog)
    else:
        app.logger.debug(
            "%s validate returned False -- abort publish."
            % app.pre_publish_hook.__class__.__name__
        )

