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


class AbstractDataValidationHook(HookBaseClass):
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

    def sanitize_check_result(self, errors):
        """
        Sanitize the value returned by any validate function to conform to the standard format.

        This method must be implemented by the subclass.

        Each engine will provide their own validation functions which should return the list of
        objects that do not follow the validation rule. These objects will be referred to as
        "errors". In order for the Data Validation App to handle these objects coming from
        different DCCs, the error objects need to be sanitized into a format that the Data
        Validation App can handle. The standard format that the Data Validation App excepts
        is a list of dictionaries, where each dictionary defines a DCC error object with
        the following keys:

            :is_valid: ``bool`` True if the validate function succeed with the current data, else False.
            :errors: ``List[dict]`` The list of error objects (found by the validate function). None or empty list if the current data is valid. List elements have the following keys:

                :id: ``str | int`` A unique identifier for the error object.
                :name: ``str`` The display name for the error object.
                :type: ``str`` The display name of the error object type (optional).

        This method will be called by the Data Validation App after any validate function is
        called, in order to receive the validate result in the required format.

        :param errors: The value returned by a validate function that needs to be sanitized to
            the standard format.
        :type errors: any

        :return: The validation result in the standardized format.
        :rtype: dict
        """

        raise NotImplementedError()
