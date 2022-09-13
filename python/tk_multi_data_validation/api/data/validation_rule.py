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

from .validation_rule_type import ValidationRuleType


class ValidationRule(object):
    """
    A validation rule to be applied to the DCC data, which determines if the DCC data is valid or not.

    The key properties of the rule are the `check_func` and `fix_func`; these functions define the how the
    DCC data is validated and provides an automated function to resolve data that is not valid. See the list
    of class properties below for more information on what data is contained in the validation rule object.
    """

    def __init__(self, rule_data):
        """
        Create a validation rule with the provided data.

        :param rule_data: The data that defines the rule.
        :type rule_data: dict

        **rule_data dict format**
            key
                :type: str
                :description: The unique identifier for this rule.
            name
                :type: str
                :description: The display name for this rule.
            data_type:
                :type: str
                :description: The name of the data type that this rule pertains to.
            description
                :type: str
                :description: Text that describes what the rule checks for in the data.
            required
                :type: bool
                :description: True indicates that this rule should be applied when validating the data.
            checked
                :type: bool
                :description: True indicates that this rule has a checked state (for UI purposes), False indicates the rule is unchecked.
            check_name
                :type: str
                :description: The display name for the rule's check function.
            check_func
                :type: function
                :description: The function the rule executes to check the data for violations agains the rule.
            fix_name
                :type: str
                :description: The display name for the rule's fix function.
            fix_func
                :type: function
                :description: The function the rule executes to fix the data violations found after applying the rule's check function to the data.
            fix_tooltip
                :type: str
                :description: Text that describes what the rule's fix function will do.
            error_msg
                :type: str
                :description: Text that describes how the data is not valid.
            warn_msg
                :type: str
                :description: Text that describes the warning for this rule.
            get_kwargs
                :type: function
                :description: A function that returns a dictionary of keyword arguments to pass to the check and fix functions.
            actions
                :type: list<dict>
                :description: A list of actions that can be applied to the data to resolve any errors for this rule.

                **Required Keys**
                    name
                        :type: str
                        :description: The display text for the action.
                    callback
                        :type: function
                        :description: The function to call when the action is invoked.

                **Optional Keys**
                    tooltip
                        :type: str
                        :description: Text to display as for the item action's tooltip help messages.
            item_actions
                :type: list<dict>
                :description: A list of actions that can be applied to the particular data for this rule, to resolve the error.

                **Required Keys**
                    name
                        :type: str
                        :description: The display text for the action.
                    callback
                        :type: function
                        :description: The function to call when the action is invoked.

                **Optional Keys**
                    tooltip
                        :type: str
                        :description: Text to display as for the item action's tooltip help messages.
            dependencies
                :type: dict<str>
                :description: A dict of the valiation rule ids that this rule depends on and their display name. All dependency rules must be fixed before this rule can be fixed.
        """

        # Set the main rule data
        self._data = rule_data or {}

        # The checked property can be updated at runtime by user interaction. Initailzie the default value.
        self._optional_checked = self._data.get("checked", False)
        # This indicates whether the user checked the manual rule as being "done"
        self._manual_checked = False

        # Get the validatin rule type object for this rule
        self._rule_type = ValidationRuleType.get_type_for_rule(self)

        # Initialize valid property to None, indicating that this rule has not been checked yet.
        # Set to True once check has been run and the rule fails, or False if it passes.
        self._valid = None
        # The error items found the last time the rule's check function was executed.
        self._error_items = None
        # Flag indicating that the rule fix method was executed at least once
        self._fix_executed = False
        # Runtime exceptions caught - used to display error messages
        self._check_runtime_exception = None
        self._fix_runtime_exception = None

        # Keep track of the rules that this rule depends on, which have failed to be checked
        # upon attempting to check this rule
        self._failed_dependency = None

        # Store the hook method to sanitize validation results, as it will be used many times.
        bundle = sgtk.platform.current_bundle()
        hook_path = bundle.get_setting("hook_data_validation")
        self._sanitize_check_result = bundle.create_hook_instance(
            hook_path
        ).sanitize_check_result

    @property
    def id(self):
        """Get the unique identifier for this rule."""
        return self._data.get("id")

    @property
    def type(self):
        """Get the :class:`ValidationRuleType` of this rule."""
        return self._rule_type

    @property
    def rule_type_name(self):
        """Get the display name for the type of this rule."""
        return self.type.name

    @property
    def data_type(self):
        """Get the data type that this rule peratins to."""

        return self._data.get("data_type")

    @property
    def name(self):
        """Get the display name for thsi rule."""
        return self._data.get("name", "")

    @property
    def description(self):
        """Get the description text for what this rule does."""
        return self._data.get("description", "")

    @property
    def required(self):
        """Get the property flag indicating if this rule should be executed to validate the data."""
        return self._data.get("required", True)

    @property
    def manual(self):
        """
        Get the property flag indicating if this rule cannot be automatically checked.

        These types of rules must be manually validated by user.
        """

        return not (bool(self.check_func) or bool(self.fix_func))

    @property
    def optional(self):
        """
        Get the property flag indicating if this rule is optional.
        """
        return not self.required

    @property
    def check_name(self):
        """Get the display name for the check function of this rule."""
        return self._data.get("check_name", "Validate")

    @property
    def fix_name(self):
        """Get the display name for the fix function of this rule."""
        return self._data.get("fix_name", "Fix")

    @property
    def fix_tooltip(self):
        """Get the text that describes what the fix function does for this rule."""
        return self._data.get("fix_tooltip", "Click to fix this data violation.")

    @property
    def error_message(self):
        """Get or set the text that describes how the current data errors."""
        msg = self._data.get("error_msg")
        if msg is None:
            if self.check_func:
                msg = "Found errors."
            else:
                msg = ""
            self.error_message = msg
        return msg

    @property
    def warn_message(self):
        """Get or set the text that describes the current warnings."""
        return self._data.get("warn_msg")

    @property
    def checked(self):
        """
        Get the set the property flag indicating that an optional rule is checked (turned on).

        This is meant to be used to set the UI check state for an optional rule.
        """

        return self._optional_checked

    @checked.setter
    def checked(self, checked):
        self._optional_checked = checked

    @property
    def manual_checked(self):
        """
        Get the set the property flag indicating that a manual rule is checked (user set as valid).

        This is meant to be used to set the UI check state for a manual rule.
        """

        return self._manual_checked

    @manual_checked.setter
    def manual_checked(self, checked):
        self._manual_checked = checked

    @property
    def check_func(self):
        """
        Get the function that this rule executes to validate the data.

        It is encouraged to use the `exec_check` method instead of getting this function and calling it
        directly.
        """
        return self._data.get("check_func")

    @property
    def fix_func(self):
        """
        Get the function that this rule executes to fix the data violations found by the rule.

        It is encouraged to use the `exec_fix` method instead of getting this function and calling it
        directly.
        """
        return self._data.get("fix_func")

    @property
    def get_kwargs(self):
        """Get the function that returns the extra keyword arguments dict to pass to the check and fix functions."""
        return self._data.get("get_kwargs", lambda: {})

    @property
    def actions(self):
        """
        Get the list of actions that can be applied to all error items (as a group) for this rule.

        These do no include the primary check or fix functions. This property is a list of dicts, which contain
        a `name` and `callback` keys, and optionally contains keys: `tooltip`.
        """
        return self._data.get("actions", [])

    @property
    def item_actions(self):
        """
        Get the list of actions that can be applied invididual error items (one at a time) for this rule.

        These do no include the primary check or fix functions. This property is a list of dicts, which contain
        a `name` and `callback` keys, and optionally contains keys: `tooltip`.
        """
        return self._data.get("item_actions", [])

    @property
    def valid(self):
        """
        Get the valid state of the rule.

        This will reflect the status returned by the rule's check function the last time it was
        executed. If the value of this property is None, this indicates that the rule's check
        function was not executed, or the rule's valid state cannot be determined because at
        least one of the rule's dependencies is not valid or could not be checked (due to one
        of its dependencies).
        """
        return self._valid

    @property
    def errors(self):
        """
        Get the error data for this rule, based on the last time its check function executed.

        This will contain the error data items found by the rule's check function the last time
        it was executed.
        """
        return self._error_items or []

    @property
    def fix_executed(self):
        """Get the flag indicating if the rule's fix method was executed at least once."""
        return self._fix_executed

    @property
    def dependencies(self):
        """
        Get the dependencies information for this rule.

        Dependent rules must be fixed before this rule can be fixed. This defines the order that rules are
        fixed in, when fixing in bulk.
        """
        return self._data.get("dependencies", {})

    #########################################################################################################
    # Public methods

    def get_data(self, field):
        """
        Get the data from the rule.

        :param field: The field to get data for
        :type field: str

        :return: The data for the specified field
        :rtype: any
        """

        return self._data.get(field)

    def get_actions_data(self, pre_validate=False):
        """
        Return the action data required to execute the action callback functions.

        :param pre_validate: True will validate the rule before getting the errors to include
            in the action data. This ensures that the error data included is not stale.
        :type pre_validate: bool

        :return: The action data required to execute the callback functions.
        :rtype: List[dict]
        """

        actions = []

        for action in self.actions:
            # Add the current errors to the action data so that the action function can be
            # applied to the current errors.
            errors = self.get_errors() if pre_validate else self.errors
            action["kwargs"] = {"errors": errors}
            actions.append(action)

        return actions

    def get_error_item_ids(self):
        """
        Convenience method to get a list of the item ids from the data errors.

        :return: The item ids of the error items.
        :rtype: list
        """

        return [item["id"] for item in self.errors]

    def get_error_messages(self):
        """
        Return the list of current error messages.

        If there was a run time error during the check or fix function, the error messages will
        contain these run time error messages. The default error message will not be included.

        If the check and fix functions executed successfully, then return the default error
        message for the rule (e.g. assumes if the check/fix ran successfully than if there is
        an error, it will be due to finding actual validation errors related to the rule).

        :return: The error messages.
        :rtype: list
        """

        messages = []

        if self._check_runtime_exception:
            messages.append(
                "Validation Error: {}".format(self._check_runtime_exception)
            )

        if self._fix_runtime_exception:
            messages.append("Fix Error: {}".format(self._fix_runtime_exception))

        if not self._check_runtime_exception and not self._fix_executed:
            # Only include the validation error message if both check and fix functions
            # executed successfully.
            if self.error_message:
                messages.append(self.error_message)

        return messages

    def get_warning_messages(self):
        """Return the list of current warning messages."""

        messages = []

        if self.warn_message:
            messages.append(self.warn_message)

        if (self.manual and not self.manual_checked) or (
            not self.manual and not self.check_func
        ):
            messages.append("Validation must be manually checked.")

        if self._failed_dependency:
            messages.append(
                "Validation/Fix not run because the dependency failed: {}".format(
                    self._failed_dependency.name
                )
            )

        return messages

    def get_dependency_ids(self):
        """
        Get the validation rules (ids) that this rule depends on.

        Dependent rules must be fixed before this rule can be fixed. This defines the order that rules are
        fixed in, when fixing in bulk.
        """
        return self.dependencies.keys()

    def get_dependency_names(self):
        """
        Get the validation rules (display names) that this rule depends on.

        Dependent rules must be fixed before this rule can be fixed. This defines the order that rules are
        fixed in, when fixing in bulk.
        """
        return self.dependencies.values()

    def get_errors(self):
        """
        Execute this rule's check function to get the most up to date error data.

        The rule's check function will be executed, the `errors` property will be updated with
        the check function's result, and the result will be returned.

        :return: The most up to date error data.
        :rtype: list
        """

        self.exec_check()
        return self.errors

    def set_failed_dependency(self, dependency_rule):
        """
        Set the failed dependency for this rule.

        Set the failed dependency as None to indicate that this rule has no failed
        dependencies.

        This value is used to determine if it is safe to execute the rule's check and fix
        functions. If a dependency does not succeed, then the data may not be in a proper
        state for the dependent rule to act on; thus, attempting to execute the rule's
        check or fix function on the data may yield incorrect results.

        :param dependency_rule: The dependency rule that failed. Pass None to indicate that
            the rule has no failed dependencies.
        :type dependency_rule: ValidationRule
        """

        self._failed_dependency = dependency_rule

    def has_failed_dependency(self):
        """
        Return True if this rule has a dependency that failed.

        See `set_failed_dependency` for more information about the usage and purpose of this
        value.
        """

        return self._failed_dependency is not None

    def exec_check(self, force=False):
        """
        Execute the rule's check function.

        It is reccommended to use this method to execute the rule's check function, instead of
        directly invoking the check function, so that the rule's properties are updated
        consistently after the check function is executed.

        :param force: Set to True to run the check function no matter if there are failed
            dependencies. Set to False to only run the check if there there is not a failed
            dependency. Default is False.
        :type force: bool

        :return: The result returned by the check function.
        :rtype: any
        """

        if not force and self.has_failed_dependency():
            # Do not run the check function when it has a failed dependency, and not forcing.
            # Set the rule state to indicate that the check function not run
            self._valid = None
            self._error_items = []
            return False

        # Run the check function
        if self.check_func:
            kwargs = self.get_kwargs()
            try:
                result = self.check_func(**kwargs)
                # Try to set the valid and errors data properties on the rule from the result returned by
                # the check function. If the result does not have the expected attributes, we will continue on
                # but the rule will not be updated
                self._process_check_result(result)
                # Set the runtime exception to None since there was no error
                self._check_runtime_exception = None
            except Exception as runtime_error:
                result = None
                self._valid = False
                self._error_items = []
                self._check_runtime_exception = runtime_error
        else:
            # This is a manual check. It is considered valid if the user has checked it off.
            self._valid = self.manual_checked
            self._error_items = []
            result = None

        return result

    def exec_fix(self, pre_validate=True, force=False):
        """
        Execute the rule's fix function.

        Note that if this rule has dependencies, this method does not take those into account. See the
        ValidationManager resolve methods to handle rule dependencies.

        It is reccommended to use this method to execute the rule's fix function, instead of
        directly invoking the fix function, so that the rule's properties are updated
        consistently after the fix function is executed.

        :param pre_validate: Set to True to run the rule's validate first and pass its result
            to the rule's fix function.
        :type pre_validate: bool
        :param force: Set to True to run the fix function no matter if there are failed
            dependencies. Set to False to only run the fix if there there is not a failed
            dependency. Default is False.
        :type force: bool

        :return: The result of the fix function.
        :rtype: bool

        :raises Exception: If the fix operation was not successful.
        """

        if not self.fix_func:
            # Cannot fix if there is no fix function.
            return False

        if not force and self.has_failed_dependency():
            # Do not run the fix function if it has a failed dependency - the data may not be
            # in the required state for this rule's fix function to be applicable.
            return False

        if pre_validate:
            # Run the validate function right before fixing so that the rule's errors are the
            # most up to date with the current data (e.g. the data may have changed since the
            # last time validate was called and collected the error items).
            self.exec_check()

        # Get the key-word arguments and set the errors to pass to the fix function
        kwargs = self.get_kwargs()
        kwargs["errors"] = self.errors

        try:
            fix_result = self.fix_func(**kwargs)
            self._fix_runtime_exception = None
            # The fix function was executed - set the flag to True
            self._fix_executed = True
        except Exception as runtime_error:
            self._fix_runtime_exception = runtime_error
            fix_result = False

        return fix_result

    #########################################################################################################
    # Protected methods

    def _process_check_result(self, result):
        """
        Process the result returned by the validation rule check function and update the
        validation rule based on the result.

        The result can be one of:
            - dict with required keys: 'is_valid', 'errors'
            - object with required attributes: 'is_valid', 'errors'

        :param result: The result returned by a validation rule check function.
        :type result: dict | object
        """

        # First sanitize the result
        sanitized_result = self._sanitize_check_result(result)

        # Define the required fields for the check result
        required_fields = ("is_valid", "errors")

        if isinstance(sanitized_result, dict):
            for field in required_fields:
                if field not in sanitized_result:
                    raise ValueError(
                        "Validation Rule check function dict result missing key '{field}'".format(
                            field=field
                        )
                    )

            self._valid = sanitized_result["is_valid"]
            self._error_items = sanitized_result["errors"]

        elif isinstance(sanitized_result, object):
            for field in required_fields:
                if not hasattr(sanitized_result, field):
                    raise ValueError(
                        "Validation Rule check function object result missing attribute '{field}'".format(
                            field=field
                        )
                    )

            self._valid = sanitized_result.is_valid
            self._error_items = sanitized_result.errors

        else:
            raise TypeError(
                "Validation Rule check function result cannot be processed."
            )
