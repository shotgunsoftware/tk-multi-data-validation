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
    """
    Subclass the main abstract data validator hook.
    """

    def get_validation_data(self):
        """
        Return the main data validation rule set that drives the App.

        This method must be implemented by the subclass.

        It is not enforced, but the dictionary returned by this function should be formated such that each
        key-value pair can be passed to create a :class:`tk_multi_data_validation.api.data.ValidationRule`.

        :return: The validation data that can be used to validate the data.
        :rtype: dict
        """

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
