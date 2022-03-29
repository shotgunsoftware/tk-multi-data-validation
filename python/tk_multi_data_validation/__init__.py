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
from .widgets import ValidationWidget


def show_dialog(app, modal=False):
    """
    Show the main dialog ui

    :param app: The parent App
    """

    # defer imports so that the app works gracefully in batch modes
    from .dialog import AppDialog

    if modal:
        app.engine.show_modal("Scene Data Validation", app, AppDialog)
    else:
        app.engine.show_dialog("Scene Data Validation", app, AppDialog)
