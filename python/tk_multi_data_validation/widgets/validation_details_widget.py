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

from ..data.validation_rule import ValidationRule
from ..models.validation_rule_details_model import ValidationRuleDetailsModel
from ..utils.framework_qtwidgets import (
    GroupedItemView,
    ViewItemDelegate,
    ViewItemAction,
    ShotgunOverlayWidget,
    SGQWidget,
)


class ValidationDetailsWidget(SGQWidget):
    """
    Widget displays the individual data items that violate a validation rule.
    """

    # Emit signal to request to validate data according to the validateion rule
    request_validate_data = QtCore.Signal(ValidationRule)

    # Emit signal to request to fix data according to the validation rule
    request_fix_data = QtCore.Signal(ValidationRule)

    def __init__(self, parent):
        """
        Create the validation details widget.

        :param parent: The parent widget
        :type parent: QtGui.QWidget
        """

        super(ValidationDetailsWidget, self).__init__(
            parent, layout_direction=QtGui.QBoxLayout.TopToBottom
        )

        self._rule = None
        self._details_item_model = ValidationRuleDetailsModel(self)

        self._setup_ui()
        self._connect_signals()

    #########################################################################################################
    # Properties

    @property
    def rule(self):
        """Get the validation rule that this details widget displays data for."""
        return self._rule

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

        if self.rule.dependencies:
            dependencies_text = "Dependencies (by ID):\n    "
            dependencies_text += "\n    ".join([d for d in self.rule.dependencies])
        else:
            dependencies_text = ""

        description = "{desc}\n\n{id}{space}{dependencies}".format(
            desc=self.rule.description,
            id="ID: {}".format(self.rule.id),
            space="\n\n" if dependencies_text else "",
            dependencies=dependencies_text,
        )
        self._details_description.setText(description)

        self._details_item_model.initialize_data(self.rule.errors)

        #
        # Set up details action items
        #
        self._details_toolbar.clear()
        self._details_toolbar.add_stretch()

        # Add check action
        if self.rule.check_func is not None:
            name = self.rule.check_name
            check_button = QtGui.QPushButton(name, self._details_toolbar)

            args = []
            kwargs = {}
            check_button.clicked.connect(self._request_validate_rule)
            self._details_toolbar.add_widget(check_button)

        # Add fix action
        if self.rule.fix_func is not None:
            name = self.rule.fix_name
            fix_button = QtGui.QPushButton(name, self._details_toolbar)

            args = []
            kwargs = {}
            fix_button.clicked.connect(self._request_fix_rule)
            self._details_toolbar.add_widget(fix_button)

        # Add generic actions
        for rule_action in self.rule.actions:
            action_cb = rule_action.get("callback")
            if not action_cb:
                continue

            args = rule_action.get("args", [])
            kwargs = {"errors": self.rule.get_error_item_ids()}
            button = QtGui.QPushButton(rule_action["name"], self._details_toolbar)
            button.clicked.connect(lambda cb=action_cb, a=args, k=kwargs: cb(*a, **k))
            self._details_toolbar.add_widget(button)

        #
        # Show/hide the overlay message
        #
        if self.rule.errors:
            self._details_item_view_overlay.hide()
        else:
            if self.rule.manual:
                self._details_item_view_overlay.show_message(
                    "Validation rule must be manually checked."
                )
            elif self.rule.valid is not None:
                self._details_item_view_overlay.show_message(
                    "Check passed. No errors found."
                )
            else:
                self._details_item_view_overlay.show_message(
                    "Run this Check to validate the scene data."
                )

    ######################################################################################################
    # Protected methods

    def _setup_ui(self):
        """
        Set up the widget UI.

        This should be called once when creating the widget.
        """

        self._details = QtGui.QGroupBox(self)
        self._details.setMinimumWidth(200)
        self._details.setMaximumWidth(400)
        self._details.setSizePolicy(
            QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        )
        self._details_description = QtGui.QLabel(self._details)
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
        self._details_item_view_overlay = ShotgunOverlayWidget(self._details_item_view)

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

    def _create_delegate(self):
        """
        Create the delegate for the details item view and set it.
        """

        delegate = ViewItemDelegate(self._details_item_view)
        delegate.text_padding = ViewItemDelegate.Padding(0, 7, 0, 7)

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
            callback = rule_action.get("callback")
            if not callback:
                continue

            args = rule_action.get("args", [])
            kwargs = rule_action.get("kwargs", {})

            action = QtGui.QAction(rule_action["name"])
            action.triggered.connect(lambda fn=callback, a=args, k=kwargs: fn(*a, **k))
            actions.append(action)

        menu = QtGui.QMenu(self)
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
            action["args"] = [item_id]
            actions.append(action)
        return actions

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

        actions = self._get_details_item_actions(index)

        if actions and actions[0]:
            visible = True
            name = actions[0]["name"]
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

        actions = self._get_details_item_actions(index)

        if not actions:
            return

        action = actions[0]
        if not action:
            return

        func = action.get("callback")
        if not func:
            return

        args = action.get("args", [])
        kwargs = action.get("kwargs", {})
        return func(*args, **kwargs)


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
