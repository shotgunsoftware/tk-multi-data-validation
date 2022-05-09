# Copyright (c) 2020 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import copy
import os
import sys

import pytest
import mock
from mock import call, patch, MagicMock

from app_test_base import AppTestBase

from tank_test.tank_test_base import setUpModule  # noqa

# Manually add the app modules to the path in order to import them here.
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python"))
app_dir = os.path.abspath(os.path.join(base_dir, "tk_multi_data_validation"))
api_dir = os.path.abspath(os.path.join(app_dir, "api"))
sys.path.extend([base_dir, app_dir, api_dir])
from tk_multi_data_validation.api import ValidationManager


#########################################################################################################
# Fixtures and mock data for ValidationManager pytests
#########################################################################################################


class Notifier(object):
    """Mock object for testing."""


class Logger(object):
    """Mock object for testing."""

    def debug(self, msg):
        pass

    def error(self, msg):
        pass


class CheckResult(object):
    def __init__(self, is_valid, errors=None):
        self.is_valid = is_valid
        self.errors = errors


MOCK_GET_VALIDATOR_DATA = {
    "rule_1": {
        "name": "Rule #1",
        "description": "This is the first test rule.",
        "error_msg": "This is the error message",
        "dependency_ids": ["rule_2", "rule_3", "omit_rule"],
        "check_func": lambda: CheckResult(True),
    },
    "rule_2": {
        "name": "Rule #2",
        "description": "This is the second test rule.",
        "dependency_ids": ["rule_3"],
        "check_func": lambda: CheckResult(False),
    },
    "rule_3": {
        "name": "Rule #3",
    },
    "omit_rule": {
        "name": "This rule will not be excluded by not including it in the config.",
    },
}


@pytest.fixture
def notifier():
    """
    A mock Application object to use to create the ValidationManager object. Note that
    the mock Application does not provide the full functionality of the actual class
    it represents; any additional functionality required must be added here.
    """

    class MockValidateAllBeginSignal:
        emit = MagicMock()

    class MockValidateAllFinishedSignal:
        emit = MagicMock()

    class MockValidateRuleBeginSignal:
        emit = MagicMock()

    class MockValidateRuleFinishedSignal:
        emit = MagicMock()

    class MockResolveAllBeginSignal:
        emit = MagicMock()

    class MockResolveAllFinishedSignal:
        emit = MagicMock()

    class MockResolveRuleBeginSignal:
        emit = MagicMock()

    class MockResolveRuleFinishedSignal:
        emit = MagicMock()

    # Set up the mock notifier
    mock_notifier = MagicMock()
    mock_notifier.validate_all_begin = MockValidateAllBeginSignal()
    mock_notifier.validate_all_finished = MockValidateAllFinishedSignal()
    mock_notifier.validate_rule_begin = MockValidateRuleBeginSignal()
    mock_notifier.validate_rule_finished = MockValidateRuleFinishedSignal()
    mock_notifier.resolve_all_begin = MockResolveAllBeginSignal()
    mock_notifier.resolve_all_finished = MockResolveAllFinishedSignal()
    mock_notifier.resolve_rule_begin = MockResolveRuleBeginSignal()
    mock_notifier.resolve_rule_finished = MockResolveRuleFinishedSignal()

    return mock_notifier


@pytest.fixture(scope="module")
def bundle_hook_data_validator_return_value():
    """
    The return value for the ValidationManager's class variable '_bundle' method
    call 'execute_hook_method("hook_scene_operation", "scan_scene")'.
    """

    return MOCK_GET_VALIDATOR_DATA


@pytest.fixture(scope="module")
def bundle_settings():
    """
    The settings for the ValidationManager class variable '_bundle'.
    """

    return {
        "rules": [
            {"id": "rule_1"},
            {"id": "rule_2", "required": False},
            {"id": "rule_3", "data_type": "Test Data"},
        ],
    }


@pytest.fixture(scope="module")
def bundle_hook_methods(bundle_hook_data_validator_return_value):
    """
    A mapping of hooks and their return value for the ValidationManager's class
    variable '_bundle'. The return values do not necessarily match real production
    data, this is meant to be used to ensure the ValidationManager can execute its
    methods without erring on hooks not found.
    """

    return {
        "hook_data_validator": {
            "get_validation_data": bundle_hook_data_validator_return_value
        },
    }


@pytest.fixture
def bundle(bundle_settings, bundle_hook_methods):
    """
    A mock Application object to use to create the ValidationManager object. Note that
    the mock Application does not provide the full functionality of the actual class
    it represents; any additional functionality required must be added here.
    """

    def mock_app_get_setting(name, default_value=None):
        """
        Mock the Application method 'get_settings'
        """
        return bundle_settings.get(name, default_value)

    def mock_app_execute_hook_method(hook_name, hook_method, **kwargs):
        """
        Mock the Application method 'execute_hook_method'.
        """
        return bundle_hook_methods.get(hook_name, {}).get(hook_method, None)

    # Set up the mock Application
    app = MagicMock()
    app.get_setting = mock_app_get_setting
    app.execute_hook_method = mock_app_execute_hook_method
    app.logger = Logger()

    return app


@pytest.fixture
def manager(bundle, notifier):
    """
    Fixture to return a ValidationManager.
    """

    return ValidationManager(bundle, notifier=notifier)


#########################################################################################################
# ValidationManager pytests
#########################################################################################################
#
# The purpose of set of tests below are to validate the ValidationManager class functionality.
# They are light-weight tests that do not use any other Toolkit functionality (e.g. sgtk,
# Application, Engine, etc.), and strictly focus on testing the ValidationManager class.
# These tests are not a subclass of TankTestBase (unittest.TestCase) so that we can
# leverage pytest's functionality, like parametrize and fixtures.
#
#########################################################################################################


def test_manager_init_does_not_modify_hook_data(
    bundle, bundle_hook_data_validator_return_value
):
    """
    Test the ValidationManager init does not modify the hook data used to create the rules.
    """

    saved_data = copy.deepcopy(bundle_hook_data_validator_return_value)

    manager = ValidationManager(bundle=bundle)

    assert saved_data == bundle_hook_data_validator_return_value


def test_manager_init_defaults(bundle, bundle_settings):
    """
    Test the ValidationManager constructor with the default params (except for the bundle
    that we need to pass in).
    """

    manager = ValidationManager(bundle)

    assert manager._bundle is bundle
    assert manager._logger is bundle.logger
    assert manager.notifier is None
    assert not manager.has_ui
    assert manager.accept_rule_fn is None
    assert not manager.errors

    # Check the rules created from the bundle settings
    rules = bundle_settings.get("rules", [])
    assert len(manager.rules) == len(rules)
    for rule in rules:
        found_rule = manager.get_rule(rule["id"])
        assert found_rule

        required = rule.get("required", True)
        assert found_rule.required == required

        assert found_rule.data_type == rule.get("data_type")


@pytest.mark.parametrize(
    "notifier",
    [
        None,
        Notifier,
    ],
)
def test_manager_init_with_notifier(bundle, notifier):
    """
    Test the ValidationManager constructor with the notifier param.
    """

    manager = ValidationManager(bundle=bundle, notifier=notifier)

    assert manager.notifier is notifier


@pytest.mark.parametrize(
    "has_ui",
    [
        True,
        False,
    ],
)
def test_manager_init_with_has_ui(bundle, has_ui):
    """
    Test the ValidationManager constructor with the has_ui param.
    """

    manager = ValidationManager(bundle=bundle, has_ui=has_ui)

    assert manager.has_ui == has_ui


@pytest.mark.parametrize(
    "include_rules",
    [
        None,
        [],
        ["rule_1"],
        ["rule_1", "rule_3"],
        ["rule_1", "rule_2", "rule_3"],
        ["rule_1", "rule_3", "omit_rule"],
    ],
)
def test_manager_init_with_include_rules(bundle, bundle_settings, include_rules):
    """
    Test the ValidationManager constructor with the has_ui param.
    """

    manager = ValidationManager(bundle=bundle, include_rules=include_rules)

    settings_rules = bundle_settings.get("rules", [])

    if not include_rules:
        # All rules from the settings should be in the manager
        expected_rules = settings_rules
    else:
        # Only the (valid) rules specified should be in the manager
        expected_rules = [r for r in settings_rules if r["id"] in include_rules]

    assert len(manager.rules) == len(expected_rules)
    for rule in expected_rules:
        assert manager.get_rule(rule["id"])


@pytest.mark.parametrize(
    "exclude_rules",
    [
        None,
        [],
        ["rule_1"],
        ["rule_1", "rule_3"],
        ["rule_1", "rule_2", "rule_3"],
        ["rule_1", "rule_3", "omit_rule"],
    ],
)
def test_manager_init_with_exclude_rules(bundle, bundle_settings, exclude_rules):
    """
    Test the ValidationManager constructor with the exclude_rules param.
    """

    manager = ValidationManager(bundle=bundle, exclude_rules=exclude_rules)

    settings_rules = bundle_settings.get("rules", [])

    if not exclude_rules:
        # All rules from the settings should be in the manager
        expected_rules = settings_rules
    else:
        # Only the (valid) rules specified should be in the manager
        expected_rules = [r for r in settings_rules if r["id"] not in exclude_rules]

    assert len(manager.rules) == len(expected_rules)
    for rule in expected_rules:
        assert manager.get_rule(rule["id"])


@pytest.mark.parametrize(
    "include_rules",
    [
        None,
        [],
        ["rule_1"],
        ["rule_1", "rule_3"],
        ["rule_1", "rule_2", "rule_3"],
        ["rule_1", "rule_3", "omit_rule"],
    ],
)
@pytest.mark.parametrize(
    "exclude_rules",
    [
        None,
        [],
        ["rule_1"],
        ["rule_1", "rule_3"],
        ["rule_1", "rule_2", "rule_3"],
        ["rule_1", "rule_3", "omit_rule"],
    ],
)
def test_manager_init_with_include_and_exclude_rules(
    bundle, bundle_settings, include_rules, exclude_rules
):
    """
    Test the ValidationManager constructor with the include_rules and exclude_rules param.
    """

    manager = ValidationManager(
        bundle=bundle, include_rules=include_rules, exclude_rules=exclude_rules
    )

    settings_rules = bundle_settings.get("rules", [])
    expected_rules = []
    for rule in settings_rules:
        if exclude_rules and rule["id"] in exclude_rules:
            # Rule should be excluded
            # Exclude takes precedence over include
            continue

        if include_rules and rule["id"] not in include_rules:
            # Rule is not to be included
            continue

        # Rule is accepted, add it to the expected list
        expected_rules.append(rule)

    assert len(manager.rules) == len(expected_rules)
    for rule in expected_rules:
        assert manager.get_rule(rule["id"])


@pytest.mark.parametrize(
    "rule_settings",
    [
        None,
        [],
        [{"id": "rule_does_not_exist"}],
        [{"id": "rule_1"}],
        [{"id": "rule_1"}, {"id": "rule_2"}],
        [{"id": "rule_1"}, {"id": "rule_2"}, {"id": "rule_3"}],
        [{"id": "rule_does_not_exist"}, {"id": "rule_1"}],
    ],
)
def test_manager_init_with_rule_settings(
    bundle, bundle_settings, bundle_hook_data_validator_return_value, rule_settings
):
    """
    Test the ValidationManager constructor with the rule_settings param.
    """

    # Rule id must exist in the value returned by the hook method, else it won't be added to the manager
    manager = ValidationManager(bundle=bundle, rule_settings=rule_settings)

    if not rule_settings:
        expected_rules = bundle_settings.get("rules", [])
    else:
        rule_ids = bundle_hook_data_validator_return_value.keys()
        expected_rules = [r for r in rule_settings if r["id"] in rule_ids]

    assert len(manager.rules) == len(expected_rules)
    for rule in expected_rules:
        assert manager.get_rule(rule["id"])


def test_manager_create_dependencies(
    manager, bundle_settings, bundle_hook_data_validator_return_value
):
    """
    Test the ValidationManager constructor creates the Validation Rules correctly.
    """

    rules = bundle_settings.get("rules", [])

    for rule in rules:
        if rule["id"] not in bundle_hook_data_validator_return_value:
            continue

        # Get the list of dependency ids from the rule data that will create the ValidationRule object
        rule_data = bundle_hook_data_validator_return_value[rule["id"]]
        dependency_ids = rule_data.get("dependency_ids", [])

        # Ensure we can find the ValidationRule object
        found_rule = manager.get_rule(rule["id"])
        assert found_rule

        # Go through each expected dependency and assert that it is added to the ValidationRule object
        for dep_id in dependency_ids:
            found_dep = manager.get_rule(dep_id)
            if not found_dep:
                continue

            assert found_dep.id in found_rule.dependencies
            assert found_rule.dependencies[found_dep.id] == found_dep.name


def test_manager_reset(manager):
    """
    Test the ValidationManager reset method.
    """

    manager.reset()
    assert manager.errors == {}


def test_manager_validate(bundle):
    """
    Test the ValidationManager validate method.
    """

    manager = ValidationManager(bundle, notifier=None)
    manager.accept_rule_fn = None

    success = manager.validate()
    assert not success

    # Based on the hook data, there should be 2 errors.
    # 1. rule_2 explicitly returns not valid
    # 2. rule_3 does not have a check function (which makes it manual) and is not manually "checked"
    assert len(manager.errors) == 2
    assert "rule_2" in manager.errors
    assert "rule_3" in manager.errors


def test_manager_validate_with_accept_fn(bundle):
    """
    Test the ValidationManager validate method.
    """

    manager = ValidationManager(bundle, notifier=None)
    manager.accept_rule_fn = lambda r: r.check_func is not None

    success = manager.validate()
    assert not success

    # Based on the hook data and accept function, there should be only 1 error.
    # 1. rule_2 explicitly returns not valid
    # Note that rule_3 is ignored by the accept_rule_fn
    assert len(manager.errors) == 1
    assert "rule_2" in manager.errors


def test_manager_validate_successfully(bundle):
    """
    Test the ValidationManager validate method.
    """

    manager = ValidationManager(bundle, notifier=None)
    manager.accept_rule_fn = lambda r: r.id == "rule_1"

    success = manager.validate()
    assert success
    assert not manager.errors


def test_manager_validate_notifier_signals(bundle, notifier):
    """
    Test the ValidationManager validate method.
    """

    manager = ValidationManager(bundle, notifier=notifier)
    manager.validate()

    manager.notifier.validate_all_begin.emit.assert_called_once()
    manager.notifier.validate_all_finished.emit.assert_called_once()

    expected_calls = [call(r) for r in manager.rules]
    manager.notifier.validate_rule_begin.emit.assert_has_calls(
        expected_calls, any_order=True
    )
    manager.notifier.validate_rule_finished.emit.assert_has_calls(
        expected_calls, any_order=True
    )


def test_manager_resolve_notifier_signals(bundle, notifier):
    """
    Test the ValidationManager validate method.
    """

    manager = ValidationManager(bundle, notifier=notifier)
    manager.accept_rule_fn = None

    manager.validate()
    expected_calls = [call(r) for r in manager.rules if not r.valid]

    manager.resolve()

    manager.notifier.resolve_all_begin.emit.assert_called_once()
    manager.notifier.resolve_all_finished.emit.assert_called_once()

    manager.notifier.resolve_rule_begin.emit.assert_has_calls(
        expected_calls, any_order=True
    )
    manager.notifier.resolve_rule_finished.emit.assert_has_calls(
        expected_calls, any_order=True
    )


def test_manager_resolve_with_pre_validate_notifier_signals(bundle, notifier):
    """
    Test the ValidationManager validate method.
    """

    manager = ValidationManager(bundle, notifier=notifier)

    manager.resolve(pre_validate=True)

    manager.notifier.validate_all_begin.emit.assert_called_once()
    manager.notifier.validate_all_finished.emit.assert_called_once()

    expected_calls = [call(r) for r in manager.rules]
    manager.notifier.validate_rule_begin.emit.assert_has_calls(
        expected_calls, any_order=True
    )
    manager.notifier.validate_rule_finished.emit.assert_has_calls(
        expected_calls, any_order=True
    )
