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
# Fixtures and mock data for ValidationRule pytests


@pytest.fixture


#########################################################################################################
# ValidationRule pytests


def test_validadtion_rule_init_defaults(rule_data, bundle):
    """
    Test the ValidationRule init.
    """

    rule_data = {
        "id": "rule_1",
        "name": "Rule #1",
        "description": "This is the first test rule.",
        "error_msg": "This is the error message",
        "check_func": lambda: {"is_valid": True, "errors": None},
        "fix_func": lambda: {"is_valid": True, "errors": None},
    }
    rule = ValidationRule(rule_data, bundle=bundle)

    assert rule._data is rule_data
    assert rule.checked is rule_data.get("checked", False)
    assert rule.manual_checked is False
    assert rule.valid is None
    assert rule.errors == []
    assert rule.fix_executed is False

    for key, value in rule_data.items():
        if hasattr(rule, key):
            assert value == getattr(rule, key)
        assert value == rule.get_data(key)


def test_validadtion_rule_type(bundle):
    """
    Test the ValidationRule type object.
    """

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
    """
    Test the ValidationRule type object.
    """

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


def test_validadtion_rule_dependencies(bundle):
    """
    Test the ValidationRule dependencies.
    """

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


def test_validadtion_rule_exec_check(bundle):
    """
    Test the ValidationRule check function.
    """

    success_rule_result = {"is_valid": True, "errors": None}
    success_rule = {
        "id": "rule",
        "name": "Rule",
        "check_func": MagicMock(return_value=success_rule_result),
    }
    rule = ValidationRule(success_rule, bundle=bundle)
    result = rule.exec_check()
    assert result == success_rule_result
    assert rule.valid is True
    assert not rule.errors
    success_rule["check_func"].assert_called_once()

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
    assert rule.errors == []

    rule.manual_checked = True
    result = rule.exec_check()
    assert result is None
    assert rule.valid is True
    assert rule.errors == []


def test_validadtion_rule_exec_fix(bundle):
    """
    Test the ValidationRule fix function.
    """

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
