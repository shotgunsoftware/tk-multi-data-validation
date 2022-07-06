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
import pytest

from app_test_base import AppTestBase
from tank_test.tank_test_base import setUpModule  # noqa


class TestApplication(AppTestBase):
    """
    Test the Data Validation Application class methods. Note that
    this test module is a subclass of TankTestBase, which makes it
    a unittest.TestCase, which means we cannot use some pytest
    functionality, like parametrization and pytest fixtures.
    """

    def setUp(self):
        """
        Set up before any tests are executed.
        """

        os.environ["TEST_ENVIRONMENT"] = "test"
        super(TestApplication, self).setUp()

    def test_init_app(self):
        """
        Test initializing the application.
        """

        assert self.app is not None
        assert self.app._manager_class is not None
        assert self.engine is not None

        # Ensure that the engine has the app command registered with
        # the correct properties
        app_cmd = self.engine.commands.get("Data Validation...", None)
        assert app_cmd is not None
        cmd_props = app_cmd.get("properties", None)
        assert cmd_props is not None
        assert cmd_props.get("short_name", "") == "data_validation"

    def test_create_validation_manager(self):
        """
        Test creating and returning a :class:`tk_multi_data_validation.ValidationManager` instance.
        """

        manager = self.app.create_validation_manager()
        assert manager is not None
        assert manager._bundle == self.app
