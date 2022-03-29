# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import sgtk


class DataValidation(sgtk.platform.Application):
    """
    This is the :class:`sgtk.platform.Application` subclass that defines the
    top-level data validation App interface.
    """

    def init_app(self):
        """
        Called as the application is being initialized
        """

        tk_multi_data_validation = self.import_module("tk_multi_data_validation")

        # the manager class provides the interface for validatin. We store a reference to it to enable the
        # create_validation_manager method exposed on the application itself
        self._manager_class = tk_multi_data_validation.ValidationManager
        self._widget_class = tk_multi_data_validation.ValidationWidget

        cb = lambda: tk_multi_data_validation.show_dialog(self)
        self.engine.register_command(
            "Scene Data Validation...", cb, {"short_name": "data_validation"}
        )

    def show_dialog(self, modal=False):
        """
        Show the Data Validation App dialog.

        :param modal: Open the dialog in modal mode.
        :type modal: True to open the dialog in modal, else non-modal.
        """

        tk_multi_data_validation = self.import_module("tk_multi_data_validation")
        tk_multi_data_validation.show_dialog(self, modal)

    def create_validation_widget(self, parent, validation_manager=None):
        """
        Create a validation widget instance.

        :param parent: The parent widget
        :type parent: QtGui.QWidget
        :param validation_manager: (optional) The ValidationManager to faciliate validating and fixing the
            data violations.
        :type validation_manager: ValidationManager
        """

        return self._widget_class(parent, validation_manager=validation_manager)

    def create_validation_manager(
        self, rule_settings=None, include_rules=None, exclude_rules=None,
    ):
        """
        Create a validation manager instance.

        :param rule_settings: The settings data containing the validation rules
        :type rule_settings: list<dict>
        :param include_rules: The validation rule ids to use from the settings
        :type include_rules: list<str>
        :param exclude_rules: The validation rule ids to not use from the settings
        :type exclude_rules: list<str>

        :return: The validation manager.
        :rtype: :class:`tk_multi_data_validation.ValidationManager`
        """

        return self._manager_class(
            rule_settings=rule_settings,
            include_rules=include_rules,
            exclude_rules=exclude_rules,
        )

    def _log_metric_viewed_app(self):
        """
        Module local metric logging helper method for the "Logged In" metric.
        """

        try:
            from sgtk.util.metrics import EventMetric

            EventMetric.log(
                EventMetric.GROUP_TOOLKIT,
                "Opened Scene Data Validation App",
                log_once=False,
                bundle=self,
            )
        except:
            # Ignore all errors, e.g. using a core that does not support metrics.
            pass
