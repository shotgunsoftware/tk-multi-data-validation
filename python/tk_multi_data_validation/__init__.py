# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

from .api import ValidationManager


def show_dialog(app, modal=False):
    """
    Show the main dialog ui

    :param app: The parent App
    """

    # defer imports so that the app works gracefully in batch modes
    from .dialog import AppDialog

    # Check if the App is already showing
    app_dialog = None
    for qt_dialog in app.engine.created_qt_dialogs:
        if not hasattr(qt_dialog, "_widget"):
            continue

        app_name = qt_dialog._widget.property("app_name")
        if app_name == app.name:
            app_dialog = qt_dialog
            break

    if app_dialog:
        # App dialog already showing, pop it to the front
        app_dialog.activateWindow()
    else:
        if modal:
            _, widget = app.engine.show_modal("Scene Data Validation", app, AppDialog)
        else:
            widget = app.engine.show_dialog("Scene Data Validation", app, AppDialog)

        # Set the widget property so that we can detect if the dialog for this app
        # is already showing to avoid multiple dialogs open at one time.
        widget.setProperty("app_name", app.name)
