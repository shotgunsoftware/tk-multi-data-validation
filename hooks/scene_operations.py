# Copyright (c) 2024 Autodesk Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk Inc.


import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class AbstractSceneOperationsHook(HookBaseClass):
    """
    Abstract hook class that defines the optional methods for updating the Data Validation
    App UI based on the DCC scene operations.
    """

    def register_scene_events(self, reset_callback, change_callback):
        """
        Register events for when the scene has changed.

        The function reset_callback provided will reset the current Data Validation App,
        when called. The function change_callback provided will display a warning in the
        Data Validation App UI that the scene has changed and the current validatino state
        may be stale.

        The default implementation does nothing. Override this method by engine to provide
        the necessary functionality.

        :param reset_callback: Callback function to reset the Data Validation App.
        :type reset_callback: callable
        :param change_callback: Callback function to handle the changes to the scene.
        :type change_callback: callable
        """

    def unregister_scene_events(self):
        """
        Unregister the scene events.

        The default implementation does nothing. Override this method by engine to provide
        the necessary functionality.
        """
