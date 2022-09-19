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

HookBaseClass = sgtk.get_hook_baseclass()


class TestDataValidationHook(HookBaseClass):
    """Implement the data validation hook for testing."""

    def get_validation_data(self):
        """Implement the hook method for to return test data for validation."""

        return {
            "validation_rule_1": {
                "name": "Rule #1",
                "description": "This is the first test rule.",
                "error_msg": "This is the error message",
            },
            "validation_rule_2": {
                "name": "Rule #2",
                "description": "This is the second test rule.",
            },
            "validation_rule_3": {
                "name": "Rule #3",
            },
            "skip_rule": {
                "name": "This rule will not be excluded by not including it in the config.",
            },
        }

    def sanitize_check_result(self, check_result):
        """Implement the hook metho to sanitize the check result for testing validation."""

        # Just return the result as is
        return check_result
