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
    """Test the ValidationRule dependencies."""

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
    """Test the ValidationRule check function."""

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
    assert rule.errors == None
    assert rule._check_runtime_exception is None
    success_rule["check_func"].assert_called_once()


def test_validadtion_rule_exec_check_with_errors(bundle):
    """Test the ValidationRule check function."""

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
    assert not rule.errors
    error_rule["check_func"].assert_called_once()

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
    error_rule_with_data["check_func"].assert_called_once()

    dict_errors = [4, 5, 6]
    dict_result = {"is_valid": True, "errors": dict_errors}
    error_rule_with_dict_result = {
        "id": "rule",
        "name": "Rule",
        "check_func": MagicMock(return_value=dict_result),
    }
    rule = ValidationRule(error_rule_with_dict_result, bundle=bundle)
    result = rule.exec_check()
    assert result == dict_result
    assert rule.valid is True
    assert rule.errors == dict_errors
    error_rule_with_dict_result["check_func"].assert_called_once()

    manual_rule = {"id": "rule", "name": "No check function provided"}
    rule = ValidationRule(manual_rule, bundle=bundle)
    rule.manual_checked = False
    result = rule.exec_check()
    assert result is None
    assert rule.valid is False
    assert rule.errors == None

    rule.manual_checked = True
    result = rule.exec_check()
    assert result is None
    assert rule.valid is True
    assert rule.errors == None


def test_validadtion_rule_exec_fix(bundle):
    """Test the ValidationRule fix function."""

    rule_with_fix = {
        "id": "rule",
        "name": "Rule",
        "fix_func": MagicMock(),
    }
    rule_without_fix = {"id": "rule", "name": "Rule", "name": "No fix func provided"}
    errmsg = "Fix threw an exception"
    rule_with_fix_throws_exception = {
        "id": "rule",
        "name": "Rule",
        "fix_func": MagicMock(side_effect=Exception(errmsg)),
    }

    rule = ValidationRule(rule_with_fix, bundle=bundle)
    assert rule.fix_executed is False
    rule.exec_fix()
    assert rule.fix_executed is True
    rule_with_fix["fix_func"].assert_called_once()

    rule = ValidationRule(rule_without_fix, bundle=bundle)
    assert rule.fix_executed is False
    rule.exec_fix()
    # Nothing should have happened, and the flag that fix was executed should remain False
    assert rule.fix_executed is False

    rule = ValidationRule(rule_with_fix_throws_exception, bundle=bundle)
    assert rule.fix_executed is False
    with pytest.raises(Exception) as fix_error:
        rule.exec_fix()
        assert str(fix_error) == errmsg
        assert rule.fix_executed is False
        rule_with_fix_throws_exception["fix_func"].assert_called_once()
