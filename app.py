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

        # Store references to validation class objects such that other modules have access to
        # the data validation functionality
        #   - ValidationManager: class provides the interface for validatin.
        #   - ValidationWidget: class provides the user interface to perform data validation
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

    def create_validation_manager(
        self,
        rule_settings=None,
        include_rules=None,
        exclude_rules=None,
        logger=None,
        notifier=None,
        has_ui=False,
    ):
        """
        Create a validation manager instance.

        :param rule_settings: The settings data containing the validation rules
        :type rule_settings: list<dict>
        :param include_rules: The validation rule ids to use from the settings
        :type include_rules: list<str>
        :param exclude_rules: The validation rule ids to not use from the settings
        :type exclude_rules: list<str>
        :param logger: This is a standard python logger to use during validation. A default logger
            will be provided if not supplied.
        :type logger: A standard python logger.
        :param notifier: A notifier object to emit Qt signals.
        :type notifier: ValidationNotifer
        :param has_ui: Set to True if the manager is being used with a UI, else False.
        :type has_ui: bool

        :return: The validation manager.
        :rtype: :class:`tk_multi_data_validation.ValidationManager`
        """

        return self._manager_class(
            rule_settings=rule_settings,
            include_rules=include_rules,
            exclude_rules=exclude_rules,
            logger=logger,
            notifier=notifier,
            has_ui=has_ui,
        )

    def create_validation_widget(self, parent, group_rules_by=None):
        """
        Create the main validation widget.

        This can be used to embed the data validation functionality in another App.

        :param parent: The parent widget
        :type parent: QWidget
        :param group_rules_by: The validation rule field that the view will group rules by
        :type group_rules_by: str

        :return: The data validation widget.
        :rtype: :class:`tk_multi_data_validation.ValidationWidget`
        """

        return self._widget_class(parent, group_rules_by)

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
