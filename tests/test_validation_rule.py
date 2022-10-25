# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import os
import sys

import pytest
from mock import MagicMock

# Manually add the app modules to the path in order to import them here.
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python"))
app_dir = os.path.abspath(os.path.join(base_dir, "tk_multi_data_validation"))
api_dir = os.path.abspath(os.path.join(app_dir, "api"))
data_dir = os.path.abspath(os.path.join(api_dir, "data"))
sys.path.extend([base_dir, app_dir, api_dir, data_dir])
from tk_multi_data_validation.api.data import ValidationRule, ValidationRuleType


#########################################################################################################
# Helper classes


class CheckResultMissingIsValid:
    """Mock a check result object passed to the validation rule _process_check_result."""

    def __init__(self, errors):
        self.errors = errors


class CheckResultMissingErrors:
    """Mock a check result object passed to the validation rule _process_check_result."""

    def __init__(self, is_valid):
        self.is_valid = is_valid


class CheckResultMissingBothIsValidAndErrors:
    """Mock a check result object passed to the validation rule _process_check_result."""

    def __init__(self, name):
        self.name = name


class ACorrectCheckResult:
    """Mock a check result object passed to the validation rule _process_check_result."""

    def __init__(self, is_valid, errors):
        self.is_valid = is_valid
        self.errors = errors
        self.it_can_have_other_stuff_but_is_ignored = True


#########################################################################################################
# ValidationRule pytests


def test_validadtion_rule_init_defaults(bundle):
    """Test the ValidationRule init default values."""

    # The bare minimum data to create a Validation Rule object
    rule_data = {
        "id": "rule_1",
        "name": "Rule #1",
    }
    rule = ValidationRule(rule_data, bundle=bundle)

    assert rule._data is rule_data
    assert rule.id == rule_data["id"]
    assert rule.name == rule_data["name"]
    assert rule.description == ""
    assert rule.check_func is None
    assert rule.fix_func is None
    assert rule.error_message == ""
    assert rule.warn_message is None
    assert rule.check_name == "Validate"
    assert rule.fix_name == "Fix"
    assert rule.fix_tooltip == "Click to fix this data violation."
    assert rule.actions == []
    assert rule.item_actions == []
    assert rule.dependencies == {}
    assert rule.data_type is None
    assert rule.required is True
    assert rule.optional is False
    assert rule.checked is False
    assert rule.manual is True
    assert rule.manual_checked is False
    assert rule.valid is None
    assert rule.errors == None
    assert rule.fix_executed is False


def test_validadtion_rule_init_with_data(bundle):
    """Test the ValidationRule init sets the given data."""

    rule_data = {
        "id": "rule_1",
        "name": "Rule #1",
        "description": "This is the first test rule.",
        "error_msg": "This is the error message",
        "warn_msg": "This is the warning message",
        "check_name": "My Check Name",
        "fix_name": "My Fix Name",
        "fix_tooltip": "My fix tooltip",
        "data_type": "My data type",
        "actions": "My actions should be a list, but this is enough to test init",
        "item_actions": "My item actions should be a list, but this is enough to test init",
        "dependencies": "My dependencies should be a dict, but this is enough to test init",
        "check_func": "My check func should be function, but this is enough to test init",
        "fix_func": "My fix func should be function, but this is enough to test init",
        "get_kwargs": "My get_kwargs should be a function, but this is enough to test init",
    }
    rule = ValidationRule(rule_data, bundle=bundle)

    assert rule._data is rule_data
    assert rule.id == rule_data["id"]
    assert rule.name == rule_data["name"]
    assert rule.description == rule_data["description"]
    assert rule.check_func == rule_data["check_func"]
    assert rule.fix_func == rule_data["fix_func"]
    assert rule.error_message == rule_data["error_msg"]
    assert rule.warn_message == rule_data["warn_msg"]
    assert rule.check_name == rule_data["check_name"]
    assert rule.fix_name == rule_data["fix_name"]
    assert rule.fix_tooltip == rule_data["fix_tooltip"]
    assert rule.data_type == rule_data["data_type"]
    assert rule.actions == rule_data["actions"]
    assert rule.item_actions == rule_data["item_actions"]
    assert rule.dependencies == rule_data["dependencies"]
    assert rule.get_kwargs == rule_data["get_kwargs"]
    assert rule.required is True
    assert rule.optional is False
    assert rule.checked is False
    assert rule.manual is False
    assert rule.manual_checked is False
    assert rule.valid is None
    assert rule.errors == None
    assert rule.fix_executed is False


def test_validadtion_rule_type(bundle):
    """Test the ValidationRule type object."""

    rule_data = {
        "required_rule": {
            "id": "rule_1",
            "name": "Rule #1",
            "required": True,
        },
        "optional_rule": {
            "id": "rule_2",
            "name": "Rule #2",
            "required": False,
        },
    }

    required_rule = ValidationRule(rule_data["required_rule"], bundle=bundle)
    assert required_rule.type == ValidationRuleType(
        ValidationRuleType.RULE_TYPE_REQUIRED
    )

    optional_rule = ValidationRule(rule_data["optional_rule"], bundle=bundle)
    assert optional_rule.type == ValidationRuleType(
        ValidationRuleType.RULE_TYPE_OPTIONAL
    )


def test_validadtion_rule_manual_property(bundle):
    """Test the ValidationRule manual property."""

    rule_data = {
        "manual_rule": {
            "id": "manual_1",
            "name": "This is manual rule (no check or fix func defined)",
        },
        "non_manual_1": {
            "id": "manual_2",
            "name": "Manual 2",
            "check_func": True,
        },
        "non_manual_2": {
            "id": "manual_3",
            "name": "Manual 3",
            "fix_func": True,
        },
        "non_manual_3": {
            "id": "manual_4",
            "name": "Manual 4",
            "check_func": True,
            "fix_func": True,
        },
    }

    manual_rule = ValidationRule(rule_data["manual_rule"], bundle=bundle)
    assert manual_rule.manual is True

    non_manual_1 = ValidationRule(rule_data["non_manual_1"], bundle=bundle)
    assert non_manual_1.manual is False

    non_manual_2 = ValidationRule(rule_data["non_manual_2"], bundle=bundle)
    assert non_manual_2.manual is False

    non_manual_3 = ValidationRule(rule_data["non_manual_3"], bundle=bundle)
    assert non_manual_3.manual is False


def test_validadtion_rule_dependencies_property(bundle):
    """Test the ValidationRule dependencies property."""

    rule_data = {
        "id": "rule",
        "name": "Rule",
        "dependencies": {
            "dep_1_id": "dep_1_name",
            "dep_2_id": "dep_2_name",
            "dep_3_id": "dep_3_name",
        },
    }

    rule = ValidationRule(rule_data, bundle=bundle)
    rule.dependencies == rule_data["dependencies"]
    rule.get_dependency_ids() == rule_data["dependencies"].keys()
    rule.get_dependency_names() == rule_data["dependencies"].values()


def test_validadtion_rule_exec_check_success(bundle):
    """Test the ValidationRule exec check function successfully executes."""

    success_rule_result = {"is_valid": True, "errors": []}
    success_rule = {
        "id": "rule",
        "name": "Rule",
        "check_func": MagicMock(return_value=success_rule_result),
    }
    rule = ValidationRule(success_rule, bundle=bundle)
    result = rule.exec_check()
    assert result == success_rule_result
    assert rule.valid is True
    assert rule.errors == []
    assert rule._check_runtime_exception is None
    success_rule["check_func"].assert_called_once()


def test_validadtion_rule_exec_check_not_valid(bundle):
    """Test the ValidationRule exec check function executes but not valid."""

    error_rule_result = {"is_valid": False, "errors": None}
    error_rule = {
        "id": "rule",
        "name": "Rule",
        "check_func": MagicMock(return_value=error_rule_result),
    }
    rule = ValidationRule(error_rule, bundle=bundle)
    result = rule.exec_check()
    assert result == error_rule_result
    assert rule.valid is False
    assert rule.errors is None
    assert rule._check_runtime_exception is None
    error_rule["check_func"].assert_called_once()


def test_validadtion_rule_exec_check_with_errors_list(bundle):
    """Test the ValidationRule exec check function executes but not valid and has error list."""

    error_list = [1, 2, 3]
    error_rule_with_data_result = {"is_valid": False, "errors": error_list}
    error_rule_with_data = {
        "id": "rule",
        "name": "Rule",
        "check_func": MagicMock(return_value=error_rule_with_data_result),
    }
    rule = ValidationRule(error_rule_with_data, bundle=bundle)
    result = rule.exec_check()
    assert result == error_rule_with_data_result
    assert rule.valid is False
    assert rule.errors == error_list
    assert rule._check_runtime_exception is None
    error_rule_with_data["check_func"].assert_called_once()


def test_validadtion_rule_exec_manual_not_valid(bundle):
    """Test the ValidationRule exec check function when rule is manual (has no check function nor fix function)."""

    manual_rule = {"id": "rule", "name": "No check function provided"}
    rule = ValidationRule(manual_rule, bundle=bundle)
    rule.manual_checked = False
    result = rule.exec_check()
    assert result is None
    assert rule.valid is False
    assert rule.errors == None
    assert rule._check_runtime_exception is None


def test_validadtion_rule_exec_manual_valid(bundle):
    """Test the ValidationRule exec check function when rule is manual (has no check function nor fix function) and not valid."""

    manual_rule = {"id": "rule", "name": "No check function provided"}
    rule = ValidationRule(manual_rule, bundle=bundle)
    rule.manual_checked = True
    result = rule.exec_check()
    assert result is None
    assert rule.valid is True
    assert rule.errors is None
    assert rule._check_runtime_exception is None


def test_validadtion_rule_exec_semi_automatied(bundle):
    """Test the ValidationRule exec check function when rule has fix function but not check function."""

    # A semi-automated rule has a fix func but not a check func
    semi_automated_rule = {
        "id": "rule",
        "name": "No check function provided",
        "fix_func": True,
    }
    rule = ValidationRule(semi_automated_rule, bundle=bundle)
    result = rule.exec_check()
    assert rule.valid is True
    assert result is None
    assert rule.errors is None
    assert rule._check_runtime_exception is None


def test_validadtion_rule_exec_throws_exception(bundle):
    """Test the ValidationRule exec check function when rule check func throws an exception."""

    exception = Exception("check threw an exception")
    semi_automated_rule = {
        "id": "rule",
        "name": "Throw exception",
        "check_func": MagicMock(side_effect=exception),
    }
    rule = ValidationRule(semi_automated_rule, bundle=bundle)
    result = rule.exec_check()
    assert rule.valid is False
    assert result is None
    assert rule.errors is None
    assert rule._check_runtime_exception == exception


def test_validadtion_rule_exec_fix(bundle):
    """Test the ValidationRule fix function executes successfully."""

    rule_with_fix = {
        "id": "rule",
        "name": "Rule",
        "fix_func": MagicMock(),
    }

    rule = ValidationRule(rule_with_fix, bundle=bundle)
    assert rule.fix_executed is False
    rule.exec_fix()
    assert rule.fix_executed is True
    assert rule._fix_runtime_exception is None
    rule_with_fix["fix_func"].assert_called_once()


def test_validadtion_rule_exec_fix_no_func(bundle):
    """Test the ValidationRule exec fix function when rule has no fix function defined."""

    rule_without_fix = {"id": "rule", "name": "Rule", "name": "No fix func provided"}

    rule = ValidationRule(rule_without_fix, bundle=bundle)
    assert rule.fix_executed is False
    rule.exec_fix()
    # Nothing should have happened, and the flag that fix was executed should remain False
    assert rule.fix_executed is False
    assert rule._fix_runtime_exception is None


def test_validadtion_rule_exec_fix_throws_exception(bundle):
    """Test the ValidationRule exec fix function when fix function throws an exception."""

    exception = Exception("Fix threw an exception")
    rule_with_fix_throws_exception = {
        "id": "rule",
        "name": "Rule",
        "fix_func": MagicMock(side_effect=exception),
    }

    rule = ValidationRule(rule_with_fix_throws_exception, bundle=bundle)
    assert rule.fix_executed is False

    rule.exec_fix()
    assert rule.fix_executed is False
    assert rule._fix_runtime_exception == exception
    rule_with_fix_throws_exception["fix_func"].assert_called_once()


def test_validadtion_rule_exec_fix_exit_early(bundle):
    """Test the ValidationRule exec fix function exits early (does not execute fix func) because rule is already valid."""

    rule_data = {
        "id": "rule",
        "name": "Rule",
        "check_func": MagicMock(),
        "fix_func": MagicMock(),
    }

    rule = ValidationRule(rule_data, bundle=bundle)
    # Hack the valid property to mimic the pre validate found the rule to already be valid
    rule._valid = True
    assert rule.valid is True
    assert rule.fix_executed is False

    rule.exec_fix()
    # Since the rule was already marked valid and it has a check function, the fix will not execute
    assert rule.fix_executed is False
    rule.fix_func.assert_not_called()


def test_validadtion_rule_exec_fix_do_not_exit_early_because_no_check_func(bundle):
    """Test the ValidationRule exec fix function does not exit early because no check func to say that the rule is truly valid."""

    rule_data = {
        "id": "rule",
        "name": "Rule",
        "fix_func": MagicMock(),
    }

    rule = ValidationRule(rule_data, bundle=bundle)
    # Hack the valid property to mimic the pre validate found the rule to already be valid
    rule._valid = True
    assert rule.valid is True
    assert rule.fix_executed is False

    rule.exec_fix()
    # The rule was already marked valid but it does not have a check function, the fix will execute
    assert rule.fix_executed is True
    rule.fix_func.assert_called_once()


def test_validadtion_rule_exec_fix_do_not_exit_early_because_not_valid(bundle):
    """Test the ValidationRule exec fix function does not exit early because rule is not valid."""

    rule_data = {
        "id": "rule",
        "name": "Rule",
        "fix_func": MagicMock(),
    }

    rule = ValidationRule(rule_data, bundle=bundle)
    assert not rule.valid
    assert rule.fix_executed is False

    rule.exec_fix()
    # The rule was not marked valid (does not matter if it has a check function), the fix will execute
    assert rule.fix_executed is True
    rule.fix_func.assert_called_once()


def test_validation_rule_exec_fix_has_failed_dependencies(bundle):
    """Test the ValidationRule exec fix function does not run fix because it has failed dependencies."""

    rule_data = {
        "id": "rule",
        "name": "Rule",
        "fix_func": MagicMock(),
    }

    rule = ValidationRule(rule_data, bundle=bundle)
    # Just set it to something that is not None
    rule.set_failed_dependency(True)
    assert not rule.valid
    assert rule.fix_executed is False
    assert rule.has_failed_dependency()

    rule.exec_fix()
    # The fix not executed because it has failed dependencies
    assert rule.fix_executed is False
    rule.fix_func.assert_not_called()


def test_validation_rule_exec_fix_has_failed_dependencies_but_force(bundle):
    """Test the ValidationRule exec fix function does execute the fix because it is forcing, even with failed dependenceis."""

    rule_data = {
        "id": "rule",
        "name": "Rule",
        "fix_func": MagicMock(),
    }

    rule = ValidationRule(rule_data, bundle=bundle)
    # Just set it to something that is not None
    rule.set_failed_dependency(True)
    assert not rule.valid
    assert rule.fix_executed is False
    assert rule.has_failed_dependency()

    rule.exec_fix(force=True)
    # The fix executed because it has failed dependencies but is forcing
    assert rule.fix_executed is True
    rule.fix_func.assert_called_once()


@pytest.mark.parametrize(
    "result_data",
    [
        (None, ValueError),
        (1, ValueError),
        ("bad result", ValueError),
    ],
)
def test_validaiton_rule_process_check_result_bad_result_type(bundle, result_data):
    """Test the ValidationRule _process_check_result function with unsupported result object type."""

    rule_data = {
        "id": "rule",
        "name": "Rule",
    }
    rule = ValidationRule(rule_data, bundle=bundle)

    result, exception_class = result_data
    with pytest.raises(exception_class):
        rule._process_check_result(result)


@pytest.mark.parametrize(
    "result_data",
    [
        ({}, ValueError),
        ({"is_valid": True}, ValueError),
        ({"errors": []}, ValueError),
        (CheckResultMissingIsValid([]), ValueError),
        (CheckResultMissingErrors(True), ValueError),
        (CheckResultMissingBothIsValidAndErrors("bad result"), ValueError),
    ],
)
def test_validaiton_rule_process_check_result_bad_result_data(bundle, result_data):
    """Test the ValidationRule _process_check_result function with bad result object data."""

    rule_data = {
        "id": "rule",
        "name": "Rule",
    }
    rule = ValidationRule(rule_data, bundle=bundle)

    result, exception_class = result_data
    with pytest.raises(exception_class):
        rule._process_check_result(result)


@pytest.mark.parametrize(
    "result",
    [
        {"is_valid": True, "errors": []},
        {"is_valid": False, "errors": [1, 2, 3]},
    ],
)
def test_validaiton_rule_process_check_result_with_dict(bundle, result):
    """Test the ValidationRule _process_check_result function with result dict data."""

    rule_data = {
        "id": "rule",
        "name": "Rule",
    }
    rule = ValidationRule(rule_data, bundle=bundle)

    sanitized_result = rule._process_check_result(result)
    # Our mock should just return the result as is
    assert sanitized_result == result
    # Now actually validate the data
    assert rule.valid == result["is_valid"]
    assert rule.errors == result["errors"]


@pytest.mark.parametrize(
    "result",
    [
        ACorrectCheckResult(True, None),
        ACorrectCheckResult(False, [4, 5, 6]),
    ],
)
def test_validaiton_rule_process_check_result_with_object(bundle, result):
    """Test the ValidationRule _process_check_result function with result object data."""

    rule_data = {
        "id": "rule",
        "name": "Rule",
    }
    rule = ValidationRule(rule_data, bundle=bundle)

    sanitized_result = rule._process_check_result(result)
    # Our mock should just return the result as is
    assert sanitized_result == result
    # Now actually validate the data
    assert rule.valid == result.is_valid
    assert rule.errors == result.errors
