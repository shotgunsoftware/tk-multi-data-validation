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
from sgtk.platform.qt import QtGui, QtCore

from .api import ValidationManager
from .api.data import ValidationRule
from .widgets import ValidationWidget
from .utils.validation_notifier import ValidationNotifier

settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")


class AppDialog(QtGui.QWidget):
    """
    The main Data Validation App dialog.
    """

    #
    # Settings keys to save/restore
    #
    SETTINGS_WIDGET_GEOMETRY = "app_dialog_geometry"

    # Notifier IDS for show/hide busy popup
    VALIDATE_ID = "validate"
    RESOLVE_ID = "resolve"

    def __init__(self, parent=None):
        """
        Initialize the App dialog.

        :param parent: The parent QWidget for this dialog.
        :type parent: QtGui.QWidget
        """

        QtGui.QWidget.__init__(self, parent)

        self._bundle = sgtk.platform.current_bundle()

        # Information about the busy popup. Set 'showing' to True when the popup is showing, else False.
        # Set the title and details to what the current busy popup is showing.
        self._busy_info = {"id": None, "showing": False, "title": "", "details": ""}

        # -----------------------------------------------------
        # Create validation manager

        self._manager = ValidationManager(notifier=ValidationNotifier(), has_ui=True)
        self._manager.accept_rule_fn = lambda rule: not rule.optional or rule.checked

        # -----------------------------------------------------
        # Set up settings

        self._settings_manager = settings.UserSettings(self._bundle)

        # Define another QSettings object to store raw values. This is a work around for storing QByteArray objects in Python 3,
        # since the settings manager converts QByteArray objects to str, which causes an error when retrieving it and trying
        # to set the splitter state with a str instead of QByteArray object.
        self._raw_values_settings = QtCore.QSettings(
            "ShotGrid Software", "{app}_raw_values".format(app=self._bundle.name)
        )

        # -----------------------------------------------------
        # Set up UI

        # Requires the validation manager to alrady be creatd.
        self._setup_ui()
        self._connect_signals()

        # -----------------------------------------------------
        # Restore settings

        widget_geometry = self._raw_values_settings.value(
            self.SETTINGS_WIDGET_GEOMETRY, None
        )
        if widget_geometry:
            self.restoreGeometry(widget_geometry)

        self._validation_widget.restore_state(
            self._settings_manager, self._raw_values_settings
        )

        # -----------------------------------------------------
        # Log metric for app usage

        self._bundle._log_metric_viewed_app()

    def _setup_ui(self):
        """
        Set up the UI manually (without a .ui file). This should only be called once.
        """

        # -----------------------------------------------------
        # Create the main validation widget

        self._validation_widget = ValidationWidget(self, group_rules_by="data_type")

        # NOTE hide the left-hand filter widget for now for simplicity
        self._validation_widget.turn_on_rule_type_filter(False)

        # TODO implement the functionality for validation -> publish and then this button can be shown
        self._validation_widget.publish_button.hide()

        # Set custom callbacks for validating/fix all and validating/fix individual rules
        self._validation_widget.validate_rules_callback = self._manager.validate_rules
        self._validation_widget.validate_all_callback = (
            lambda rules: self._manager.validate()
        )
        self._validation_widget.fix_rules_callback = self._resolve_rules
        self._validation_widget.fix_all_callback = lambda rules: self._manager.resolve(
            pre_validate=True, post_validate=True
        )

        self._validation_widget.set_validation_rules(
            self._manager.rules, self._manager.rule_types
        )

        # -----------------------------------------------------
        # Add the validation widget to this dialog's layout

        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._validation_widget)
        self.setLayout(main_layout)

    def _connect_signals(self):
        """
        Set up Qt signals and slot connections.
        """

        # ------------------------------------------------------------
        # ValidationManager signals connected to this dialog

        self._manager.notifier.validate_all_begin.connect(
            lambda: self.show_busy_popup(
                self.VALIDATE_ID,
                "Validating Scene Data...",
                "This may take a few minutes. Thanks for waiting.",
            )
        )
        self._manager.notifier.validate_all_finished.connect(
            lambda: self.hide_busy_popup(self.VALIDATE_ID)
        )

        self._manager.notifier.validate_rule_begin.connect(
            lambda rule: self.show_busy_popup(
                "{}_{}".format(self.VALIDATE_ID, rule.id),
                "Validating {}...".format(rule.name),
                "This may take a few minutes. Thanks for waiting.",
            )
        )
        self._manager.notifier.validate_rule_finished.connect(
            lambda rule: self.hide_busy_popup("{}_{}".format(self.VALIDATE_ID, rule.id))
        )

        self._manager.notifier.resolve_all_begin.connect(
            lambda: self.show_busy_popup(
                self.RESOLVE_ID,
                "Processing Scene Data...",
                "This may take a few minutes. Thanks for waiting.",
            )
        )
        self._manager.notifier.resolve_all_finished.connect(
            lambda: self.hide_busy_popup(self.RESOLVE_ID)
        )

        self._manager.notifier.about_to_open_msg_box.connect(
            lambda: self.hide_busy_popup(self._busy_info["id"], clear_info=False)
        )
        self._manager.notifier.msg_box_closed.connect(self.show_busy_popup)

        # ------------------------------------------------------------
        # ValidationManager signals connected to the ValidationWidget

        # Connect signals from manager and widget
        self._manager.notifier.validate_rule_begin.connect(
            self._validation_widget.validate_rule_begin
        )
        self._manager.notifier.validate_rule_finished.connect(
            self._validation_widget.validate_rule_finished
        )
        self._manager.notifier.validate_all_begin.connect(
            self._validation_widget.validate_all_begin
        )
        self._manager.notifier.validate_all_finished.connect(
            self._validation_widget.validate_all_finished
        )
        self._manager.notifier.resolve_rule_begin.connect(
            self._validation_widget.fix_rule_begin
        )
        self._manager.notifier.resolve_rule_finished.connect(
            self._validation_widget.fix_rule_finished
        )

        # ------------------------------------------------------------
        # ValidationWidget signals

        self._validation_widget.details_about_to_execute_action.connect(
            lambda action: self.show_busy_popup(
                "exec_action_{}".format(action.get("name")),
                "Executing Action...",
                action.get("name", "Please hold on."),
            )
        )
        self._validation_widget.details_execute_action_finished.connect(
            lambda action: self.hide_busy_popup(
                "exec_action_{}".format(action.get("name"))
            )
        )

    def _resolve_rules(self, rules):
        """
        Helper function to execute the manager resolve rule and then call validate post resolution.

        :param rule: The rule or list of rules to resolve and then validate.
        :type rule: ValidationRule | list<ValidationRule>
        """

        if isinstance(rules, ValidationRule):
            rule_id = rules.id
            rule_name = rules.name
            rules = [rules]
        else:
            rule_id = "all"
            rule_name = None

        busy_id = "{}_{}".format(self.RESOLVE_ID, rule_id)
        self.show_busy_popup(
            busy_id,
            "Resolving Data{}...".format(
                " '{}'".format(rule_name) if rule_name else ""
            ),
            "Please hold on.",
        )

        try:
            self._manager.resolve_rules(rules)
            self._manager.validate_rules(rules)
        finally:
            self.hide_busy_popup(busy_id)

    ######################################################################################################
    # Override Qt methods

    def closeEvent(self, event):
        """
        Overriden method triggered when the widget is closed.  Cleans up as much as possible
        to help the GC.

        :param event: Close event
        """

        # Save settings
        self._raw_values_settings.setValue(
            self.SETTINGS_WIDGET_GEOMETRY, self.saveGeometry()
        )
        self._validation_widget.save_state(
            self._settings_manager, self._raw_values_settings
        )

        return QtGui.QWidget.closeEvent(self, event)

    ######################################################################################################
    # Public methods

    def show_busy_popup(self, busy_id=None, title=None, details=None):
        """
        Show the busy popup message dialog.

        This can be used to display a "loading" popup message for when the validation is performing an
        operation that takes some time.

        :param busy_id: The unique identifier to set the busy info.
        :type busy_id: str
        :param title: The title for the popup message. Set to None to use the current busy info title.
        :type title: str
        :param title: The details for the popup message. Set to None to use the current busy info details.
        :type title: str
        """

        if self._busy_info["showing"]:
            return

        engine = self._bundle.engine
        if not engine:
            return

        if busy_id:
            self._busy_info["id"] = busy_id

        if title:
            self._busy_info["title"] = title

        if details:
            self._busy_info["details"] = details

        engine.show_busy(self._busy_info["title"], self._busy_info["details"])
        self._busy_info["showing"] = True

    def hide_busy_popup(self, busy_id, clear_info=True):
        """
        Hide the busy popup message dialog.

        :param busy_id: The unique identifier to set the busy info.
        :type busy_id: str
        :param clear_info: Set to True will reset the busy information. Set to False to keep the busy
            information to restore the next time `show_busy_popup` in called without specifying a title
            or details.
        :type clear_info: bool
        """

        if not self._busy_info["showing"] or busy_id != self._busy_info["id"]:
            return

        engine = self._bundle.engine
        if not engine:
            return

        engine.clear_busy()
        self._busy_info["showing"] = False

        # Clear the busy info if specified. Do not clear if the popup is the popup needs to be resumed at a
        # later time (e.g. pause pop up for user interaction and resume after)
        if clear_info:
            self._busy_info["id"] = None
            self._busy_info["title"] = ""
            self._busy_info["details"] = ""
