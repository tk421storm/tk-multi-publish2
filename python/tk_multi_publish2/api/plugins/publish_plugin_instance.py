# Copyright (c) 2018 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from contextlib import contextmanager
import traceback

#python 2 only
from inspect import getargspec

import sgtk
from .instance_base import PluginInstanceBase

logger = sgtk.platform.get_logger(__name__)


class PublishPluginInstance(PluginInstanceBase):
    """
    Class that wraps around a publishing plugin hook

    Each plugin object reflects an instance in the app configuration.
    """

    def __init__(self, name, path, settings, publish_logger=None):
        """
        :param name: Name to be used for this plugin instance
        :param path: Path to publish plugin hook
        :param settings: Dictionary of plugin-specific settings
        :param publish_logger: a logger object that will be used by the hook
        """
        # all plugins need a hook and a name
        self._name = name

        self._icon_pixmap = None

        super(PublishPluginInstance, self).__init__(
            path,
            settings,
            publish_logger
        )

    def _create_hook_instance(self, path):
        """
        Create the plugin's hook instance.

        Injects the plugin base hook class in order to provide a default
        implementation.
        """
        bundle = sgtk.platform.current_bundle()
        hook = bundle.create_hook_instance(
            path,
            base_class=bundle.base_hooks.PublishPlugin
        )
        hook.id = path
        return hook

    @property
    def name(self):
        """
        The name of this publish plugin instance
        """
        return self._name

    @property
    def plugin_name(self):
        """
        The name of the publish plugin itself.
        Always a string.
        """
        value = None
        try:
            value = self._hook_instance.name
        except AttributeError:
            pass

        return value or "Untitled Integration."

    @property
    def description(self):
        """
        The description of the publish plugin.
        Always a string.
        """
        value = None
        try:
            value = self._hook_instance.description
        except AttributeError:
            pass

        return value or "No detailed description provided."

    @property
    def icon(self):
        """
        Returns the icon for this plugin instance.

        .. warning:: This property will return ``None`` when run without a UI
            present
        """

        # nothing to do if running without a UI
        if not sgtk.platform.current_engine().has_ui:
            return None

        if not self._icon_pixmap:
            self._icon_pixmap = self._load_plugin_icon()

        return self._icon_pixmap

    @property
    def item_filters(self):
        """
        The item filters defined by this plugin
        or [] if none have been defined.
        """
        try:
            return self._hook_instance.item_filters
        except AttributeError:
            return []

    @property
    def has_custom_ui(self):
        """
        Checks if a plugin has a custom widget.

        :returns: ``True`` if the plugin supports ``create_settings_widget``,
            ``get_ui_settings`` and ``set_ui_settings``,``False`` otherwise.
        """
        return all(
            hasattr(self._hook_instance, attr)
            for attr in ["create_settings_widget", "get_ui_settings", "set_ui_settings"]
        )

    @property
    def settings(self):
        """
        returns a dict of resolved raw settings given the current state
        """
        return self._settings

    def run_accept(self, item):
        """
        Executes the hook accept method for the given item

        :param item: Item to analyze
        :returns: dictionary with boolean keys accepted/visible/enabled/checked
        """

        try:
            return self._hook_instance.accept(self.settings, item)
        except Exception:
            error_msg = traceback.format_exc()
            self._logger.error(
                "Error running accept for %s" % self,
                extra=_get_error_extra_info(error_msg)
            )
            return {"accepted": False}
        finally:
            if not sgtk.platform.current_engine().has_ui:
                from sgtk.platform.qt import QtCore
                QtCore.QCoreApplication.processEvents()

    def run_validate(self, settings, item):
        """
        Executes the validation logic for this plugin instance.

        :param settings: Dictionary of settings
        :param item: Item to analyze
        :return: True if validation passed, False otherwise.
        """

        with self._handle_plugin_error(None, "Error Validating: %s"):
            status = self._hook_instance.validate(settings, item)

        # check that we are not trying to publish to a site level context
        if item.context.project is None:
            status = False
            self.logger.error("Please link '%s' to a Shotgun object and task!" % item.name)

        if status:
            self.logger.debug("Validation successful!")
        else:
            self.logger.error("Validation failed.")

        return status
       
    def run_rollback(self, settings, item):
        """
        Executes the rollback logic for this plugin instance.
        
        Not all plugins will have rollback functions; if they dont, this will pass

        :param settings: Dictionary of settings
        :param item: Item to analyze
        :return: True if rollback passed, False otherwise.
        """

        with self._handle_plugin_error(None, "Error Rolling back: %s"):
            try:
                status = self._hook_instance.rollback(settings, item)
            except:
                self.logger.debug('No rollback function is defined for '+str(self._hook_instance.name))
                return False

            if status:
                self.logger.debug("Rollback successful!")
            else:
                self.logger.error("Rollback failed.")
    
            return status

    def run_publish(self, settings, item):
        """
        Executes the publish logic for this plugin instance.

        :param settings: Dictionary of settings
        :param item: Item to analyze
        """
        with self._handle_plugin_error(None, "Error publishing: %s"):
            status = self._hook_instance.publish(settings, item)
            
        if status:
            self.logger.debug("Publish successful!")
        else:
            self.logger.error("Publish failed.")

        return status

    def run_finalize(self, settings, item):
        """
        Executes the finalize logic for this plugin instance.

        :param settings: Dictionary of settings
        :param item: Item to analyze
        """
        with self._handle_plugin_error(None, "Error finalizing: %s"):
            status = self._hook_instance.finalize(settings, item)
            
        if status:
            self.logger.debug("Finalization successful!")
        else:
            self.logger.error("Finalization failed.")

        return status

    ############################################################################
    # ui methods

    def run_create_settings_widget(self, parent):
        """
        Creates a custom widget to edit a plugin's settings.

        .. note:: This method is a no-op if running without a UI present

        :param parent: Parent widget
        :type parent: :class:`QtGui.QWidget`
        """

        # nothing to do if running without a UI
        if not sgtk.platform.current_engine().has_ui:
            return None

        with self._handle_plugin_error(None, "Error laying out widgets: %s"):
            return self._hook_instance.create_settings_widget(parent)

    def run_get_ui_settings(self, parent, selected_tasks=None):
        """
        Retrieves the settings from the custom UI.

        .. note:: This method is a no-op if running without a UI present

        :param parent: Parent widget
        :type parent: :class:`QtGui.QWidget`
        
        :param selected_tasks: a list of tasks selected in the gui
        :type selected_tasks: List of PublishTask instances
        """

        # nothing to do if running without a UI
        if not sgtk.platform.current_engine().has_ui:
            return None

        with self._handle_plugin_error(None, "Error reading settings from UI: %s"):
            #we'll need to determine how the plugin was coded - if it can accept the selected_tasks variable, pass it
            #note that we'll have to replace this with Signature as of python 3
            function=self._hook_instance.get_ui_settings
            args=len(getargspec(function)[0])
            if args==2:
                return function(parent, selected_tasks)
            else:
                return function(parent)

    def run_set_ui_settings(self, parent, settings, selected_tasks=None):
        """
        Provides a list of settings from the custom UI. It is the responsibility of the UI
        handle different values for the same setting.

        .. note:: This method is a no-op if running without a UI present

        :param parent: Parent widget
        :type parent: :class:`QtGui.QWidget`
        :param settings: List of dictionary of settings as python literals.
        """

        # nothing to do if running without a UI
        if not sgtk.platform.current_engine().has_ui:
            return None

        with self._handle_plugin_error(None, "Error writing settings to UI: %s"):
            #we'll need to determine how the plugin was coded - if it can accept the selected_tasks variable, pass it
            #note that we'll have to replace this with Signature as of python 3
            function=self._hook_instance.set_ui_settings
            args=len(getargspec(function)[0])
            if args==2:
                return function(parent, settings, selected_tasks)
            else:
                return function(parent, settings)

    @contextmanager
    def _handle_plugin_error(self, success_msg, error_msg):
        """
        Creates a scope that will properly handle any error raised by the plugin
        while the scope is executed.

        .. note::
            Any exception raised by the plugin is bubbled up to the caller.

        :param str success_msg: Message to be displayed if there is no error.
        :param str error_msg: Message to be displayed if there is an error.
        """

        try:
            # Execute's the code inside the with statement. Any errors will be
            # caught and logged and the events will be processed
            yield
        except Exception as e:
            exception_msg = traceback.format_exc()
            self._logger.error(
                error_msg % (e,),
                extra=_get_error_extra_info(exception_msg)
            )
            raise
        else:
            if success_msg:
                self._logger.debug(success_msg)
        finally:
            if not sgtk.platform.current_engine().has_ui:
                from sgtk.platform.qt import QtCore
                QtCore.QCoreApplication.processEvents()

    def _load_plugin_icon(self):
        """
        Loads the icon defined by the plugin's hook.

        :returns: QPixmap or None if not found
        """

        # defer import until needed and to avoid issues when running without UI
        from sgtk.platform.qt import QtGui

        # load plugin icon
        pixmap = None
        try:
            icon_path = self._hook_instance.icon
            if icon_path:
                try:
                    pixmap = QtGui.QPixmap(icon_path)
                except Exception, e:
                    self._logger.warning(
                        "%r: Could not load icon '%s': %s" % (
                            self, icon_path, e
                        )
                    )
        except AttributeError:
            # plugin does not have an icon
            pass

        # load default pixmap if hook doesn't define one
        if pixmap is None:
            pixmap = QtGui.QPixmap(":/tk_multi_publish2/task.png")

        return pixmap


def _get_error_extra_info(error_msg):
    """
    A little wrapper to return a dictionary of data to show a button in the
    publisher with the supplied error message.
    :param error_msg: The error message to display.
    :return: An logging "extra" dictionary to show the error message.
    """

    return {
        "action_show_more_info": {
            "label": "Error Details",
            "tooltip": "Show the full error tack trace",
            "text": "<pre>%s</pre>" % (error_msg,)
        }
    }
