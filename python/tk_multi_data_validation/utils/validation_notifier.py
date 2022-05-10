# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import sgtk
from sgtk.platform.qt import QtCore

from ..api.data.validation_rule import ValidationRule


class ValidationNotifier(QtCore.QObject):
    """Class to emit signals around validation operations."""

    validate_rule_begin = QtCore.Signal(ValidationRule)
    validate_rule_finished = QtCore.Signal(ValidationRule)
    validate_all_begin = QtCore.Signal()
    validate_all_finished = QtCore.Signal()
    resolve_rule_begin = QtCore.Signal(ValidationRule)
    resolve_rule_finished = QtCore.Signal(ValidationRule)
    resolve_all_begin = QtCore.Signal()
    resolve_all_finished = QtCore.Signal()
    about_to_open_msg_box = QtCore.Signal()
    msg_box_closed = QtCore.Signal()
