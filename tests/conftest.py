import pytest
from mock import MagicMock

#########################################################################################################
# Helper classes & functions


class Logger(object):
    """Mock logger object for testing."""

    def debug(self, msg):
        pass

    def error(self, msg):
        pass

    def warning(self, msg):
        pass


class CheckResult(object):
    """Mock object for passing check function result for testing."""

    def __init__(self, is_valid, errors=None):
        self.is_valid = is_valid
        self.errors = errors


class MockHookDataValidationClass(object):
    """Mock the hook data validation class."""

    def get_validation_data(self):
        return mock_get_validation_data()

    def sanitize_check_result(self, result):
        return mock_sanitize_check_result(result)


def mock_sanitize_check_result(result):
    """Mock the hook method to sanitize check results."""

    # Just return the result as is.
    return result


#########################################################################################################
# Global fixtures


@pytest.fixture(scope="module")
def mock_get_validation_data():
    """
    The return value for the ValidationManager's class variable '_bundle' method
    call 'execute_hook_method("hook_data_validation", "get_validation_data")'.
    """

    return {
        "rule_1": {
            "name": "Rule #1",
            "check_func": lambda: CheckResult(True),
        },
        "rule_2": {
            "name": "Rule #2",
            "check_func": lambda: CheckResult(False),
        },
        "rule_3": {
            "name": "Rule #3",
        },
        "rule_4": {
            "name": "Rule #4",
            "check_func": lambda: {"is_valid": False, "errors": None},
        },
        "omit_rule": {
            "name": "This rule will not be excluded by not including it in the config.",
        },
        "dep_1": {
            "name": "Dependency #1",
            "check_func": lambda: {"is_valid": False, "errors": None},
        },
        "dep_2": {
            "name": "Dependency #2",
            "check_func": lambda: {"is_valid": True, "errors": None},
            "dependency_ids": [
                "dep_1",
            ],
        },
        "dep_3": {
            "name": "Dependency #3",
            "check_func": lambda: {"is_valid": True, "errors": None},
            "dependency_ids": [
                "dep_2",
            ],
        },
        "dep_4": {
            "name": "Dependency #4",
            "check_func": lambda: {"is_valid": True, "errors": None},
        },
        "dep_5": {
            "name": "Dependency #5",
            "check_func": lambda: {"is_valid": True, "errors": None},
            "dependency_ids": [
                "dep_4",
            ],
        },
        "dep_6": {
            "name": "Dependency #6",
            "check_func": lambda: {"is_valid": True, "errors": None},
            "dependency_ids": ["dep_5", "dep_3"],
        },
        "dep_7": {
            "name": "Dependency #7",
            "check_func": lambda: {"is_valid": False, "errors": None},
            "dependency_ids": [
                "dep_1",
            ],
        },
        "bad_dep_1": {
            "name": "Introduce a dependency cycle - exclude me unless testing for cycles.",
            "check_func": lambda: {"is_valid": True, "errors": None},
            "dependency_ids": [
                "bad_dep_3",
            ],
        },
        "bad_dep_2": {
            "name": "Depend on the first bad dep.",
            "check_func": lambda: {"is_valid": True, "errors": None},
            "dependency_ids": [
                "bad_dep_1",
            ],
        },
        "bad_dep_3": {
            "name": "Depend on the second bad dep.",
            "check_func": lambda: {"is_valid": True, "errors": None},
            "dependency_ids": [
                "bad_dep_2",
            ],
        },
        "bad_dep_4": {
            "name": "I'm not bad!",
            "check_func": lambda: {"is_valid": True, "errors": None},
        },
    }


@pytest.fixture(scope="module")
def bundle_hook_methods(mock_get_validation_data):
    """
    A mapping of hooks and their return value for the ValidationManager's class
    variable '_bundle'. The return values do not necessarily match real production
    data, this is meant to be used to ensure the ValidationManager can execute its
    methods without erring on hooks not found.
    """

    return {
        "hook_data_validation": {
            "get_validation_data": mock_get_validation_data,
            "sanitize_check_result": mock_sanitize_check_result,
        },
    }


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
            {"id": "rule_4", "data_type": "Test Data"},
            {"id": "dep_1", "data_type": "Dependency"},
            {"id": "dep_2", "data_type": "Dependency"},
            {"id": "dep_3", "data_type": "Dependency"},
            {"id": "dep_4", "data_type": "Dependency"},
            {"id": "dep_5", "data_type": "Dependency"},
            {"id": "dep_6", "data_type": "Dependency"},
            {"id": "dep_7", "data_type": "Dependency"},
            {"id": "bad_dep_1", "data_type": "Bad Dependency"},
            {"id": "bad_dep_2", "data_type": "Bad Dependency"},
            {"id": "bad_dep_3", "data_type": "Bad Dependency"},
            {"id": "bad_dep_4", "data_type": "Bad Dependency"},
        ],
        "hook_data_validation": "hook_data_validation",
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

    def mock_app_create_hook_instance(hook_path):
        """
        Mock the Application method 'execute_hook_method'.
        """

        if hook_path == "hook_data_validation":
            return MockHookDataValidationClass()

        raise ValueError("Failed to create hook instance for {}".format(hook_path))

    # Set up the mock Application
    app = MagicMock()
    app.get_setting = mock_app_get_setting
    app.execute_hook_method = mock_app_execute_hook_method
    app.create_hook_instance = mock_app_create_hook_instance
    app.logger = Logger()

    return app
