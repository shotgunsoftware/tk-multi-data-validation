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
from sgtk.platform.qt import QtCore, QtGui

from .list_view_auto_height import ListViewAutoHeight
from .validation_details_widget import ValidationDetailsWidget
from ..data.validation_rule_type import ValidationRuleType
from ..models.validation_rule_model import ValidationRuleModel
from ..models.validation_rule_type_model import ValidationRuleTypeModel
from ..models.validation_rule_proxy_model import ValidationRuleProxyModel
from ..utils.framework_qtwidgets import SGQIcon

from ..utils.framework_qtwidgets import (
    FilterMenu,
    FilterMenuButton,
    GroupedItemView,
    ViewItemDelegate,
    ViewItemAction,
    ShotgunOverlayWidget,
    SearchWidget,
    SGQToolButton,
    SGQWidget,
)

from ..utils.decorators import wait_cursor


class ValidationWidget(SGQWidget):
    """
    The main widget for the Data Validation App.

    This widget displays the provided data validation rules, and provides the user interface to execute the
    rule check and fix functions. When data violations are found, a details widget will display the
    individual data items that violate the rules.
    """

    #
    # Settings keys to save and restore the widget properties
    #
    SETTINGS_PREFIX = "ValidationWidget"
    SETTINGS_VIEW_MODE = "{prefix}_view_mode".format(prefix=SETTINGS_PREFIX)
    SETTINGS_DETAILS_VISIBILITY = "{prefix}_details_visibility".format(
        prefix=SETTINGS_PREFIX
    )
    SETTINGS_VIEW_DETAILS_SPLITTER_STATE = "{prefix}_view_details_splitter_state".format(
        prefix=SETTINGS_PREFIX
    )
    SETTINGS_SELECTED_RULE_TYPE_ID = "{prefix}_selected_rule_type_id".format(
        prefix=SETTINGS_PREFIX
    )

    #
    # List of view modes
    #
    (VIEW_MODE_LIST, VIEW_MODE_GROUPED,) = range(2)

    # Emit signals to indicate that the details widget is about to run an action, and when it has finished
    # (this is useful to # show a busy indicator, if the operation takes some time)
    details_about_to_execute_action = QtCore.Signal(dict)
    details_execute_action_finished = QtCore.Signal()

    def __init__(self, parent):
        """
        Create the validation widget.

        :param parent: The parent widget
        :type parent: QWidget
        """

        super(ValidationWidget, self).__init__(
            parent, layout_direction=QtGui.QBoxLayout.TopToBottom
        )

        self._bundle = sgtk.platform.current_bundle()

        self._view_mode = self.VIEW_MODE_GROUPED
        self._details_on = True
        self._rule_type_filter_on = True
        self._group_rules_by = "data_type"

        # Flag indicating that we're in the middle of validating all rules
        self._is_validating_all = False

        # Custom callbacks for validate and fix all operations. See properties for more details.
        # Set these callbacks to the default validate and fix methods
        self._validate_callback = self._validate_rules
        self._fix_callback = self._fix_rules

        # -----------------------------------------------------
        # Set up the UI

        self._setup_models()
        self._setup_ui()
        self._connect_signals()

        # -----------------------------------------------------
        # Initialize the widget data

        # Set an empty data message until the it is initialized
        self._view_overlay_widget.show_message("No validation data")

    #########################################################################################################
    # Properties

    @property
    def view_mode(self):
        """Get or set the current view mode."""
        return self._view_mode

    @view_mode.setter
    def view_mode(self, mode):
        self._set_view_mode(mode)

    @property
    def group_rules_by(self):
        """Get or set the field to group the validation rules by in the main view."""
        return self._group_rules_by

    @group_rules_by.setter
    def group_rules_by(self, field):
        self._group_rules_by = field

    @property
    def validate_button(self):
        """
        Get the validate all button.

        This may be useful to disconnect the default callback for the fix all button clicked signal, to
        execute a custom validate all operation.
        """
        return self._validate_button

    @property
    def fix_button(self):
        """
        Get the fix all button.

        This may be useful to disconnect the default callback for the fix all button clicked signal, to
        execute a custom fix all operation.
        """
        return self._fix_button

    @property
    def publish_button(self):
        """
        Get the publish button.
        """
        return self._publish_button

    @property
    def validate_callback(self):
        """
        Get or set the custom callback triggered when the validate button is clicked.

        This property must be a function that accepts a single parameter that is a list of ValidationRule
        objects.
        """
        return self._validate_callback

    @validate_callback.setter
    def validate_callback(self, cb):
        self._validate_callback = cb

    @property
    def fix_callback(self):
        """
        Get or set the custom callback triggered when the fix button is clicked.

        This property must be a function that accepts a single parameter that is a list of ValidationRule
        objects.
        """
        return self._fix_callback

    @fix_callback.setter
    def fix_callback(self, cb):
        self._fix_callback = cb

    #########################################################################################################
    # Public methods

    def save_state(self, user_settings, qsettings):
        """
        Save the widget state in the settings.

        :param user_settings: The Toolkit settings object to save the widget settings to.
        :type user_settings: UserSettings
        :param qsettings: The Qt settings for the App to save the widget settings to. The Toolkit settings
            has some limitations to storing byte array objects, so the Qt settings are required for saving
            those unsupported data types.
        """

        if user_settings:
            user_settings.store(self.SETTINGS_VIEW_MODE, self._view_mode)
            user_settings.store(
                self.SETTINGS_DETAILS_VISIBILITY, self._details_widget.isVisible()
            )

            rule_type_selected = self._rule_types_view.selectedIndexes()
            if rule_type_selected:
                rule_type_selected = rule_type_selected[0]
                rule_type_id = rule_type_selected.data(
                    ValidationRuleTypeModel.RULE_TYPE_ID_ROLE
                )
                user_settings.store(self.SETTINGS_SELECTED_RULE_TYPE_ID, rule_type_id)

        if qsettings:
            # SG Toolkit settings cannot handle byte arrays, so just save it in the QSettings objects
            qsettings.setValue(
                self.SETTINGS_VIEW_DETAILS_SPLITTER_STATE,
                self._view_details_splitter.saveState(),
            )

    def restore_state(self, user_settings, qsettings):
        """
        Restore the widget state from the settings.

        :param user_settings: The Toolkit settings object to restore the widget settings to.
        :type user_settings: UserSettings
        :param qsettings: The Qt settings for the App to restore the widget settings to. The Toolkit
            settings has some limitations to storing byte array objects, so the Qt settings are required for
            saving those unsupported data types.
        """

        if user_settings:
            self.view_mode = user_settings.retrieve(
                self.SETTINGS_VIEW_MODE, self.VIEW_MODE_GROUPED
            )

            show_details = user_settings.retrieve(
                self.SETTINGS_DETAILS_VISIBILITY, False
            )
            self._show_details(show_details)

            if self._rule_type_filter_on:
                rule_type_id = user_settings.retrieve(
                    self.SETTINGS_SELECTED_RULE_TYPE_ID,
                    ValidationRuleType.RULE_TYPE_NONE,
                )
                rule_type_item = self._rule_types_model.get_item_for_rule_type(
                    rule_type_id
                )
                if rule_type_item:
                    rule_type_index = rule_type_item.index()
                else:
                    rule_type_index = self._rule_types_model.index(0, 0)
                self._rule_types_view.selectionModel().select(
                    rule_type_index,
                    QtGui.QItemSelectionModel.ClearAndSelect
                    | QtGui.QItemSelectionModel.Current,
                )

        if qsettings:
            splitter_state = qsettings.value(self.SETTINGS_VIEW_DETAILS_SPLITTER_STATE)
            self._view_details_splitter.restoreState(splitter_state)

        # Must set the splitter collapsible property after the state is restored, or else this property is overwritten
        self._view_details_splitter.setChildrenCollapsible(False)

    def turn_on_details(self, on):
        """
        Turn details on to show the right-hand side details panel widget.

        :param on: Set to True to turn on, or False to turn off.
        :type on: bool
        """

        self._details_on = on

        if self._details_on:
            self._details_button.show()
        else:
            self._details_button.hide()
            self._details_widget.hide()
            self._details_overlay_widget.hide()

    def turn_on_rule_type_filter(self, on):
        """
        Turn rule type filter on to show the left-hand side filter widget.

        :param on: Set to True to turn on, or False to turn off.
        :type on: bool
        """

        self._rule_type_filter_on = on

        if self._rule_type_filter_on:
            self._rule_types_widget.show()
        else:
            self._rule_types_widget.hide()

    def set_validation_rules(self, validation_rules, validation_rule_types=None):
        """
        Set the validation rule types and data for the widget.

        This will reinitialize the validation rule models with the given data.

        :param validation_rules: The validation rules data
        :type validation_rules: list<ValidationRule>
        :param validation_rule_types: The type of validation rules to group the data by
        :type validation_rule_types: list<ValidationRuleType>
        """

        rule_types = validation_rule_types or []
        if not rule_types:
            # Not rule types provied, extract the rule types from the data
            for rule in validation_rules:
                rule_types.append(rule.type)

        self._rule_types_model.initialize_data(rule_types)
        self._rules_model.initialize_data(validation_rules)

    def get_active_rules(self):
        """
        Get the list of the validation rules that are currently active.

        A validation rule is considered to be active if it is visible in the current view. Validation
        operations, like "Validate" and "Fix All", may only be applied to active rules.

        :return: The list of validation rules.
        :rtype: list<ValidationRule>
        """

        rules = []

        src_model = self._rules_proxy_model.sourceModel()
        for proxy_row in range(self._rules_proxy_model.rowCount()):
            proxy_index = self._rules_proxy_model.index(proxy_row, 0)
            src_index = self._rules_proxy_model.mapToSource(proxy_index)

            rule = src_index.data(ValidationRuleModel.RULE_ITEM_ROLE)
            if rule:
                rules.append(rule)

            # Check if the source index has children
            src_model_item = src_model.itemFromIndex(src_index)
            child_rows = src_model_item.rowCount()
            for child_row in range(child_rows):
                child_item = src_model_item.child(child_row)
                # Need to check that child is visible (proxy model has accepted it)
                if self._rules_proxy_model.filterAcceptsRow(child_row, src_index):
                    rule = child_item.data(ValidationRuleModel.RULE_ITEM_ROLE)
                    if rule:
                        rules.append(rule)

        return rules

    ######################################################################################################
    # Protected methods

    def _setup_models(self):
        """
        Set up the models for the widget.

        This should be called once when creating the widget, and it should be called before _setup_ui.
        """

        # Rule types left-hand list (filter) navigation
        self._rule_types_model = ValidationRuleTypeModel(self)

        # Main validation rule source and proxy models
        self._rules_model = ValidationRuleModel(self, self.group_rules_by)
        self._rules_proxy_model = ValidationRuleProxyModel(self)
        self._rules_proxy_model.setSourceModel(self._rules_model)

    def _setup_ui(self):
        """
        Set up the widget UI.

        This should be called once when creating the widget.
        """

        # -----------------------------------------------------
        # Main content

        # Create the left-hand list filter navigation
        # TODO allow the list filter to be configurable (not only by rule types)
        self._rule_types_view = ListViewAutoHeight(self, height_padding=6)
        self._rule_types_view.setModel(self._rule_types_model)
        self._rule_types_view.setMouseTracking(True)
        self._rule_types_view.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self._rule_types_view.group_items_selectable = True
        self._rule_types_view.setMinimumWidth(200)
        self._rule_types_view.setSizePolicy(
            QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        )
        self._rule_types_delegate = self._create_rule_types_delegate()
        self._rule_types_widget = SGQWidget(
            self,
            layout_direction=QtGui.QBoxLayout.TopToBottom,
            child_widgets=[self._rule_types_view, None],
        )

        # Create horizontal splitter for main view and details widgets
        self._view_details_splitter = QtGui.QSplitter(self)
        self._view_details_splitter.setSizePolicy(
            QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        )
        self._view_details_splitter.setOrientation(QtCore.Qt.Horizontal)

        self._rules_view = GroupedItemView(self._view_details_splitter)
        self._rules_view.setMinimumWidth(300)
        self._rules_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._rules_view.setMouseTracking(True)
        self._rules_view.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self._rules_view.setModel(self._rules_proxy_model)
        self._rules_delegate = self._create_rules_delegate()
        self._view_overlay_widget = ShotgunOverlayWidget(self._rules_view)

        self._details_widget = ValidationDetailsWidget(self._view_details_splitter)
        self._details_overlay_widget = ShotgunOverlayWidget(self._details_widget)

        # Place the splitter in a container widget so that the left hand rule types widget and the splitter
        # widget vertically align
        rules_widget = SGQWidget(
            self,
            layout_direction=QtGui.QBoxLayout.TopToBottom,
            child_widgets=[self._view_details_splitter],
        )

        # Create a layout for the main content and add the widgets
        self._content_widget = SGQWidget(
            self,
            layout_direction=QtGui.QBoxLayout.LeftToRight,
            child_widgets=[self._rule_types_widget, rules_widget],
        )

        # -----------------------------------------------------
        # Top toolbar

        # List view mode button
        self._view_mode_list_button = SGQToolButton(self, icon=SGQIcon.ListViewMode())
        self._view_mode_list_button.setToolTip("Compact List View")
        self._view_mode_list_button.clicked.connect(
            lambda checked=None: self._set_view_mode(self.VIEW_MODE_LIST)
        )

        # Grouped view mode button
        self._view_mode_grouped_button = SGQToolButton(
            self, icon=SGQIcon.GridViewMode()
        )
        self._view_mode_grouped_button.setToolTip("Grouped View")
        self._view_mode_grouped_button.clicked.connect(
            lambda checked=None: self._set_view_mode(self.VIEW_MODE_GROUPED)
        )

        # Error view mode button
        self._errors_button = SGQToolButton(self, icon=SGQIcon.RedBullet())
        self._errors_button.setToolTip("Toggle to see only validation errors.")
        self._errors_button.clicked.connect(lambda checked=None: self._toggle_errors())

        # Details button
        self._details_button = SGQToolButton(self, icon=SGQIcon.Info())
        self._details_button.setToolTip("Show/Hide Details Panel")
        self._details_button.clicked.connect(
            lambda checked=None: self._show_details(checked)
        )

        # Filter text search bar
        self._search_text_widget = SearchWidget(self)
        self._search_text_widget.setMaximumWidth(150)
        self._search_text_widget.search_edited.connect(self._on_search_text_changed)

        # Filter menu
        self._filter_menu = FilterMenu(self)
        self._filter_menu.set_filter_roles(
            [self._rules_model.RULE_ITEM_ROLE,]
        )
        self._filter_menu.set_accept_fields(
            [
                "{role}.name".format(role=ValidationRuleModel.RULE_ITEM_ROLE),
                "{role}.data_type".format(role=ValidationRuleModel.RULE_ITEM_ROLE),
                "{role}.rule_type_name".format(role=ValidationRuleModel.RULE_ITEM_ROLE),
                "{role}.required".format(role=ValidationRuleModel.RULE_ITEM_ROLE),
                "{role}.optional".format(role=ValidationRuleModel.RULE_ITEM_ROLE),
                "{role}.manual".format(role=ValidationRuleModel.RULE_ITEM_ROLE),
            ]
        )
        self._filter_menu.set_visible_fields(
            [
                "{role}.name".format(role=ValidationRuleModel.RULE_ITEM_ROLE),
                "{role}.data_type".format(role=ValidationRuleModel.RULE_ITEM_ROLE),
                "{role}.required".format(role=ValidationRuleModel.RULE_ITEM_ROLE),
                "{role}.manual".format(role=ValidationRuleModel.RULE_ITEM_ROLE),
            ]
        )
        self._filter_menu.set_filter_model(self._rules_proxy_model)
        self._filter_menu.initialize_menu()

        # Filter menu button
        self._filter_menu_button = FilterMenuButton()
        self._filter_menu_button.setMenu(self._filter_menu)

        # Create the top toolbar layout and add all the widgets
        self._toolbar_widget = SGQWidget(
            self,
            child_widgets=[
                None,
                self._view_mode_list_button,
                self._view_mode_grouped_button,
                self._errors_button,
                self._search_text_widget,
                self._filter_menu_button,
                self._details_button,
            ],
        )

        # -----------------------------------------------------
        # Bottom right main action buttons
        #

        self._validate_button = QtGui.QPushButton("Validate")
        self._fix_button = QtGui.QPushButton("Fix All")
        self._publish_button = QtGui.QPushButton("Ready to Publish")

        # Create the button layout and add the widgets
        self._footer_widget = SGQWidget(
            self,
            child_widgets=[
                None,
                self._validate_button,
                self._fix_button,
                self._publish_button,
            ],
        )

        # Add the widgest to the main widget layout
        self.add_widgets(
            [self._toolbar_widget, self._content_widget, self._footer_widget,]
        )

    def _connect_signals(self):
        """
        Set up and connect signal slots between widgets.

        This should be called once when creating the widget.
        """

        # -----------------------------------------------------
        # Rule types view signals
        #
        self._rule_types_view.selectionModel().selectionChanged.connect(
            self._on_rule_type_selection_changed
        )
        self._rules_view.selectionModel().selectionChanged.connect(
            self._on_rule_selection_changed
        )
        self._rules_view.customContextMenuRequested.connect(
            self._on_rule_item_context_menu_requested
        )

        # -----------------------------------------------------
        # Rules types model signals
        #
        self._rule_types_model.modelReset.connect(self._rule_types_view.updateGeometry)
        self._rule_types_model.rule_type_check_state_changed.connect(
            self._on_rule_type_check_state_changed
        )

        # -----------------------------------------------------
        # Rules model signals
        #
        self._rules_model.itemChanged.connect(self._on_rules_model_item_changed)
        self._rules_model.modelReset.connect(self._on_rules_model_reset)
        self._rules_model.rule_check_state_changed.connect(
            self._on_rule_check_state_changed
        )

        # -----------------------------------------------------
        # Rules proxy model signals
        #
        self._rules_proxy_model.layoutChanged.connect(self._on_rules_proxy_model_reset)

        # -----------------------------------------------------
        # Details widget signals
        #
        self._details_widget.request_validate_data.connect(
            lambda rule: self.on_validate_rule(rule, refresh_details=True)
        )
        self._details_widget.request_fix_data.connect(self.on_fix_rule)
        self._details_widget.about_to_execute_action.connect(
            self.details_about_to_execute_action
        )
        self._details_widget.execute_action_finished.connect(
            self.details_execute_action_finished
        )

        # -----------------------------------------------------
        # Button clicked signals
        #
        self.validate_button.clicked.connect(self.on_validate_all)
        self.fix_button.clicked.connect(self.on_fix_all)

    def _create_rule_types_delegate(self):
        """
        Create the delegate for the rule types view and set it.
        """

        assert (
            self._rule_types_view
        ), "The rules view must be created before the delegate"

        delegate = ViewItemDelegate(self._rule_types_view)
        delegate.text_padding = ViewItemDelegate.Padding(13, 7, 0, 7)
        delegate.item_padding = ViewItemDelegate.Padding(4, 4, 0, 4)
        delegate.separator_role = ValidationRuleTypeModel.VIEW_ITEM_SEPARATOR_ROLE

        delegate.add_action(
            {
                "type": ViewItemAction.TYPE_ICON,
                "show_always": True,
                "get_data": get_rule_type_icon_data,
            },
            ViewItemDelegate.LEFT,
        )
        delegate.add_actions(
            [
                {
                    "type": ViewItemAction.TYPE_CHECK_BOX,
                    "show_always": True,
                    "padding_right": 24,
                    "padding_top": 0,
                    "padding_bottom": 0,
                    "get_data": get_rule_type_checkbox_data,
                },
                {
                    "type": ViewItemAction.TYPE_ICON,
                    "show_always": True,
                    "get_data": get_rule_type_status_icon_data,
                },
            ],
            ViewItemDelegate.RIGHT,
        )

        self._rule_types_view.setItemDelegate(delegate)
        return delegate

    def _create_rules_delegate(self):
        """
        Create the delegate for the rules view and set it.
        """

        assert self._rules_view, "The rules view must be created before the delegate"

        delegate = ViewItemDelegate(self._rules_view)
        delegate.text_padding = ViewItemDelegate.Padding(2, 7, 2, 7)

        delegate.header_role = ValidationRuleModel.VIEW_ITEM_HEADER_ROLE
        delegate.subtitle_role = ValidationRuleModel.VIEW_ITEM_SUBTITLE_ROLE
        delegate.text_role = ValidationRuleModel.VIEW_ITEM_TEXT_ROLE
        delegate.separator_role = ValidationRuleModel.VIEW_ITEM_SEPARATOR_ROLE
        delegate.loading_role = ValidationRuleModel.VIEW_ITEM_LOADING_ROLE
        delegate.height_role = ValidationRuleModel.VIEW_ITEM_HEIGHT_ROLE

        delegate.add_action(
            {
                "type": ViewItemAction.TYPE_PUSH_BUTTON,
                "icon": SGQIcon.TreeArrow(),
                "show_always": True,
                "features": QtGui.QStyleOptionButton.Flat,
                "get_data": get_expand_action_data,
                "callback": lambda view, index, pos: view.toggle_expand(index),
            },
            ViewItemDelegate.LEFT,
        )
        delegate.add_actions(
            [
                {
                    "type": ViewItemAction.TYPE_CHECK_BOX,
                    "show_always": True,
                    "padding_top": 0,
                    "padding_bottom": 0,
                    "padding_right": 0,
                    "get_data": get_rule_optional_data,
                },
                {
                    "type": ViewItemAction.TYPE_CHECK_BOX,
                    "check_state_role": ValidationRuleModel.RULE_MANUAL_CHECK_STATE_ROLE,
                    "show_always": True,
                    "padding_top": 0,
                    "padding_bottom": 0,
                    "padding_right": 14,
                    "get_data": get_rule_manual_data,
                },
                {
                    "type": ViewItemAction.TYPE_PUSH_BUTTON,
                    "name": "...",
                    "padding_left": 4,
                    "padding_right": 4,
                    "padding": 2,
                    "get_data": get_rule_show_actions_data,
                    "callback": self.rule_show_actions_callback,
                },
                {
                    "type": ViewItemAction.TYPE_PUSH_BUTTON,
                    "padding": 2,
                    "get_data": get_rule_fix_action_data,
                    "callback": self.rule_fix_action_callback,
                },
                {
                    "type": ViewItemAction.TYPE_PUSH_BUTTON,
                    "padding": 2,
                    "get_data": get_rule_check_action_data,
                    "callback": self.rule_check_action_callback,
                },
            ],
            ViewItemDelegate.TOP_RIGHT,
        )
        delegate.add_actions(
            [
                {
                    "type": ViewItemAction.TYPE_ICON,
                    "show_always": True,
                    "padding": 2,
                    "get_data": get_rule_status_action_data,
                },
            ],
            ViewItemDelegate.TOP_LEFT,
        )

        self._rules_view.setItemDelegate(delegate)
        return delegate

    def _set_view_mode(self, view_mode):
        """
        Set the current view mode for the main validation rules view.

        :param view_mode: The view mode (id) to set
            Supported view modes:
                VIEW_MODE_LIST - a flat list view
                VIEW_MODE_GROUPED - a grouped list view
        :type view_mode: int
        """

        if view_mode == self.VIEW_MODE_LIST:
            self._view_mode = view_mode
            self._rules_model.hierarchical = False
            self._rules_view.group_items_selectable = True
            self._rules_delegate.expand_role = None
            self._rules_delegate.visible_lines = 1
            self._rules_delegate.action_item_margin = 4
            self._view_mode_list_button.setChecked(True)
            self._view_mode_grouped_button.setChecked(False)

        elif view_mode == self.VIEW_MODE_GROUPED:
            self._view_mode = view_mode
            self._rules_model.hierarchical = True
            self._rules_view.group_items_selectable = False
            self._rules_delegate.expand_role = ValidationRuleModel.VIEW_ITEM_EXPAND_ROLE
            self._rules_delegate.visible_lines = 2
            self._rules_delegate.action_item_margin = 7
            self._view_mode_grouped_button.setChecked(True)
            self._view_mode_list_button.setChecked(False)

        else:
            assert False, "Unsupported view mode"

        self._rules_model.initialize_data()

    def _show_details(self, show=None):
        """
        Set the details widget visibility and update the widget according to the current selection.

        If the details functionality is turned off, nothing will happen.

        :param show: True will show the details, else False will hide it. If None, the details visibility
            will be toggled based on the current visibility state. Default=None
        :type show: bool
        """

        if not self._details_on:
            # The details widget is not available
            return

        if show is None:
            # Toggle the visibility
            show = self._details_button.isChecked()
        else:
            # Set the visibility explicitly
            self._details_button.setChecked(show)

        self._details_widget.setVisible(show)

        if show:
            indexes = self._rules_view.selectionModel().selectedIndexes()
            self._set_details(indexes)

    def _set_details(self, selected_indexes):
        """
        Set the details widget with the current seleciton.

        :param selected_indexes: The selected indexes to update the widget with
        :type selected_indexes: list<QtGui.QModelIndex>
        """

        if not selected_indexes:
            self._details_overlay_widget.show_message(
                "Select an item to see more details."
            )
        elif len(selected_indexes) > 1:
            self._details_overlay.show_message("Select a single item to see details.")
        else:
            self._details_overlay_widget.hide()
            model_index = selected_indexes[0]
            rule = model_index.data(ValidationRuleModel.RULE_ITEM_ROLE)
            self._details_widget.set_data(rule)

    def _refresh_details(self):
        """
        Refresh the details widget to reflect the latest changes to the data.
        """

        if not self._details_on or not self._details_widget.isVisible():
            return

        self._details_widget.refresh()

    def _show_context_menu(self, widget, pos, indexes=None):
        """
        Show a context menu for the selected items.

        :param widget: The source widget.
        :type widget: QtGui.QWidget
        :param pos: The position for the context menu relative to the source widget.
        :type pos: QtCore.QPoint
        """

        if not indexes:
            selection_model = self._rules_view.selectionModel()
            if selection_model:
                indexes = selection_model.selectedIndexes()

        # A single index must be selected
        if not indexes or len(indexes) > 1:
            return

        # Get the actions for this index
        src_index = _ensure_source_index(indexes[0])
        rule_model_item = src_index.model().itemFromIndex(src_index)
        rule_actions = rule_model_item.data(ValidationRuleModel.RULE_ACTIONS_ROLE)
        actions = []
        for rule_action in rule_actions:
            callback = rule_action.get("callback")
            if not callback:
                continue
            args = rule_action.get("args", [])
            kwargs = rule_action.get("kwargs", {})
            action = QtGui.QAction(rule_action["name"])
            action.triggered.connect(lambda fn=callback, a=args, k=kwargs: fn(*a, **k))
            actions.append(action)

        # Add action to show details for the item that the context menu is shown for.
        show_details_action = QtGui.QAction("Show Details")
        show_details_action.triggered.connect(lambda: self._show_details(show=True))
        actions.append(show_details_action)

        # Create the menu, add the actions and show it
        menu = QtGui.QMenu(self)
        menu.addActions(actions)
        pos = widget.mapToGlobal(pos)
        menu.exec_(pos)

    @sgtk.LogManager.log_timing
    def _validate_rules(self, rules, refresh_details=False):
        """
        The default validate operation that executes the validate function for each of the rules.

        :param rules: The list of rules, or single rule, to validate.
        :type rules: list<ValidationRule> | ValidationRule
        :param refresh_details: Set to True to refresh the details widget after the validation.
        :type refresh_details: bool
        """

        if not isinstance(rules, list):
            rules = [rules]

        for rule in rules:
            self._bundle.logger.debug("Validating Rule: {}".format(rule.name))
            self.validate_rule_begin(rule)
            rule.exec_check()
            self.validate_rule_finished(rule, update_rule_type=False)

        if refresh_details:
            # Refresh the details since its data may have changed
            self._refresh_details()

    @sgtk.LogManager.log_timing
    def _fix_rules(self, rules):
        """
        The default fix operation that executes the fix function for each of the rules.

        NOTE this default fix operation does not take into account rule dependencies. Rules will be executed
        in the order as they appear in the model. Use the ValidationManager to implement rule resolution order
        based on dependenceis.

        :param rules: The list of rules to validate.
        :type rules: list<ValidationRule>
        """

        if not isinstance(rules, list):
            rules = [rules]

        for rule in rules:
            self._bundle.logger.debug("Resolving Rule: {}".format(rule.name))
            self.fix_rule_begin(rule)
            rule.exec_fix()
            self.fix_rule_finished(rule)

    def _update_view_overlay(self):
        """
        Update the main rules view overlay widget.
        """

        if self._rules_model.rowCount() <= 0:
            self._view_overlay_widget.show_message("No validation data.")

        elif self._rules_proxy_model.rowCount() <= 0:
            if self._errors_button.isChecked():
                msg = "No validation errors found."
            else:
                msg = "No results. Clear filters to see validation data."
            self._view_overlay_widget.show_message(msg)

        else:
            self._view_overlay_widget.hide()

    ######################################################################################################
    # Callback methods

    @wait_cursor
    def on_validate_all(self):
        """
        Callback triggered when the validation all button has been triggered.

        If the custom validate all callback is set, then get all rules from the model to resolve and pass it
        to the custom callback, else call the default validate all operation.
        """

        self.validate_all_begin()
        try:
            active_rules = self.get_active_rules()
            self.validate_callback(active_rules)
        finally:
            self.validate_all_finished()

    @wait_cursor
    def on_fix_all(self):
        """
        Callback triggered when the fix all button has been triggered.

        If the custom fix all callback is set, then get all rules from the model to resolve and pass it to
        the custom callback, else call the default fix all operation.
        """

        active_rules = self.get_active_rules()
        self.fix_callback(active_rules)

    @wait_cursor
    def on_validate_rule(self, rule, refresh_details=False):
        """
        Callback triggered to validate a specific rule.

        :param rule: The validation rule to run the check function for.
        :type rule: VaildationRule
        :param refresh_details: Set to True to refresh the details widget after the validation.
        :type refresh_details: bool
        """

        self.validate_rule_begin(rule)
        try:
            self.validate_callback([rule])
        finally:
            self.validate_rule_finished(rule)

        if refresh_details:
            # Refresh the details since its data may have changed
            self._refresh_details()

    @wait_cursor
    def on_fix_rule(self, rule):
        """
        Callback triggered to fix a specific rule.

        :param rule: The validation rule to run the fix function for.
        :type rule: VaildationRule
        """

        self.fix_callback([rule])

    def validate_rule_begin(self, rule):
        """
        Call this method before a validaiton rule is check function is executed.

        :param rule: The rule that is about to start executing its check function.
        :type rule: ValidationRule
        """

        if not rule:
            return

        # TODO any specific actions before begin check (ie. set loading)
        # rule_item = self._rules_model.get_item_for_rule(rule)

    def validate_rule_finished(self, rule, update_rule_type=True):
        """
        Call this method after a validation rule check function has finished executing.

        :param rule: The rule that finished executing its check function.
        :type rule: ValidationRule
        :param update_rule_type: True will update the rule type model data based on the updated rule.
        :type update_rule_type: bool
        """

        if not rule or self._is_validating_all:
            # Do not process the individual rule after validation if there is not rule, or all rules are
            # being validated at once
            return

        rule_item = self._rules_model.get_item_for_rule(rule)
        if not rule_item:
            return

        updated = False

        if update_rule_type:
            # Update the rule type status corresponding to the updated rule
            status = self._rules_model.get_status_for_rule_type(rule.type)
            rule_type_index = self._rule_types_model.get_item_for_rule_type(rule.type)
            if rule_type_index:
                rule_type_index.setData(
                    status, ValidationRuleTypeModel.RULE_TYPE_STATUS_ROLE
                )
                updated = True

        if not updated:
            rule_item.emitDataChanged()

    def validate_all_begin(self):
        """
        Call this method before all validation rules are checked.
        """

        self._is_validating_all = True

    def validate_all_finished(self):
        """
        Call this method after all validation rules have been checked.
        """

        # Get and update the rule type statuses
        (valid, errors, incomplete,) = self._rules_model.get_statuses_for_rule_type()
        self._rule_types_model.set_statuses(valid, errors, incomplete)

        # Emit signal that validation rules have been updated
        self._rules_model.emit_all_data_changed()

        self._rules_proxy_model._update()

        self._is_validating_all = False

    def fix_rule_begin(self, rule):
        """
        Call this method before a validaiton rule is fix function is executed.

        :param rule: The rule that is about to start executing its fix function.
        :type rule: ValidationRule
        """

        if not rule:
            return

        # TODO any specific actions before begin check (ie. set loading)
        # rule_item = self._rules_model.get_item_for_rule(rule)

    def fix_rule_finished(self, rule):
        """
        Call this method after a validation rule fix function has finished executing.

        :param rule: The rule that finished executing its fix function.
        :type rule: ValidationRule
        """

        if not rule:
            return

        rule_item = self._rules_model.get_item_for_rule(rule)
        if not rule_item:
            return

        # The rule data may have changed, emit the data changed signal to indicate rule data updates.
        rule_item.emitDataChanged()

    def _on_rule_item_context_menu_requested(self, pos):
        """
        Callback triggered when a rule from the view has been right-clicked.

        :param pos: The mouse position, relative to the sender (widget), captured when triggering this
            callback.
        :type pos: QtCore.QPoint
        """

        self._show_context_menu(self.sender(), pos)

    def _on_rule_item_double_clicked(self, index):
        """
        Callback triggered when a rule from the view has been double-clicked.

        :param index: The index the mouse double-clicked on.
        :type index: QModelIndex
        """

        rule = index.data(ValidationRuleModel.RULE_ITEM_ROLE)
        self.on_validate_rule(rule, refresh_details=True)

    def _on_search_text_changed(self):
        """
        Callback triggered when the search widget text has been updated.
        """

        search_text = self._search_text_widget._get_search_text()
        self._rules_proxy_model.set_text_filter_value(
            search_text, data_func=self._rules_delegate.get_displayed_text
        )

    def _on_rules_model_reset(self):
        """
        Callback triggered when the rules model has been reset.
        """

        self._update_view_overlay()

        self._filter_menu.refresh(force=True)

    def _on_rules_proxy_model_reset(self):
        """
        Callback triggered when the rules proxy model has been reset.
        """

        self._update_view_overlay()

    def _on_rules_model_item_changed(self, item):
        """
        Callback triggered when data for the item in the rules model has been updated.

        :param item: The item in the ValidationRuleModel
        :type item: QStandardItem
        """

        rule = item.data(ValidationRuleModel.RULE_ITEM_ROLE)
        if not rule:
            return

        # Check if the details widget needs to be updated to reflect the item changes
        if (
            self._details_widget.isVisible()
            and self._details_widget.rule
            and (
                (self._is_validating_all and self._details_widget.rule.id == rule.id)
                or (
                    not self._is_validating_all
                    and self._details_widget.rule.id != rule.id
                )
            )
        ):
            self._details_widget.set_data(rule)

    def _on_rule_check_state_changed(self, rule, check_state):
        """
        Callback triggered when a rule has been checked.

        When a rule is checked, this will affect the data of the rule types model.

        :param rule: The valudaiton rule whose check state changed
        :type rule: ValidationRule
        """

        # Update the rule types model data
        self._rule_types_model.set_check_state_for_rule_type(rule.type, check_state)

    def _on_rule_type_check_state_changed(self, rule_type, check_state):
        """
        Callback triggered when a rule type has been checked.

        When a rule type is checked, thsi will affect the data of the rules model.

        :param rule_type: The validation rule type whose check state changed
        :type rule_type: ValidationRuleType
        """

        if rule_type.id == ValidationRuleType.RULE_TYPE_MANUAL:
            check_state_role = ValidationRuleModel.RULE_MANUAL_CHECK_STATE_ROLE
        else:
            check_state_role = QtCore.Qt.CheckStateRole

        self._rules_model.set_check_state_for_rule_type(
            rule_type, check_state, check_state_role
        )

    def _on_rule_type_selection_changed(self):
        """
        Callback triggered when the rule type selection has changed.

        The rules list will be updated to reflect the current rule type selection.
        """

        indexes = self._rule_types_view.selectionModel().selectedIndexes()
        if not indexes:
            return

        # Only single selection
        index = indexes[0]

        # Get the value to filter the rule type by
        rule_type = index.data(ValidationRuleTypeModel.RULE_TYPE_ROLE)

        # Filter the rules view by the selected rule type
        if rule_type is None or rule_type.id == ValidationRuleType.RULE_TYPE_NONE:
            self._rules_proxy_model.remove_rule_type_filter()
        else:
            self._rules_proxy_model.set_rule_type(
                rule_type, filter_role=ValidationRuleModel.RULE_ITEM_ROLE,
            )

    def _on_rule_selection_changed(self):
        """
        Callback triggered when the rule selection has chagned.

        The details widget will be updated to reflect the current rule selection.
        """

        indexes = self._rules_view.selectionModel().selectedIndexes()
        self._set_details(indexes)

    def _toggle_errors(self, show=None):
        """
        Callback triggered to show only the validation rules with errors.

        :param show: Set to True to show only errors, False to show all, and None to toggle the current state.
        :type show: bool
        """

        self._rules_proxy_model.turn_on_error_filter(on=None)

    ######################################################################################################
    # ViewItemDelegate callback functions
    #

    def rule_show_actions_callback(self, view, index, pos):
        """
        The validation rule action to show the list of action items was triggered.

        :param view: The view the index belongs to.
        :type view: QAbstractItemView
        :param index: The index to act on
        :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`
        :param pos: The mouse position captured on triggered this callback
        :type pos: :class:`sgtk.platform.qt.QtCore.QPoint`
        """

        self._show_context_menu(view, pos, [index])

    @wait_cursor
    def rule_check_action_callback(self, view, index, pos):
        """
        The validation rule action to execute the rule check function was triggered.

        :param view: The view the index belongs to.
        :type view: QAbstractItemView
        :param index: The index to act on
        :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`
        :param pos: The mouse position captured on triggered this callback
        :type pos: :class:`sgtk.platform.qt.QtCore.QPoint`
        """

        # Get the ValidationRule object for the index
        rule = index.data(ValidationRuleModel.RULE_ITEM_ROLE)
        self.on_validate_rule(rule, refresh_details=True)

    @wait_cursor
    def rule_fix_action_callback(self, view, index, pos):
        """
        The validation rule action to execute the rule fix function was triggered.

        :param view: The view the index belongs to.
        :type view: QAbstractItemView
        :param index: The index to act on
        :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`
        :param pos: The mouse position captured on triggered this callback
        :type pos: :class:`sgtk.platform.qt.QtCore.QPoint`
        """

        # Get the ValidationRule object for the index
        rule = index.data(ValidationRuleModel.RULE_ITEM_ROLE)
        self.on_fix_rule(rule)


#############################################################################################################
# ViewItemDelegate callback functions (independent of the ValidationWidget class)
#


def get_expand_action_data(parent, index):
    """
    Callback function triggered by the ViewItemDelegate.

    Get the data for displaying the rule group header expand action.

    :param parent: The parent of the ViewItemDelegate which triggered this callback
    :type parent: QAbstractItemView
    :param index: The index the action is for.
    :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`

    :return: The data for the action and index.
    :rtype: dict (see the ViewItemAction class attribute `get_data` for more details)
    """

    visible = index.data(ValidationRuleModel.IS_GROUP_ITEM_ROLE)
    state = QtGui.QStyle.State_Active | QtGui.QStyle.State_Enabled

    if parent.is_expanded(index):
        state |= QtGui.QStyle.State_Off
    else:
        state |= QtGui.QStyle.State_On

    return {"visible": visible, "state": state}


def get_rule_type_icon_data(parent, index):
    """
    Callback function triggered by the ViewItemDelegate.

    Get the data for displaying the rule type icon.

    :param parent: The parent of the ViewItemDelegate which triggered this callback
    :type parent: QAbstractItemView
    :param index: The index the action is for.
    :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`

    :return: The data for the action and index.
    :rtype: dict (see the ViewItemAction class attribute `get_data` for more details)
    """

    icon = index.data(ValidationRuleTypeModel.RULE_TYPE_ICON_ROLE)
    visible = bool(icon)

    return {"visible": visible, "icon": icon}


def get_rule_type_status_icon_data(parent, index):
    """
    Callback function triggered by the ViewItemDelegate.

    Get the data for displaying the rule type status.

    :param parent: The parent of the ViewItemDelegate which triggered this callback
    :type parent: QAbstractItemView
    :param index: The index the action is for.
    :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`

    :return: The data for the action and index.
    :rtype: dict (see the ViewItemAction class attribute `get_data` for more details)
    """

    icon = index.data(ValidationRuleTypeModel.RULE_TYPE_STATUS_ICON_ROLE)
    visible = bool(icon)

    return {"visible": visible, "icon": icon}


def get_rule_type_checkbox_data(parent, index):
    """
    Callback function triggered by the ViewItemDelegate.

    Get the data for displaying the rule type checkbox widget.

    :param parent: The parent of the ViewItemDelegate which triggered this callback
    :type parent: QAbstractItemView
    :param index: The index the action is for.
    :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`

    :return: The data for the action and index.
    :rtype: dict (see the ViewItemAction class attribute `get_data` for more details)
    """

    rule_type_id = index.data(ValidationRuleTypeModel.RULE_TYPE_ID_ROLE)
    checkbox_state = index.data(QtCore.Qt.CheckStateRole)
    icon = index.data(ValidationRuleTypeModel.CHECKBOX_ICON_ROLE)

    # This action is "visible" for all to align actions in each row, but for rule types that this
    # action does not apply to, it will be hidden (but take up the space)
    visible = True
    applicable = rule_type_id in (
        ValidationRuleType.RULE_TYPE_MANUAL,
        ValidationRuleType.RULE_TYPE_OPTIONAL,
    )

    state = QtGui.QStyle.State_Active | QtGui.QStyle.State_Enabled
    if checkbox_state == QtCore.Qt.Checked:
        state |= QtGui.QStyle.State_On
    elif checkbox_state == QtCore.Qt.PartiallyChecked:
        if icon:
            # Icons cannot have a partial check state - set the state to be on
            state |= QtGui.QStyle.State_On
        else:
            state |= QtGui.QStyle.State_NoChange
    else:
        state |= QtGui.QStyle.State_Off

    return {
        "visible": visible,
        "placeholder": not applicable,
        "state": state,
        "icon": icon,
        "padding_right": 0 if icon else 14,
    }


def get_rule_manual_data(parent, index):
    """
    Callback function triggered by the ViewItemDelegate.

    Get the data for displaying a manual rule.

    :param parent: The parent of the ViewItemDelegate which triggered this callback
    :type parent: QAbstractItemView
    :param index: The index the action is for.
    :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`

    :return: The data for the action and index.
    :rtype: dict (see the ViewItemAction class attribute `get_data` for more details)
    """

    rule = index.data(ValidationRuleModel.RULE_ITEM_ROLE)
    if not rule:
        return {"visible": False}

    if not rule.manual:
        return {"visible": False}

    checkbox_state = index.data(ValidationRuleModel.RULE_MANUAL_CHECK_STATE_ROLE)
    state = QtGui.QStyle.State_Active | QtGui.QStyle.State_Enabled

    if checkbox_state == QtCore.Qt.Checked:
        state |= QtGui.QStyle.State_On
    elif checkbox_state == QtCore.Qt.PartiallyChecked:
        state |= QtGui.QStyle.State_NoChange
    else:
        state |= QtGui.QStyle.State_Off

    return {
        "visible": True,
        "state": state,
    }


def get_rule_optional_data(parent, index):
    """
    Callback function triggered by the ViewItemDelegate.

    Get the data for displaying an optional rule.

    :param parent: The parent of the ViewItemDelegate which triggered this callback
    :type parent: QAbstractItemView
    :param index: The index the action is for.
    :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`

    :return: The data for the action and index.
    :rtype: dict (see the ViewItemAction class attribute `get_data` for more details)
    """

    rule = index.data(ValidationRuleModel.RULE_ITEM_ROLE)
    if not rule:
        return {"visible": False}

    if not rule.optional:
        if rule.manual:
            # Ensure the manual checkboxes are aligned across rows
            return {"visible": True, "placeholder": True, "padding_left": 22}
        return {"visible": False}

    checkbox_icon = index.data(ValidationRuleModel.CHECKBOX_ICON_ROLE)
    checkbox_state = index.data(QtCore.Qt.CheckStateRole)
    state = QtGui.QStyle.State_Active | QtGui.QStyle.State_Enabled

    if checkbox_state == QtCore.Qt.Checked:
        state |= QtGui.QStyle.State_On
    elif checkbox_state == QtCore.Qt.PartiallyChecked:
        state |= QtGui.QStyle.State_NoChange
    else:
        state |= QtGui.QStyle.State_Off

    return {
        "visible": True,
        "state": state,
        "icon": checkbox_icon,
    }


def get_rule_show_actions_data(parent, index):
    """
    Callback function triggered by the ViewItemDelegate.

    Get the data for displaying and executing the rule action items.

    :param parent: The parent of the ViewItemDelegate which triggered this callback
    :type parent: QAbstractItemView
    :param index: The index the action is for.
    :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`

    :return: The data for the action and index.
    :rtype: dict (see the ViewItemAction class attribute `get_data` for more details)
    """

    visible = bool(index.data(ValidationRuleModel.RULE_ACTIONS_ROLE))

    return {
        "visible": visible,
    }


def get_rule_check_action_data(parent, index):
    """
    Callback function triggered by the ViewItemDelegate.

    Get the data for displaying and executing the rule check action.

    :param parent: The parent of the ViewItemDelegate which triggered this callback
    :type parent: QAbstractItemView
    :param index: The index the action is for.
    :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`

    :return: The data for the action and index.
    :rtype: dict (see the ViewItemAction class attribute `get_data` for more details)
    """

    visible = index.data(ValidationRuleModel.RULE_CHECK_FUNC_ROLE) is not None
    name = index.data(ValidationRuleModel.RULE_CHECK_NAME_ROLE)

    if name and index.data(ValidationRuleModel.RULE_EXECUTED_ROLE):
        # Modify the name to prepend "Re", e.g. Validate -> Revalidate
        name = "Re{name}".format(name=name.lower())

    return {
        "visible": visible,
        "name": name,
    }


def get_rule_fix_action_data(parent, index):
    """
    Callback function triggered by the ViewItemDelegate.

    Get the data for displaying and executing the rule fix action.

    :param parent: The parent of the ViewItemDelegate which triggered this callback
    :type parent: QAbstractItemView
    :param index: The index the action is for.
    :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`

    :return: The data for the action and index.
    :rtype: dict (see the ViewItemAction class attribute `get_data` for more details)
    """

    name = index.data(ValidationRuleModel.RULE_FIX_NAME_ROLE)
    visible = index.data(ValidationRuleModel.RULE_FIX_FUNC_ROLE) is not None

    return {
        "visible": visible,
        "name": name,
    }


def get_rule_status_action_data(parent, index):
    """
    Callback function triggered by the ViewItemDelegate.

    Get the data for displaying the rule status.

    :param parent: The parent of the ViewItemDelegate which triggered this callback
    :type parent: QAbstractItemView
    :param index: The index the action is for.
    :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`

    :return: The data for the action and index.
    :rtype: dict (see the ViewItemAction class attribute `get_data` for more details)
    """

    icon = index.data(ValidationRuleModel.RULE_STATUS_ICON_ROLE)
    visible = icon is not None

    return {
        "visible": visible,
        "icon": icon,
    }


#############################################################################################################
# Helper functions


def _ensure_source_index(index):
    """
    Convenience method to get the source index from the given index.

    :param index: The index to ensure is the source index
    :type index: QtGui.QModelIndex

    :return: The source index for the given index
    :rtype: QtGui.QModelIndex
    """

    src_model = index.model()
    if isinstance(src_model, QtGui.QSortFilterProxyModel):
        return src_model.mapToSource(index)

    return index
