# Copyright (c) 2022 Autodesk Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk Software Inc.

import os
import sys

import sgtk
from tank_test.tank_test_base import TankTestBase


class AppTestBase(TankTestBase):
    """
    Base class for data validation API functionality.
    """

    def setUp(self):
        """
        Set up before any tests are executed.
        """

        # First call the parent TankTestBase constructor to set up the tests base
        super(AppTestBase, self).setUp()
        self.setup_fixtures()

        # Set up the python path to import required modules
        base_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "python",
            )
        )
        app_dir = os.path.abspath(os.path.join(base_dir, "tk_multi_data_validation"))
        api_dir = os.path.abspath(os.path.join(app_dir, "api"))
        sys.path.extend([base_dir, app_dir, api_dir])

        from tk_multi_data_validation.api import ValidationManager

        self._manager_class = ValidationManager
        self._app = None
        self._engine = None
        self._manager = None
        self.project_name = os.path.basename(self.project_root)
        context = self.tk.context_from_entity(self.project["type"], self.project["id"])

        # Full App test environment
        engine_name = os.environ.get("TEST_ENGINE", "tk-testengine")
        self._engine = sgtk.platform.start_engine(engine_name, self.tk, context)
        self._app = self._engine.apps["tk-multi-data-validation"]

    def tearDown(self):
        """
        Clean up after all tests have been executed.
        """

        if self.engine:
            self.engine.destroy()

        super(AppTestBase, self).tearDown()

    @property
    def engine(self):
        """
        The engine running the Breadkwon2 Application.
        """

        return self._engine

    @property
    def app(self):
        """
        The Data Validation Application.
        """

        return self._app

    @property
    def manager(self):
        """
        The Data Validation Manager object.
        """

        if not self._manager:
            if self.app:
                self._manager = self._app.create_validation_manager()
            elif self._manager_class:
                self._manager = self._manager_class(self.app)

        return self._manager

    def create_manager(self):
        """
        Convenience method to create a new Data Validation Manager object.
        """

        if self.app:
            return self._app.create_validation_manager()

        if self._manager_class:
            return self._manager_class(self.app)

        return None
