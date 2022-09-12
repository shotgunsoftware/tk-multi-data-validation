# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

from collections import deque

import sgtk

from ..api.data.validation_rule import ValidationRule
from ..api.data.validation_rule_type import ValidationRuleType


class ValidationManager(object):
    """
    Manager class for data validation.

    This class is responsible for retrieving the data validation rules from the current bundle's settings,
    and creating the set of ValidationRule objects that define how the data should be validated.

    This class object may be passed to the :class:`tk_multi_data_validation.widgets.ValidationWidget` to help
    manager validation rules, and executing their actions.

    It also coordinates the execution of validation rule check and fix functions.
    """

    def __init__(
        self,
        bundle=None,
        rule_settings=None,
        include_rules=None,
        exclude_rules=None,
        logger=None,
        notifier=None,
        has_ui=False,
        pre_validate_before_fix=True,
    ):
        """
        Initialize the validation manager from the settings data.

        The hook "hook_data_validation" will be used to get the validation data for the
        manager by calling the hook's method "get_validation_data". NOTE the data returned
        by this hook method will be modified.

        :param bundle: The bundle instance for the app.
        :type bundle: TankBundle
        :param rule_settings: The rule settings to use for this manager. Default is to use the
                              current bunlde's settings.
        :type rule_settings: dict
        :param include_rules: List of rule ids to include from the app's default rules list.
        :type include_rules: list<str>
        :param exclude_rules: List of rule ids to exclude from the app's default rules list.
        :type exclude_rules: list<str>
        :param logger: This is a standard python logger to use during validation. A default logger
            will be provided if not supplied.
        :type logger: A standard python logger.
        :param notifier: A notifier object to emit Qt signals.
        :type notifier: ValidationNotifer
        :param has_ui: Set to True if the manager is being used with a UI, else False.
        :type has_ui: bool
        :param pre_validate_before_fix: Set to True to ensure validate is executed before a
            rule is fixed.
        :type pre_validate_before_fix: bool

        :signal ValidationNotifier.validate_rule_begin(ValidationRule): Emits before a validation rule check
            function is executed. The returned parameter is the validation rule.
        :signal ValidationNotifier.validate_rule_finished(ValidationRule): Emits after a validation rule
            check function is executed. The returned parameter is the validation rule.
        """

        self._bundle = bundle or sgtk.platform.current_bundle()
        self._logger = logger or self._bundle.logger
        self._notifier = notifier
        self._has_ui = has_ui
        self._pre_validate_before_fix = pre_validate_before_fix

        # Set the default rule types (in order). This can be set using the rule_types property.
        # TODO allow this to be config-based
        self._rule_types = [
            ValidationRuleType(ValidationRuleType.RULE_TYPE_NONE),
            ValidationRuleType(ValidationRuleType.RULE_TYPE_ACTIVE),
            ValidationRuleType(ValidationRuleType.RULE_TYPE_REQUIRED),
            ValidationRuleType(ValidationRuleType.RULE_TYPE_OPTIONAL),
        ]

        # Default accept function is not set, which will accept all rules
        self._accept_rule_fn = None

        # Retrieve the validation data from the hook method. NOTE the data returned by this
        # hook method will be modified
        self.__data = self._bundle.execute_hook_method(
            "hook_data_validation", "get_validation_data"
        )
        self.__rules_by_id = {}
        self.__errors = {}

        # Create the set of ValidationRules from the validation data and the rules defined in
        # the settings
        rule_settings = rule_settings or self._bundle.get_setting("rules", [])
        for rule_item in rule_settings:
            rule_id = rule_item["id"]

            if include_rules and not rule_id in include_rules:
                continue

            if exclude_rules and rule_id in exclude_rules:
                continue

            rule_data = self.__data.get(rule_id)
            if not rule_data:
                self._logger.error(
                    "Data was not found for validation rule id '{}'".format(rule_id)
                )
                continue

            # Collect dependencies first, if any
            for dependency_id in rule_data.get("dependency_ids", []):
                dependency_data = self.__data.get(dependency_id)
                if dependency_data:
                    rule_data.setdefault("dependencies", {})[
                        dependency_id
                    ] = dependency_data.get("name")

            rule_data.update(rule_item)
            rule = ValidationRule(rule_data)
            self.__rules_by_id[rule.id] = rule

    #########################################################################################################
    # Properties

    @property
    def notifier(self):
        """Get the notifier for the validation manager."""
        return self._notifier

    @property
    def rules(self):
        """Get the list of validtaion rules obtained from the validation data."""
        return self.__rules_by_id.values()

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
        return self.__errors

    @property
    def accept_rule_fn(self):
        """
        Get or set the function called to check if the validation should be applied to the given rule.

        This property must be a function that takes a single param (ValidationRule) and returns a bool to
        indicate if the rule should be validated or not.
        """
        return self._accept_rule_fn

    @accept_rule_fn.setter
    def accept_rule_fn(self, fn):
        self._accept_rule_fn = fn

    @property
    def has_ui(self):
        """Get the flag indicating if this manager is running with a User Interface."""
        return self._has_ui

    @property
    def pre_validate_before_fix(self):
        """
        Get or set the property to run validate before fix.

        Set to True to ensure that validate is always executed before a rule is fixed. This
        ensure that the fix is applied to the most up to date data.

        Default is True.
        """
        return self._pre_validate_before_fix

    @pre_validate_before_fix.setter
    def pre_validate_before_fix(self, pre_validate):
        self._pre_validate_before_fix = pre_validate

    #########################################################################################################
    # Public functions

    def get_rule(self, rule_id):
        """
        Return the validation rule object for the id.

        :param rule_id: The validation rule unique identifier.
        :type rule_id: str

        :return: The validation rule.
        :rtype: ValidationRule
        """

        return self.__rules_by_id.get(rule_id)

    def reset(self):
        """
        Reset the manager state.

        Clear the errors.
        """

        self.__errors = {}

    def validate(self):
        """
        Validate the data by executing all validation rule check functions.

        This method will reset the current validation manager state before validating any
        rules. This means that any errors found on a previous validation operation will be
        removed.

        :return: True if all validation rule checks passed (data is valid), else False.
        :rtype: bool
        """

        if self.notifier:
            self.notifier.validate_all_begin.emit()

        try:
            # Reset the manager state before performing validation
            self.reset()
            self.validate_rules(self.rules, emit_signals=False)
        finally:
            if self.notifier:
                self.notifier.validate_all_finished.emit()

        return not self.__errors

    @sgtk.LogManager.log_timing
    def validate_rules(self, rules, emit_signals=True):
        """
        Validate the given list of rules.

        This method will not reset the current validation manager state. This means that
        if a rule was found to have errors and it is not processed in this validation
        operation, than the error will remain.

        If the `accept_rule_fn` function is defined, only rules that are accepted by the
        function will be validated. If the `accept_rule_fn` is not defiend, then all given
        rules will be validated.

        :param rules: The list of rules to validate. This method will also accept a single
            validation object.
        :type rules: list<ValidationRule> | ValidationRule
        :param emit_signals: True will emit notifier signals when validation begins and ends.
        :param emit_signals: bool
        """

        if isinstance(rules, ValidationRule):
            rules = [rules]

        if emit_signals and self.notifier:
            self.notifier.validate_all_begin.emit()

        try:
            for rule in rules:
                if not self.accept_rule_fn or self.accept_rule_fn(rule):
                    self.validate_rule(rule)
        finally:
            if emit_signals and self.notifier:
                self.notifier.validate_all_finished.emit()

    def validate_rule(self, rule, emit_signals=True):
        """
        Validate the data with the given rule.

        The check function executed to validate the DCC data is implemented by the ValidationRule (e.g. the
        manager does nothing to validate the data, it is just responsible for executing the validate
        functions).

        :param rule: The rule to validate data by
        :type rule: ValidationRule

        :return: True if the validation rule check passed (data is valid for this rule), else False.
        :rtype: bool
        """

        if not rule:
            return

        if emit_signals and self.notifier:
            # Emit a signal to notify that a specifc rule has started validation
            self.notifier.validate_rule_begin.emit(rule)

        try:
            # Run the validation rule check function
            self._logger.debug("Validating Rule: {}".format(rule.id))
            rule.exec_check()

            # Check if rule's valid state after executing its check function
            is_valid = rule.valid

            if is_valid:
                if rule.id in self.__errors:
                    # Remove the rule from the error set
                    del self.__errors[rule.id]
            else:
                # Add the rule to the error set
                self.__errors[rule.id] = rule
        finally:
            if emit_signals and self.notifier:
                # Emit a signal to notify that a specifc rule has finished validation
                self.notifier.validate_rule_finished.emit(rule)

        return is_valid

    def resolve(
        self, pre_validate=False, post_validate=False, retry_until_success=True
    ):
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
        :param retry_until_success: Set to True will try to fun the resolution operation until all
            rules have been resolved. The maximum number of tries to resolve will be equal to the
            number of rules in the manager. This will perform post validate step, evne if post validate
            has been set to False.
        :type retry_until_success: bool

        :return: True if the resolve operation was successful, else False. Note that if the post_validate
            param is False, this will always be True, since the return status is based on the status
            returned by post validating the data.
        :rtype: bool
        """

        if self.notifier:
            self.notifier.resolve_all_begin.emit()

        try:
            success = True

            if pre_validate:
                # First run the validate method to check for data violations.
                self.validate()

            if self.errors:
                # Resolve the data violations. Explicitly say not to fetch dependencies because this function
                # has validated all rules and all rules will be passed to resolve that will be fixed - if
                # dependencies are not included, then that means they have no errors and thus, do not need to
                # run their fix action to modify the data. Basically, this means dependencies can be ignored
                # as they will have no effect on the data.
                self.resolve_rules(
                    self.errors.values(), fetch_dependencies=False, emit_signals=False
                )

                if post_validate or retry_until_success:
                    # Run validation step once all resolution actions compelted to ensure everything was fixed.
                    success = self.validate()

                # Brute force try to resolve all errors - keep running the resolution on any errors found
                # from validate until there are none, or the max number of tries reached.
                #
                # New errors may occur if executing a rule's fix has side effects which cause another rule to
                # have errors. For example, rule A has no dependencies, rule B depends on rule A, and rule A
                # has errors, then only rule A's fix will be executed but it causes rule B to now have errors.
                # Rule B's fix will not be executed though, so even though resolve all was executed, we have
                # new errors.
                #
                # NOTE if this brute force method becomes slow, the resolve_rules method should be modified to
                # look up the reverse dependencies to add to the list of rules whose fix operatoins will be
                # executed.
                max_retry = len(self.rules) if retry_until_success else 0
                count = 0
                prev_errors = set()
                while not success and count < max_retry:
                    if prev_errors == set(self.errors):
                        # Nothing changed from the last attempt to resolve, stop retrying
                        count = max_retry
                    else:
                        self._logger.debug("Resolve retry attempt {}".format(count))

                        # Update the previous errors to the current set
                        prev_errors = set(self.errors)

                        # Attempt to resolve again
                        self.resolve_rules(
                            self.errors.values(),
                            fetch_dependencies=False,
                            emit_signals=False,
                        )
                        # Check for errors
                        success = self.validate()
                        # Update retry count
                        count += 1

                if retry_until_success and not success:
                    self._logger.debug(
                        "Failed to resolve after max retry attempts. There may be a rule dependecy cycle."
                    )

        finally:
            if self.notifier:
                self.notifier.resolve_all_finished.emit()

        return success

    @sgtk.LogManager.log_timing
    def resolve_rules(self, rules, fetch_dependencies=None, emit_signals=True):
        """
        Resolve the given list of rules.

        Steps to resolve rules
        1. Iterate over all rules

            a. If the rule has no dependencies - resolve it immediately
            b. If the rule has dependencies - add it to the queue to process later

        2. If `fetch_dependencies` is not explicitly set as False, check if all dependencies
           are provided

            a. If missing dependencies and `fetch_dependencies` not explicitly set to True then
               prompt user to fetch and resolve dependencies
            b. If `fetch_dependencies` is explicitly set to True or user answered YES to (a),
               then try to find any missing dependencies in the manager, and process them as
               done with the other rules

        3. Process the queue of rules (that have dependencies)

            a. If the rule's dependencies have been resolved or ignored - now resolve it and
               mark it as resolved
            b. If the rule's dependencies have not been resolved - add it back to the end of
               the queue

        Time complexity (n = number of rules)

        1. O(n)
        2. O(n^2) - worst case

        NOTE: Time complexity is not the best with O(n^2) but is probably good enough since the list of
        validation rules is not expected to be so large. If the number of rules does grow to be a large
        list, then this fix operation may need to be optimized (e.g. build a dependency tree that defines
        the order of fixing the rules).

        :param rules: The list of rules to resolve.
        :type rules: list<ValidationRule>
        :param fetch_dependencies: Set to True to ensure all dependencies for a reule are resolved before
            the rule itself is resolved. Set to False will not fetch any missing dependencies to resolve.
        :type fetch_dependencies: bool
        :param emit_signals: Set to True to emit notifier signals for resolve operation.
        :type emit_signals: bool
        """

        if not rules:
            return

        if emit_signals:
            self.notifier.resolve_all_begin.emit()

        try:
            # The set of rule ids passed to resolve - this set gets populated the first the rules are iterated
            # through to check then check if the necessary dependencies are available to resolve first. Any
            # dependency rules will be added in the step wheere dependencies are checked.
            rule_ids = set()
            # Add rules to the set once they have been resolved.
            resolved = set()
            # The set of all dependencies to required by the list of rules passed to resolve.
            all_dependencies = set()
            # Dependencies mapping - update this mapping as dependencies are resolved.
            dependencies = {}
            # Add rules to the queue if they have dependencies that have not been resolved yet.
            queue = deque()
            queue_count = 0

            def process_rule(rule):
                """
                Helper function to intially process a validation rule.

                1. Add the rule to the set of rule ids.
                2a. If the rule does not have dependencies, resolve it immediately and add it to the resolved
                    set.
                2b. If the rule has dependencies, update the dependencies map and list, and add it to the queue
                    to process later once all of its dependencies are resolved.

                :param rule: The rule to process
                :type rule: ValidationRule

                :return: True if the rule was resolved, else False if it was not resolved and added to the queue.
                :rtype: bool
                """

                if not rule or rule in rule_ids:
                    # Trivially return True for rule that does not exist, and skip rules that have already been
                    # processed
                    return True

                rule_ids.add(rule.id)

                dependencies_ids = rule.get_dependency_ids()
                if dependencies_ids:
                    # Copy the list of dependencies so that the original dependency list is not modified, and
                    # using a set instead for faster lookup and removal
                    rule_dependencies_set = set(dependencies_ids)
                    dependencies[rule.id] = rule_dependencies_set
                    # Only add dependencies to the set if they have not been processed yet.
                    all_dependencies.update(rule_dependencies_set.difference(rule_ids))

                    queue.append(rule)
                    return False

                # No dependencies, resolve it immediately
                self.resolve_rule(rule)
                resolved.add(rule.id)
                return True

            # First pass will resolve any rules without dependencies. Rules with dependencies will be added to
            # the queue to be resolved once all its dependencies are resolved.
            for rule in rules:
                if not self.accept_rule_fn or self.accept_rule_fn(rule):
                    if not process_rule(rule):
                        queue_count += 1

            # Check for dependencies and fetch them if specified
            if fetch_dependencies or fetch_dependencies is None:
                # Keep processing dependencies until the set is empty - dependencies may be added during
                # while iterating if a dependency and another dependency
                while all_dependencies:
                    dependency_rule_id = all_dependencies.pop()
                    if dependency_rule_id in rule_ids:
                        # Dependency is already found
                        continue

                    dependency_rule = self.get_rule(dependency_rule_id)
                    if not dependency_rule:
                        # Skip dependenceis that the manager does not have
                        continue

                    # If not yet specified, prompt user to fetch missing dependencies
                    if fetch_dependencies is None:
                        if self.notifier:
                            self.notifier.about_to_open_msg_box.emit()

                        # NOTE for now this is simplified by asking to fetch all or not - if requested this could ask
                        # to only individual dependencies
                        if self.has_ui:
                            from sgtk.platform.qt import QtGui

                            answer = QtGui.QMessageBox.question(
                                None,
                                "Fix Dependencies",
                                "This operation will apply additional fixes for dependencies.",
                                QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                            )
                            fetch_dependencies = bool(answer == QtGui.QMessageBox.Ok)
                        else:
                            # TODO allow headless mode to specify whether or not to fetch. Default to fetch
                            fetch_dependencies = True

                        if self.notifier:
                            self.notifier.msg_box_closed.emit()

                    if fetch_dependencies:
                        if not process_rule(dependency_rule):
                            queue_count += 1
                    else:
                        # The user canceled the operation
                        if emit_signals and self.notifier:
                            self.notifier.resolve_all_finished.emit()
                        return

            # Now process the queue of rules, which have dependencies. For each rule, if all dependencies are
            # resolved or ignored, then resolve it and add it to the resolved list, else add it back to the end
            # of the queue to try again after all rules in the queue have been processed.
            #
            # Detect cycles by calculating the max number of iterations it would take to empty the queue, if this
            # count is exceeded, then there is a cycle. In the worst case, the each item depends on the item that
            # comes after it, which means it'll take n + (n-1) + (n-2) + ... + 2 + 1
            max_iters = queue_count + (queue_count * (queue_count - 1) / 2)
            iter_count = 0
            while queue:
                if iter_count > max_iters:
                    raise RecursionError(
                        "Detected cycle in Validation Rule dependencies."
                    )
                iter_count += 1

                # Get the next rule to process from the queue
                rule = queue.popleft()

                # Determine if dependencies have been resolved
                has_dependencies = False
                rule_dependencies = dependencies.get(rule.id, [])
                while rule_dependencies and not has_dependencies:
                    dependency_rule_id = rule_dependencies.pop()

                    if dependency_rule_id not in rule_ids:
                        if fetch_dependencies:
                            self._logger.error(
                                "Dependency not resolved '{}'".format(
                                    dependency_rule_id
                                )
                            )
                        # Dependency is ignored
                        continue

                    if dependency_rule_id in resolved:
                        # Dependency has already been resolved
                        continue

                    # This dependency is not resolved yet, add it back to the set
                    has_dependencies = True
                    rule_dependencies.add(dependency_rule_id)

                if has_dependencies:
                    # Still unresolved dependencies, add it back to the end of the queue
                    queue.append(rule)
                else:
                    self.resolve_rule(rule)
                    resolved.add(rule.id)

        finally:
            if emit_signals and self.notifier:
                self.notifier.resolve_all_finished.emit()

    def resolve_rule(self, rule):
        """
        Resolve the validation rule.

        :param rule: The validation rule to resolve
        :type rule: ValidationRule
        """

        self._logger.debug(
            "\nResolving Rule: {}\nDependencies: {}".format(
                rule.id, ", ".join([d for d in rule.get_dependency_names()])
            )
        )

        if self.notifier:
            self.notifier.resolve_rule_begin.emit(rule)

        try:
            rule.exec_fix(pre_validate=self.pre_validate_before_fix)
        finally:
            if self.notifier:
                self.notifier.resolve_rule_finished.emit(rule)
