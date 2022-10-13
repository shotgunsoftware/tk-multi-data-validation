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
import os
import sys

import pytest
import mock
from mock import call, MagicMock

# Manually add the app modules to the path in order to import them here.
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python"))
app_dir = os.path.abspath(os.path.join(base_dir, "tk_multi_data_validation"))
api_dir = os.path.abspath(os.path.join(app_dir, "api"))
data_dir = os.path.abspath(os.path.join(api_dir, "data"))
sys.path.extend([base_dir, app_dir, api_dir, data_dir])
from tk_multi_data_validation.api import ValidationManager
from tk_multi_data_validation.api.data import ValidationRule


RULE_IDS = [
    "rule_1",
    "rule_2",
    "rule_3",
    "rule_4",
]
DEPENDENCY_RULE_IDS = [
    "dep_1",
    "dep_2",
    "dep_3",
    "dep_4",
    "dep_5",
    "dep_6",
    "dep_7",
]
BAD_DEPENDENCY_RULE_IDS = [
    "bad_dep_1",
    "bad_dep_2",
    "bad_dep_3",
    "bad_dep_4",
]

#########################################################################################################
# Helper classes


class Notifier(object):
    """Mock notifier object for testing the ValidationManager."""


#########################################################################################################
# Fixtures and mock data for ValidationManager pytests


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


@pytest.fixture
def manager(bundle, notifier):
    """Fixture to return a ValidationManager."""

    return ValidationManager(bundle, notifier=notifier, include_rules=RULE_IDS)


@pytest.fixture
def manager_with_dependencies(bundle, notifier):
    """Fixture to return a ValidationManager with rules that have dependencies."""

    return ValidationManager(
        bundle, notifier=notifier, include_rules=DEPENDENCY_RULE_IDS
    )


@pytest.fixture
def manager_with_dependency_cycle(bundle, notifier):
    """Fixture to return a ValidationManager with rules that have a dependency cycle."""

    return ValidationManager(
        bundle, notifier=notifier, include_rules=BAD_DEPENDENCY_RULE_IDS
    )


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


def test_manager_init_updates_validation_data(
    bundle, bundle_settings, mock_get_validation_data
):
    """
    Test the ValidationManager init updates the data passed from the hook.
    """

    data = copy.deepcopy(mock_get_validation_data)

    manager = ValidationManager(bundle=bundle)

    if "dependency_ids" in data:
        assert "dependencies" in data

    for rule in bundle_settings.get("rules", []):
        assert rule["id"] in data


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
    bundle, bundle_settings, mock_get_validation_data, rule_settings
):
    """
    Test the ValidationManager constructor with the rule_settings param.
    """

    # Rule id must exist in the value returned by the hook method, else it won't be added to the manager
    manager = ValidationManager(bundle=bundle, rule_settings=rule_settings)

    if not rule_settings:
        expected_rules = bundle_settings.get("rules", [])
    else:
        rule_ids = mock_get_validation_data.keys()
        expected_rules = [r for r in rule_settings if r["id"] in rule_ids]

    assert len(manager.rules) == len(expected_rules)
    for rule in expected_rules:
        assert manager.get_rule(rule["id"])


def test_manager_create_dependencies(
    manager_with_dependencies, mock_get_validation_data
):
    """
    Test the ValidationManager constructor creates the Validation Rules correctly.
    """

    for rule in manager_with_dependencies.rules:
        if rule.id not in mock_get_validation_data:
            continue

        # Get the list of dependency ids from the rule data that will create the ValidationRule object
        rule_data = mock_get_validation_data[rule.id]
        dependency_ids = rule_data.get("dependency_ids", [])

        # Ensure we can find the ValidationRule object
        found_rule = manager_with_dependencies.get_rule(rule.id)
        assert found_rule

        # Go through each expected dependency and assert that it is added to the ValidationRule object
        for dep_id in dependency_ids:
            found_dep = manager_with_dependencies.get_rule(dep_id)
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


def test_manager_validate_notifier_signals(manager):
    """
    Test the ValidationManager validate method.
    """

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


def test_manager_resolve_notifier_signals(manager):
    """
    Test the ValidationManager validate method.
    """

    manager.accept_rule_fn = None

    manager.validate()
    expected_calls = [call(r) for r in manager.rules if not r.valid]

    manager.resolve(retry_until_success=False)

    manager.notifier.resolve_all_begin.emit.assert_called_once()
    manager.notifier.resolve_all_finished.emit.assert_called_once()

    manager.notifier.resolve_rule_begin.emit.assert_has_calls(
        expected_calls, any_order=True
    )
    manager.notifier.resolve_rule_finished.emit.assert_has_calls(
        expected_calls, any_order=True
    )


def test_manager_resolve_with_pre_validate_notifier_signals(manager):
    """Test the ValidationManager validate method."""

    manager.resolve(pre_validate=True, retry_until_success=False)

    manager.notifier.resolve_all_begin.emit.assert_called_once()
    manager.notifier.resolve_all_finished.emit.assert_called_once()

    assert not manager.notifier.validate_rule_begin.emit.assert_not_called()
    assert not manager.notifier.validate_rule_finsihed.emit.assert_not_called()
    assert not manager.notifier.validate_all_begin.emit.assert_not_called()
    assert not manager.notifier.validate_all_finsihed.emit.assert_not_called()
    expected_calls = [call(r) for r in manager.rules]
    manager.notifier.resolve_rule_begin.emit.assert_has_calls(
        expected_calls, any_order=True
    )
    manager.notifier.resolve_rule_finished.emit.assert_has_calls(
        expected_calls, any_order=True
    )


def test_manager_validate(manager):
    """
    Test the ValidationManager validate method.

    The validation data used is mocked through the bundle (see conftest.py).
    """

    manager.accept_rule_fn = None

    success = manager.validate()
    assert not success

    # Based on the hook data, there should be 2 errors.
    # 1. rule_2 explicitly returns not valid using a object result
    # 2. rule_3 does not have a check function (which makes it manual) and is not manually "checked"
    # 3. rule_4 explicitly returns not valid using a dict result
    assert "rule_2" in manager.errors
    assert "rule_3" in manager.errors
    assert "rule_4" in manager.errors
    assert len(manager.errors) == 3


def test_manager_validate_with_accept_fn(manager):
    """
    Test the ValidationManager validate method with the accept_fn defined.

    The validation data used is mocked through the bundle (see conftest.py).
    """

    manager.accept_rule_fn = lambda r: r.check_func is not None

    success = manager.validate()
    assert not success

    # Based on the hook data and accept function, there should be only 1 error.
    # 1. rule_2 explicitly returns not valid using object result
    # 2. rule_4 explicitly returns not valid using dict result
    # Note that rule_3 is ignored by the accept_rule_fn
    assert "rule_2" in manager.errors
    assert "rule_4" in manager.errors
    assert len(manager.errors) == 2


def test_manager_validate_successfully(manager):
    """
    Test the ValidationManager validate method.

    The validation data used is mocked through the bundle (see conftest.py).
    """

    manager.accept_rule_fn = lambda r: r.id == "rule_1"

    success = manager.validate()
    assert success
    assert not manager.errors


def test_manager_validate_with_dependencies(manager_with_dependencies):
    """
    Test the ValidationManager validate_rules method.

    Ignore the ValidationManager rules, and pass in our own specific set for testing.
    """

    success = manager_with_dependencies.validate()
    assert not success

    assert "dep_1" in manager_with_dependencies.errors
    assert "dep_2" in manager_with_dependencies.errors
    assert "dep_3" in manager_with_dependencies.errors
    assert "dep_6" in manager_with_dependencies.errors
    assert "dep_7" in manager_with_dependencies.errors
    assert len(manager_with_dependencies.errors) == 5

    dep_1 = manager_with_dependencies.get_rule("dep_1")
    assert dep_1.valid is False
    assert not dep_1.has_failed_dependency()

    dep_2 = manager_with_dependencies.get_rule("dep_2")
    assert dep_2.valid is None
    assert dep_2.has_failed_dependency()

    dep_3 = manager_with_dependencies.get_rule("dep_3")
    assert dep_3.valid is None
    assert dep_3.has_failed_dependency()

    dep_4 = manager_with_dependencies.get_rule("dep_4")
    assert dep_4.valid is True
    assert not dep_4.has_failed_dependency()

    dep_5 = manager_with_dependencies.get_rule("dep_5")
    assert dep_5.valid is True
    assert not dep_5.has_failed_dependency()

    dep_6 = manager_with_dependencies.get_rule("dep_6")
    assert dep_6.valid is None
    assert dep_6.has_failed_dependency()

    dep_7 = manager_with_dependencies.get_rule("dep_7")
    assert dep_7.valid is None
    assert dep_7.has_failed_dependency()


def test_manager_validate_rules_and_ignore_dependencies(manager_with_dependencies):
    """
    Test the ValidationManager validate_rules with dependencies.

    Ignore the ValidationManager rules, and pass in our own specific set for testing.
    """

    dep_1 = manager_with_dependencies.get_rule("dep_1")
    dep_2 = manager_with_dependencies.get_rule("dep_2")
    dep_3 = manager_with_dependencies.get_rule("dep_3")
    dep_5 = manager_with_dependencies.get_rule("dep_5")
    dep_7 = manager_with_dependencies.get_rule("dep_7")

    rules = [dep_2, dep_3, dep_5, dep_7]
    manager_with_dependencies.validate_rules(rules)

    assert "dep_1" in manager_with_dependencies.errors
    assert "dep_2" in manager_with_dependencies.errors
    assert "dep_3" in manager_with_dependencies.errors
    assert "dep_7" in manager_with_dependencies.errors
    assert len(manager_with_dependencies.errors) == 4

    assert dep_1.valid is False
    assert dep_5.valid is True

    assert dep_2.valid is None
    assert dep_3.valid is None
    assert dep_7.valid is None

    assert dep_2.has_failed_dependency()
    assert dep_3.has_failed_dependency()
    assert dep_7.has_failed_dependency()

    # Now do not fetch dependencies - ignore dep_1
    manager_with_dependencies.reset()
    manager_with_dependencies.validate_rules(rules, fetch_dependencies=False)

    assert dep_7.id in manager_with_dependencies.errors
    assert len(manager_with_dependencies.errors) == 1

    assert dep_2.valid is True
    assert dep_3.valid is True
    assert dep_5.valid is True
    assert dep_7.valid is False

    assert not dep_2.has_failed_dependency()
    assert not dep_3.has_failed_dependency()
    assert not dep_7.has_failed_dependency()


@pytest.mark.skipif(sys.version_info.major < 3, reason="requires python 3 or higher")
def test_manager_validate_detect_dependency_cycle(manager_with_dependency_cycle):
    """
    Test the validate method to catch if there is a dependency cycle.
    """

    with pytest.raises(RecursionError):
        manager_with_dependency_cycle.validate()

    dep_1 = manager_with_dependency_cycle.get_rule("bad_dep_1")
    dep_2 = manager_with_dependency_cycle.get_rule("bad_dep_2")
    dep_3 = manager_with_dependency_cycle.get_rule("bad_dep_3")
    rules = [dep_1, dep_2, dep_3]

    with pytest.raises(RecursionError):
        manager_with_dependency_cycle.validate_rules(rules)

    # OK if the cyclic dependency not included
    rules = [dep_2, dep_3]
    manager_with_dependency_cycle.validate_rules(rules, fetch_dependencies=False)


@pytest.mark.skipif(sys.version_info.major < 3, reason="requires python 3 or higher")
def test_manager_resolve_detect_dependency_cycle(manager_with_dependency_cycle):
    """
    Test the resolve method to catch if there is a dependency cycle.
    """

    with pytest.raises(RecursionError):
        manager_with_dependency_cycle.resolve(pre_validate=True)

    with pytest.raises(RecursionError):
        manager_with_dependency_cycle.resolve(pre_validate=False)

    dep_1 = manager_with_dependency_cycle.get_rule("bad_dep_1")
    dep_1 = manager_with_dependency_cycle.get_rule("bad_dep_1")
    dep_2 = manager_with_dependency_cycle.get_rule("bad_dep_2")
    dep_3 = manager_with_dependency_cycle.get_rule("bad_dep_3")
    rules = [dep_1, dep_2, dep_3]

    with pytest.raises(RecursionError):
        manager_with_dependency_cycle.resolve_rules(rules)

    # OK if the cyclic dependency not included
    rules = [dep_2, dep_3]
    manager_with_dependency_cycle.resolve_rules(rules, fetch_dependencies=False)


def test_manager_resolve(bundle):
    """
    Test the resolve method.

    This test function does not test if the data was resolved, it only checks that the fix
    functions for each rule was called.
    """

    manager = ValidationManager(bundle=bundle, include_rules=RULE_IDS)

    # Hack the rules' fix function to track the call count
    for rule in manager.rules:
        rule._data["fix_func"] = MagicMock()

    manager.resolve(pre_validate=False, retry_until_success=False)
    for rule in manager.rules:
        rule.fix_func.assert_called_once()

    # Now check that the fix was called multiple times since we will retry until success
    # The check functions will continue to return False since they are static, so the fix
    # will never "succeed"
    manager.resolve(pre_validate=False, retry_until_success=True)
    for rule in manager.rules:
        if rule.valid:
            # If the rule is valid, we called the fix once before and once now (for total 2 times)
            assert rule.fix_func.call_count == 2
        else:
            # IF the rule is not valid, the manager will have tried multiple times (over 2)
            assert rule.fix_func.call_count > 2


def test_manager_resolve_pre_validate(bundle):
    """Test the resolve method."""

    manager = ValidationManager(bundle=bundle, include_rules=RULE_IDS)

    # Hack the rules' fix function to track the call count
    for rule in manager.rules:
        rule._data["check_func"] = MagicMock()

    manager.resolve(pre_validate=False, post_validate=False, retry_until_success=False)
    for rule in manager.rules:
        rule.check_func.assert_not_called()

    manager.resolve(pre_validate=True, post_validate=False, retry_until_success=False)
    for rule in manager.rules:
        rule.check_func.assert_called_once()


def test_manager_resolve_post_validate(bundle):
    """Test the resolve method."""

    manager = ValidationManager(bundle=bundle, include_rules=RULE_IDS)

    # Hack the rules' fix function to track the call count
    for rule in manager.rules:
        rule._data["check_func"] = MagicMock()

    manager.resolve(pre_validate=False, post_validate=False, retry_until_success=False)
    for rule in manager.rules:
        rule.check_func.assert_not_called()

    manager.resolve(pre_validate=False, post_validate=True, retry_until_success=False)
    for rule in manager.rules:
        rule.check_func.assert_called_once()
