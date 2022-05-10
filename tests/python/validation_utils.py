# Copyright (c) 2022 Autodesk Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk Software Inc.


class CheckResult(object):
    def __init__(self, is_valid, errors=None):
        self.is_valid = is_valid
        self.errors = errors
