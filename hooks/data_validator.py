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


class AbstractDataValidatorHook(HookBaseClass):
    """
    Abstract hook class that defines the necessary methods for the Data Validation App to function.

    This is the main hook for the App and is essential for the App to display the validation data and to
    apply any validation actions to the DCC data. In this hook, define the data validation rules, and check
    and fix functionality for a specific DCC.

    This hook does not define any of the validation data or implement the methods itself, since the data to
    be validated will be specific to the running DCC. This hook class must be subclassed, for example, by the
    engine where DCC specific functionality is available.
    """

    def get_validation_data(self):
        """
        Return the main data validation rule set that drives the App.

        This method must be implemented by the subclass.

        It is not enforced, but the dictionary returned by this function should be formated such that each
        key-value pair can be passed to create a :class:`tk_multi_data_validation.api.data.ValidationRule`.

        :return: The validation data that can be used to validate the data.
        :rtype: dict

        :raises NotImplementedError: If the subclass does not implement this function.
        """

        raise NotImplementedError()
