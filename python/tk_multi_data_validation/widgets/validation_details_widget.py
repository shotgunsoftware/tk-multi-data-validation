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

from ..api.data.validation_rule import ValidationRule
from ..models.validation_rule_details_model import ValidationRuleDetailsModel
from ..utils.framework_qtwidgets import (
    GroupedItemView,
    ViewItemDelegate,
    ViewItemAction,
    SGQWidget,
    SGQLabel,
    SGQGroupBox,
    SGQPushButton,
    SGQMenu,
)
from .shotgrid_overlay_widget import ShotGridOverlayWidget


class ValidationDetailsWidget(SGQWidget):
    """
    Widget displays the individual data items that violate a validation rule.
    """

    # Emit signal to request to validate data according to the validateion rule
    request_validate_data = QtCore.Signal(ValidationRule)

    # Emit signal to request to fix data according to the validation rule
    request_fix_data = QtCore.Signal(ValidationRule)

    # Emit signals to indicate that an action is about to run, and when it has finished (this is useful to
    # show a busy indicator, if the operation takes some time)
    about_to_execute_action = QtCore.Signal(dict)
    execute_action_finished = QtCore.Signal(dict)

    def __init__(self, parent, pre_validate_before_actions=True):
        """
        Create the validation details widget.

        :param parent: The parent widget
        :type parent: QtGui.QWidget
        :param pre_validate_before_actions: True will run validation before executing actions
            so that the action callback acts on the most up to date error data. Default True. Default True.
        :type pre_validate_before_actions: bool
        """

        super(ValidationDetailsWidget, self).__init__(
            parent, layout_direction=QtGui.QBoxLayout.TopToBottom
        )

        self._rule = None
        self._details_item_model = ValidationRuleDetailsModel(self)
        self._show_description = True
        self._pre_validate_before_actions = pre_validate_before_actions

        self._setup_ui()
        self._connect_signals()

    #########################################################################################################
    # Properties

    @property
    def rule(self):
        """Get the validation rule that this details widget displays data for."""
        return self._rule

    @property
    def show_description(self):
        """
        Get or set the flag indicating to display the validation rule description in the details text.
        """
        return self._show_description

    @show_description.setter
    def show_description(self, show):
        self._show_description = show

    @property
    def pre_validate_before_actions(self):
        """
        Get or set the property that decides if validation is ran before executing actions
        on the current affected (error) objects.
        """
        return self._pre_validate_before_actions

    @pre_validate_before_actions.setter
    def pre_validate_before_actions(self, pre_validate):
        self._pre_validate_before_actions = pre_validate

    ######################################################################################################
    # Public methods

    def set_data(self, rule):
        """
        Set up the details data for the given validation rule.

        :param rule: The validation rule that the details is showing information for.
        :type rule: ValidationRule
        """

        self._rule = rule
        self.refresh()

    def refresh(self):
        """
        Refresh the current data in the widget.
        """

        if not self.rule:
            # No data to refresh
            return

        #
        # Set up details info
        #
        self._details.setTitle(self.rule.name)

        dependencies_names = self.rule.get_dependency_names()
        if dependencies_names:
            dependencies_text = (
                "Dependencies that will run with this fix:<ul>{deps}</ul>".format(
                    deps="".join(["<li>{}</li>".format(d) for d in dependencies_names])
                )
            )
        else:
            dependencies_text = "No dependencies."

        description = "<html>{desc}{space}{dependencies}</html>".format(
            desc=self.rule.description if self.show_description else "",
            space="<br/><br/>" if self.show_description and dependencies_text else "",
            dependencies=dependencies_text,
        )
        self._details_description.setText(description)

        #
        # Set up the details view
        #
        if self.rule.manual:
            # No details list view for manual rules
            self._details_item_view.hide()
        else:
            # Show the details list view and initialze the model data to display in the view
            self._details_item_view.show()
            self._details_item_model.initialize_data(self.rule.errors)

        #
        # Set up details action items
        #
        self._details_toolbar.clear()
        self._details_toolbar.add_stretch()

        # Add check action
        if self.rule.check_func is not None:
            name = self.rule.check_name

            # Check if the rule has already run its validation once, if so, modify the name to
            # prepend "Re", e.g. Validate -> Revalidate
            if self.rule.valid is not None:
                name = "Re{name}".format(name=name.lower())

            check_button = SGQPushButton(name, self._details_toolbar)

            check_button.clicked.connect(self._request_validate_rule)
            self._details_toolbar.add_widget(check_button)

        # Add fix action
        if self.rule.fix_func is not None:
            name = self.rule.fix_name
            fix_button = SGQPushButton(name, self._details_toolbar)

            fix_button.clicked.connect(self._request_fix_rule)
            self._details_toolbar.add_widget(fix_button)

        # Add generic actions
        for rule_action in self.rule.actions:
            action_cb = rule_action.get("callback")
            if not action_cb:
                continue

            button = SGQPushButton(rule_action["name"], self._details_toolbar)
            button.clicked.connect(
                lambda checked=False, a=rule_action: self._execute_action(a)
            )
            self._details_toolbar.add_widget(button)

        #
        # Show/hide the overlay message
        #
        if self.rule.errors or self.rule.manual:
            self._details_item_view_overlay.hide()
        else:
            text = None
            warnings = None

            if self.rule.valid is None:
                # Rule has not executed validate or fix yet
                if self.rule.check_func is not None and self.rule.fix_func is not None:
                    text = "Click {} or {} to see details.".format(
                        self.rule.check_name,
                        self.rule.fix_name,
                    )
                elif self.rule.check_func is not None:
                    text = "Click {} to see details.".format(self.rule.check_name)
                elif self.rule.fix_func is not None:
                    text = "Click {} to see details.".format(self.rule.fix_name)
            elif self.rule.valid:
                # Rule was validated and it succeedederrors
                text = "Success! No errors found."
            else:
                # Rule was validated and it failed but did not report any error items.
                # Show the rule's error message.
                error_messages = self.rule.get_error_messages()
                if error_messages:
                    text = "<span style='color:#EB5555;'>{}</span>".format(
                        "<br/><br/>".join(error_messages)
                    )

            warning_messages = self.rule.get_warning_messages()
            if warning_messages:
                warnings = "<span style='color:#FBB549;'>{}</span>".format(
                    "<br/><br/>".join(warning_messages)
                )

            self._details_item_view_overlay.show_message(title=text, details=warnings)

    ######################################################################################################
    # Protected methods

    def _setup_ui(self):
        """
        Set up the widget UI.

        This should be called once when creating the widget.
        """

        self._details = SGQGroupBox(self)
        self._details.setMinimumWidth(200)
        self._details.setSizePolicy(
            QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        )
        self._details_description = SGQLabel(self._details)
        self._details_description.setWordWrap(True)
        details_vlayout = QtGui.QVBoxLayout()
        details_vlayout.addWidget(self._details_description)
        self._details.setLayout(details_vlayout)

        self._details_toolbar = SGQWidget(self)

        self._details_item_view = GroupedItemView(self)
        self._details_item_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._details_item_view.setMouseTracking(True)
        self._details_item_view.setSelectionMode(
            QtGui.QAbstractItemView.SingleSelection
        )
        self._details_item_view.setModel(self._details_item_model)
        self._details_view_item_delegate = self._create_delegate()
        self._details_item_view_overlay = ShotGridOverlayWidget(self._details_item_view)
        self._details_item_view_overlay.title_word_wrap = True

        self.layout().setContentsMargins(10, 0, 0, 0)
        self.add_widgets(
            [self._details, self._details_toolbar, self._details_item_view]
        )

    def _connect_signals(self):
        """
        Set up and connect signal slots between widgets.

        This should be called once when creating the widget.
        """

        self._details_item_view.customContextMenuRequested.connect(
            self._on_details_item_context_menu_requested
        )
        self._details_item_view.doubleClicked.connect(
            self._on_details_item_double_clicked
        )

    def _create_delegate(self):
        """
        Create the delegate for the details item view and set it.
        """

        delegate = ViewItemDelegate(self._details_item_view)
        delegate.item_padding = ViewItemDelegate.Padding(0, 0, 0, 0)
        delegate.text_padding = ViewItemDelegate.Padding(10, 10, 10, 10)
        delegate.text_rect_valign = ViewItemDelegate.CENTER

        delegate.header_role = ValidationRuleDetailsModel.VIEW_ITEM_HEADER_ROLE
        delegate.subtitle_role = ValidationRuleDetailsModel.VIEW_ITEM_SUBTITLE_ROLE
        delegate.text_role = ValidationRuleDetailsModel.VIEW_ITEM_TEXT_ROLE
        delegate.separator_role = ValidationRuleDetailsModel.VIEW_ITEM_SEPARATOR_ROLE

        # Action button - convenience button for the first button that appears in the item's actions list
        delegate.add_action(
            {
                "type": ViewItemAction.TYPE_PUSH_BUTTON,
                "padding": 2,
                "get_data": self._get_details_item_data,
                "callback": self._details_item_action_callback,
            },
            ViewItemDelegate.RIGHT,
        )
        # Action button for footer item to show more/less items. Button is centered and spans width of row.
        delegate.add_action(
            {
                "type": ViewItemAction.TYPE_PUSH_BUTTON,
                "show_always": True,
                "padding": 0,
                "features": QtGui.QStyleOptionButton.Flat,
                "get_data": get_details_item_show_more_data,
                "callback": details_item_show_more_callback,
            },
            ViewItemDelegate.CENTER,
        )

        self._details_item_view.setItemDelegate(delegate)
        return delegate

    def _show_context_menu(self, widget, pos):
        """
        Show a context menu for the selected items.

        :param widget: The source widget.
        :type widget: QtGui.QWidget
        :param pos: The position for the context menu relative to the source widget.
        :type pos: QtCore.QPoint
        """

        selection_model = self._details_item_view.selectionModel()
        if not selection_model:
            return

        indexes = selection_model.selectedIndexes()
        if not indexes or len(indexes) > 1:
            return

        index = indexes[0]
        rule_model_item = index.model().itemFromIndex(index)
        rule_actions = self._get_details_item_actions(rule_model_item)

        actions = []
        for rule_action in rule_actions:
            action = QtGui.QAction(rule_action["name"])
            action.triggered.connect(
                lambda checked=False, a=rule_action: self._execute_item_action(a)
            )
            actions.append(action)

        menu = SGQMenu(self)
        menu.addActions(actions)
        pos = widget.mapToGlobal(pos)
        menu.exec_(pos)

    def _get_details_item_actions(self, index_or_item):
        """
        Get the list of actions for the details item.

        :param index_or_item: The model index or item of the details item.
        :type index_or_item: QModelIndex | QStandardItem

        :return: The list of actions for the details item.
        :rtype: list<dict>
        """

        if not self._rule or not index_or_item:
            return []

        item_id = index_or_item.data(ValidationRuleDetailsModel.DETAILS_ITEM_ID_ROLE)
        if not item_id:
            return

        actions = []
        for action in self._rule.item_actions:
            action["kwargs"] = {"errors": [item_id]}
            actions.append(action)
        return actions

    def _get_details_item_first_action(self, index):
        """
        Get the actions for the details item that corresponds to the given index, and return the
        first action in the list.

        :param index: The details item index.
        :type index: QModelIndex

        :return: The first action for the details item.
        :rtype: dict
        """

        actions = self._get_details_item_actions(index)
        if not actions:
            return {}

        return actions[0]

    def _execute_details_item_first_action(self, index):
        """
        Get the actions for the details item that corresponds to the given index, and execute the
        first action in the list.

        :param index: The details item index.
        :type index: QModelIndex
        """

        action = self._get_details_item_first_action(index)
        return self._execute_item_action(action)

    def _execute_action(self, action):
        """
        Execute the action.

        This action is applied to all details items.

        Get the data from the action to execute it. Emit signals to indicate when the action is about to run
        and after it has finished.

        :parm action: The action to execute.
        :type action: dict

        :return: The value returned by the action.
        :rtype: any
        """

        if not action:
            return None

        callback_fn = action.get("callback")
        if not callback_fn:
            return None

        kwargs = action.get("kwargs", {})
        kwargs["errors"] = (
            self.rule.get_errors()
            if self.pre_validate_before_actions
            else self.rule.errors
        )

        self.about_to_execute_action.emit(action)
        result = callback_fn(**kwargs)
        self.execute_action_finished.emit(action)

        return result

    def _execute_item_action(self, action):
        """
        Execute the item action.

        This action is applied to a single details item.

        Get the data from the action to execute it. Emit signals to indicate when the action is about to run
        and after it has finished.

        :parm action: The item action to execute.
        :type action: dict

        :return: The value returned by the item action.
        :rtype: any
        """

        if not action:
            return None

        callback_fn = action.get("callback")
        if not callback_fn:
            return None

        kwargs = action.get("kwargs", {})

        self.about_to_execute_action.emit(action)
        result = callback_fn(**kwargs)
        self.execute_action_finished.emit(action)

        return result

    ######################################################################################################
    # Callback methods

    def _on_details_item_context_menu_requested(self, pos):
        """
        Callback triggered when an error item from the view has been right-clicked.

        :param pos: The mouse position, relative to the sender (widget), captured when triggering this
            callback.
        :type pos: QtCore.QPoint
        """

        self._show_context_menu(self.sender(), pos)

    def _on_details_item_double_clicked(self, index):
        """
        Callback triggered when an error item from the view has been right-clicked.

        :param index: The index the mouse double-clicked on.
        :type index: QModelIndex
        """

        self._execute_details_item_first_action(index)

    def _request_validate_rule(self):
        """
        Request to execute the rule check function.

        :param rule: The rule to execute the check function for
        :type rule: ValidationRule
        """

        self.request_validate_data.emit(self.rule)

    def _request_fix_rule(self):
        """
        Request to execute the rule fix function.

        :param rule: The rule to execute the fix function for
        :type rule: ValidationRule
        """

        self.request_fix_data.emit(self.rule)

    ######################################################################################################
    # ViewItemDelegate callback functions

    def _get_details_item_data(self, parent, index):
        """
        Callback function triggered by the ViewItemDelegate.

        Get the data for displaying the details item action.

        :param parent: The parent of the ViewItemDelegate which triggered this callback
        :type parent: QAbstractItemView
        :param index: The index the action is for.
        :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`

        :return: The data for the action and index.
        :rtype: dict (see the ViewItemAction class attribute `get_data` for more details)
        """

        action = self._get_details_item_first_action(index)

        if action:
            visible = True
            name = action["name"]
        else:
            visible = False
            name = ""

        return {"visible": visible, "name": name}

    def _details_item_action_callback(self, view, index, pos):
        """
        The details item action was triggered.

        Get the first action item in the actions list and execute it.

        :param view: The view the index belongs to.
        :type view: QAbstractItemView
        :param index: The index to act on
        :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`
        :param pos: The mouse position captured on triggered this callback
        :type pos: :class:`sgtk.platform.qt.QtCore.QPoint`
        """

        self._execute_details_item_first_action(index)


######################################################################################################
# ViewItemDelegate callback functions (independent of the ValidationDetailsWidget)
#


def get_details_item_show_more_data(parent, index):
    """
    Callback function triggered by the ViewItemDelegate.

    Get the data for displaying the footer action to show more items.

    :param parent: The parent of the ViewItemDelegate which triggered this callback
    :type parent: QAbstractItemView
    :param index: The index the action is for.
    :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`

    :return: The data for the action and index.
    :rtype: dict (see the ViewItemAction class attribute `get_data` for more details)
    """

    is_footer = index.data(ValidationRuleDetailsModel.IS_FOOTER_ROLE)

    if is_footer:
        visible = True
        name = index.data(ValidationRuleDetailsModel.FOOTER_TEXT_ROLE)
    else:
        visible = False
        name = ""

    return {"visible": visible, "name": name, "width": "100%"}


def details_item_show_more_callback(view, index, pos):
    """
    The details item action was triggered.

    Show more items in the view, if not all are currently displayed.

    :param view: The view the index belongs to.
    :type view: QAbstractItemView
    :param index: The index to act on
    :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`
    :param pos: The mouse position captured on triggered this callback
    :type pos: :class:`sgtk.platform.qt.QtCore.QPoint`
    """

    if not index:
        return

    if index.data(ValidationRuleDetailsModel.IS_FOOTER_ROLE):
        index.model().toggle_display_items()
