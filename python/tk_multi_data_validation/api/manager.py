# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import copy
from collections import deque

import sgtk
from sgtk.platform.qt import QtCore

from ..data.validation_rule import ValidationRule
from ..data.validation_rule_type import ValidationRuleType


class ValidationManager(object):
    """
    Manager class for data validation.

    This class is responsible for retrieving the data validation rules from the current bundle's settings,
    and creating the set of ValidationRule objects that define how the data should be validated.

    This class object may be passed to the :class:`tk_multi_data_validation.widgets.ValidationWidget` to help
    manager validation rules, and executing their actions.

    It also coordinates the execution of validation rule check and fix functions.
    """

    class ValidationNotifier(QtCore.QObject):
        """Inner helper class to emit signals around validation operations."""

        validate_rule_begin = QtCore.Signal(ValidationRule)
        validate_rule_finished = QtCore.Signal(ValidationRule)
        validate_all_begin = QtCore.Signal()
        validate_all_finished = QtCore.Signal()
        resolve_rule_begin = QtCore.Signal(ValidationRule)
        resolve_rule_finished = QtCore.Signal(ValidationRule)
        resolve_all_begin = QtCore.Signal()
        resolve_all_finished = QtCore.Signal()


    def __init__(self, rule_settings=None, include_rules=None, exclude_rules=None, validation_logger=None):
        """
        Initialize the validation manager from the settings data.

        :param rule_settings: The rule settings to use for this manager. Default is to use the
                              current bunlde's settings.
        :type rule_settings: dict
        :param include_rules: List of rule ids to include from the app's default rules list.
        :type include_rules: list<str>
        :param exclude_rules: List of rule ids to exclude from the app's default rules list.
        :type exclude_rules: list<str>
        :param validation_logger: This is a standard python logger to use during validation. A default logger
            will be provided if not supplied.

        :signal ValidationNotifier.validate_rule_begin(ValidationRule): Emits before a validation rule check
            function is executed. The returned parameter is the validation rule.
        :signal ValidationNotifier.validate_rule_finished(ValidationRule): Emits after a validation rule
            check function is executed. The returned parameter is the validation rule.
        """

        self._bundle = sgtk.platform.current_bundle()
        self._logger = validation_logger or self._bundle.logger
        self._notifier = self.ValidationNotifier()

        # Set the default rule types (in order). This can be set using the rule_types property.
        # TODO allow this to be config-based
        self._rule_types = [
            ValidationRuleType(ValidationRuleType.RULE_TYPE_NONE),
            ValidationRuleType(ValidationRuleType.RULE_TYPE_ACTIVE),
            ValidationRuleType(ValidationRuleType.RULE_TYPE_REQUIRED),
            ValidationRuleType(ValidationRuleType.RULE_TYPE_OPTIONAL),
        ]

        # Default accept function is not set, which will accept all rules
        self._validate_accepts = None

        #
        # Retrieve the validation data from given settings or get them from the hook data validator hook.
        # Create the set of ValidationRules from the validation data retrieved.
        #
        validation_data = self._bundle.execute_hook_method("hook_data_validator", "get_validation_data")
        self.__data = copy.deepcopy(validation_data)
        self.__rules = []
        self.__error_rules = {}

        rule_settings = rule_settings or self._bundle.settings.get("rules")
        for rule_item in rule_settings:
            rule_id = rule_item["id"]
            
            if include_rules and not rule_id in include_rules:
                continue

            if exclude_rules and rule_id in exclude_rules:
                continue

            rule_data = self.get_data(rule_id)
            if rule_data:
                rule_data.update(rule_item)

            rule = ValidationRule(rule_data)
            self.__rules.append(rule)


    #########################################################################################################
    # Properties

    @property
    def notifier(self):
        """Get the notifier for the validation manager."""
        return self._notifier

    @property
    def data(self):
        """Get the raw validation data."""
        return self.__data
    
    @property
    def rules(self):
        """Get the list of validtaion rules obtained from the validation data."""
        return self.__rules
    
    @property
    def rule_types(self):
        """Get or set the rule types."""
        return self._rule_types

    @rule_types.setter
    def rule_types(self, type_data):
        self._rule_types = type_data

    @property
    def errors(self):
        """Get the list of rules which did not pass the last time their respective validate function was executed."""
        return self.__error_rules

    @property
    def validate_accepts(self):
        """
        Get or set the function called to check if the validation should be applied to the given rule.

        This property must be a function that takes a single param (ValidationRule) and returns a bool to
        indicate if the rule should be validated or not.
        """
        return self._validate_accepts

    @validate_accepts.setter
    def validate_accepts(self, fn):
        self._validate_accepts = fn

    #########################################################################################################
    # Public functions

    def get_data(self, validation_key):
        """
        Return the validation data for the given key.
        
        :param validation_key: The unique identifier for the validation item.
        :type validation_key: str
        
        :return: The validation data
        :rtype: dict
        """

        return self.data.get(validation_key)
    
    def reset(self):
        """
        Reset the manager state.

        Clear the errors.
        """

        self.__error_rules = {}
    
    def validate(self):
        """
        Validate the DCC data by executing all validation rule check functions.

        :return: True if all validation rule checks passed (data is valid), else False.
        :rtype: bool
        """

        self._notifier.validate_all_begin.emit()
        
        # Reset the manager state before performing validation
        self.reset()

        self.validate_rules(self.rules)

        self._notifier.validate_all_finished.emit()

        return not self.__error_rules

    @sgtk.LogManager.log_timing
    def validate_rules(self, rules):
        """
        Validate the given list of rules.

        :param rules: The list of rules.
        :type rules: list<ValidationRule>
        """

        for rule in rules:
            if self.validate_accepts and not self.validate_accepts(rule):
                # Skip rules that are not accepted
                continue
            self.validate_rule(rule)

    def validate_rule(self, rule, *args, **kwargs):
        """
        Validate the DCC data with the given rule.

        The check function executed to validate the DCC data is implemented by the ValidationRule (e.g. the
        manager does nothing to validate the data, it is just responsible for executing the validate
        functions).

        :param rule: The rule to validate data by
        :type rule: ValidationRule
        :param args: The arguments list to pass to the validation rule check function
        :type args: list
        :param kwargs: The keyword arguments dict to pass to the validation rule check function
        :type kwargs: dict

        :return: True if the validation rule check passed (data is valid for this rule), else False.
        :rtype: bool
        """

        # Emit a signal to notify that a specifc rule has started validation
        self._notifier.validate_rule_begin.emit(rule)

        # Run the validation rule check function
        print("Validation Manager validating rule", rule.name)
        rule.exec_check(*args, **kwargs)

        # Check if rule's valid state after executing its check function
        is_valid = rule.valid

        if is_valid:
            if rule.id in self.__error_rules:
                # Remove the rule from the error set
                del self.__error_rules[rule.id]
        else:
            # Add the rule to the error set
            self.__error_rules[rule.id] = rule

        # Emit a signal to notify that a specifc rule has finished validation
        self._notifier.validate_rule_finished.emit(rule)

        return is_valid

    def resolve(self, pre_validate=False, post_validate=False):
        """
        Resolve the current data violations found by the validate method.

        The fix function executed to resolve the DCC data violations is implemented by the ValidationRule
        (e.g. the manager does nothing to validate the data, it is just responsible for executing the
        fix functions).

        :param pre_validate: True will run the validation step before the resovle step, to ensure the
                             list of items to resolve is the most up to date.
        :type pre_validate: bool
        :param post_validate: True will run the validation step after the resolve step, to check that
                              the scene data is valid after resolution steps applied.
        :type post_validate: bool

        :return: True if the resolve operation was successful, else False. Note that if the post_validate
            param is False, this will always be True, since the return status is based on the status
            returned by post validating the data.
        :rtype: bool
        """

        success = True

        if pre_validate:
            # First run the validate method to check for data violations.
            self.validate()

        if not self.errors:
            # There are no data violations to resolve.
            return success

        # Resolve the data violations
        self.resolve_rules(self.errors.values())

        if post_validate:
            # Run validation step once all resolution actions compelted to ensure everything was fixed.
            success = self.validate()

        return success

    @sgtk.LogManager.log_timing
    def resolve_rules(self, rules):
        """
        Resolve the given list of rules.

        Steps to resolve rules:
            1. Iterate over all rules
                a. If the rule has no dependencies - resolve it immediately
                b. If the ruel has dependencies - add it to the queue to process later
            2. Process the queue of rules (with dependencies)
                a. If the rule's dependencies have been resolved - now resolve it and mark it as resolved
                b. If the rule's dependencies have not been resolved - add it back to the end of the queue

        Time complexity (n = number of rules):
            1. O(n)
            2. O(n^2) - worst case

        NOTE: Time complexity is not the best with O(n^2) but is probably good enough since the list of
        validation rules is not expected to be so large. If the number of rules does grow to be a large
        list, then this fix operation may need to be optimized (e.g. build a dependency tree that defines
        the order of fixing the rules).
        """

        print("ValidationManager resolvin rules...")

        self._notifier.resolve_all_begin.emit()

        # Add rules to the set once they have been resolved.
        resolved = set()
        # Add rules to the queue if they have dependencies that have not been resolved yet.
        queue = deque()
        queue_count = 0

        # First pass will resolve any rules without dependencies. Rules with dependencies will be added to
        # the queue to be resolved once all its dependencies are resolved.
        for rule in rules:
            if rule.dependencies:
                queue.append(rule)
                queue_count += 1
            else:
                self.resolve_rule(rule)
                resolved.add(rule.id)

        # Now process the queue of rules (that have dependencies). For each rule, check if all dependencies
        # are resolved, if yes, then resolve it and add it to the resolved list, else add it back to the end
        # of the queue to try again after all rules in the queue have been processed.
        #
        # Detect cycles by calculating the max number of iterations it would take to empty the queue, if this
        # count is exceeded, then there is a cycle. In the worst case, the each item depends on the item that
        # comes after it, which means it'll take n + (n-1) + (n-2) + ... + 2 + 1
        max_iters = max(queue_count, (queue_count * (queue_count - 1)) / 2)
        iter_count = 0
        while queue:
            if iter_count > max_iters:
                raise RecursionError("Detected cycle in Validation Rule dependencies.")
            iter_count += 1

            rule = queue.popleft()
            has_dependencies = False
            for dependency in rule.dependencies:
                if dependency not in resolved:
                    has_dependencies = True
                    break

            if has_dependencies:
                # Still unresolved dependencies, add it back to the end of the queue
                queue.append(rule)
            else:
                self.resolve_rule(rule)
                resolved.add(rule.id)

        self._notifier.resolve_all_finished.emit()

    def resolve_rule(self, rule):
        """
        Resolve the validation rule.
        
        :param rule: The validation rule to resolve
        :type rule: ValidationRule
        """

        print("\t"*len(rule.dependencies), rule.id, "(", " | ".join([d for d in rule.dependencies]), ")")

        self._notifier.resolve_rule_begin.emit(rule)
        rule.exec_fix()
        self._notifier.resolve_rule_finished.emit(rule)
