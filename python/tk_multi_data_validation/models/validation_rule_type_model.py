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

from ..api.data.validation_rule_type import ValidationRuleType
from ..utils.framework_qtwidgets import ViewItemRolesMixin
from ..utils.framework_qtwidgets import SGQIcon


class ValidationRuleTypeModel(QtGui.QStandardItemModel, ViewItemRolesMixin):
    """
    A model to manage validaiton rule types data.
    """

    # Additional data roles defined for the model
    _BASE_ROLE = QtCore.Qt.UserRole + 1
    (
        RULE_TYPE_ROLE,
        RULE_TYPE_ID_ROLE,
        RULE_TYPE_NAME_ROLE,
        RULE_TYPE_ICON_ROLE,
        RULE_TYPE_STATUS_ROLE,
        RULE_TYPE_STATUS_ICON_ROLE,
        CHECKBOX_ICON_ROLE,  # The icon used to display a checkbox for this rule type
        NEXT_AVAILABLE_ROLE,  # Keep track of the next available custome role. Insert new roles above.
    ) = range(_BASE_ROLE, _BASE_ROLE + 8)

    # Status to indicate if validation state for this rule type
    (
        RULE_TYPE_STATUS_OK,
        RULE_TYPE_STATUS_INCOMPLETE,
        RULE_TYPE_STATUS_ERROR,
    ) = range(3)

    #
    # Signals
    #
    # Emit when the a rule type item check state has changed
    rule_type_check_state_changed = QtCore.Signal(
        ValidationRuleType, QtCore.Qt.CheckState
    )

    class ValidationRuleTypeModelItem(QtGui.QStandardItem):
        """
        A validation rule type item in the ValidationRuleTypeModel.
        """

        def __init__(self, rule_type):
            """
            Initialize the rule type item data.

            :param rule_type: The rule type data for this item.
            :type rule_type: ValidationRuleType
            """

            super(ValidationRuleTypeModel.ValidationRuleTypeModelItem, self).__init__()

            self._status = None
            self._check_state = None
            self._rule_type = rule_type

            if self._rule_type.sg_icon:
                if hasattr(SGQIcon, self._rule_type.sg_icon):
                    self._rule_type.icon = getattr(SGQIcon, self._rule_type.sg_icon)()

            if self._rule_type.sg_checkbox_icon:
                if hasattr(SGQIcon, self._rule_type.sg_checkbox_icon):
                    self._rule_type.checkbox_icon = getattr(
                        SGQIcon, self._rule_type.sg_checkbox_icon
                    )()

        def data(self, role):
            """
            Override the base class method.

            Get the data for the item for the specified role.

            :param role: The model role to get the data from.
            :type role: int

            :return: The data for the specified role.
            :rtype: any
            """

            if role == QtCore.Qt.DisplayRole:
                return self._rule_type.name

            if role == QtCore.Qt.BackgroundRole:
                return QtGui.QApplication.palette().midlight()

            if role == QtCore.Qt.CheckStateRole:
                return self._check_state

            if role == ValidationRuleTypeModel.RULE_TYPE_ROLE:
                return self._rule_type

            if role == ValidationRuleTypeModel.CHECKBOX_ICON_ROLE:
                if not self._rule_type:
                    return None
                return self._rule_type.checkbox_icon

            if role == ValidationRuleTypeModel.RULE_TYPE_ID_ROLE:
                if not self._rule_type:
                    return None
                return self._rule_type.id

            if role == ValidationRuleTypeModel.RULE_TYPE_NAME_ROLE:
                if not self._rule_type:
                    return None
                return self._rule_type.name

            if role == ValidationRuleTypeModel.RULE_TYPE_ICON_ROLE:
                if not self._rule_type:
                    return None
                return self._rule_type.icon

            if role == ValidationRuleTypeModel.RULE_TYPE_STATUS_ROLE:
                return self._status

            if role == ValidationRuleTypeModel.RULE_TYPE_STATUS_ICON_ROLE:
                return ValidationRuleTypeModel.get_status_icon(self._status)

            if role == ValidationRuleTypeModel.VIEW_ITEM_SEPARATOR_ROLE:
                return False

            return super(
                ValidationRuleTypeModel.ValidationRuleTypeModelItem, self
            ).data(role)

        def setData(self, value, role):
            """
            Override the base class method.

            Set the data for the item's role. Ensure to call emitDataChanged signal if the data has been
            updated, to notify any listeners.

            :param value: The data value to set for the item's role.
            :type value: any
            :param role: The model role
            :type role: int
            """

            if role == QtCore.Qt.CheckStateRole:
                self.set_check_state(value, emit_signal=True)
                self.emitDataChanged()

            elif role == ValidationRuleTypeModel.RULE_TYPE_STATUS_ROLE:
                self._status = value
                self.emitDataChanged()

            else:
                super(
                    ValidationRuleTypeModel.ValidationRuleTypeModelItem, self
                ).setData(value, role)

        def set_check_state(self, check_state, emit_signal=False):
            """
            Set the check state for the model item.

            :param check_state: The check state to update the item with.
            :type check_state: QtCore.Qt.CheckState | int
            :param emit_signal: True will emit the `rule_type_check_state_changed` signal.
            :type emit_signal: bool

            :raises TypeError: If `check_state` param is not valid
            """

            if isinstance(check_state, int):
                self._check_state = QtCore.Qt.CheckState(check_state)
            elif isinstance(check_state, QtCore.Qt.CheckState):
                self._check_state = check_state
            else:
                raise TypeError(
                    "Attempting to set check state with value type '{}'".format(
                        type(check_state)
                    )
                )

            if emit_signal:
                self.model().rule_type_check_state_changed.emit(
                    self._rule_type, self._check_state
                )

    ######################################################################################################
    # ValidationRuleTypeModel methods
    #

    def __init__(self, parent):
        """
        Create the ValidationRuleTypeModel.
        """

        QtGui.QStandardItemModel.__init__(self, parent)

        self._rule_types = {}

        # Add additional roles defined by the ViewItemRolesMixin class.
        self.NEXT_AVAILABLE_ROLE = self.initialize_roles(self.NEXT_AVAILABLE_ROLE)

    @classmethod
    def get_status_icon(cls, rule_type_status):
        """
        Get the icon for the rule type status.
        """

        # TODO Design icon
        # TODO let this icons be configurable
        return {
            cls.RULE_TYPE_STATUS_OK: SGQIcon.green_check_mark(),
            cls.RULE_TYPE_STATUS_INCOMPLETE: SGQIcon.lock(),
            cls.RULE_TYPE_STATUS_ERROR: SGQIcon.red_bullet(),
        }.get(rule_type_status)

    ######################################################################################################
    # Public methods
    #

    def clear(self):
        """
        Override the base class method.

        Clear the model and reset its properties.
        """

        self._rule_types = []

        super(ValidationRuleTypeModel, self).clear()

    def initialize_data(self, rule_types=None):
        """
        Initialize the model with the set of rule types given.

        The model will be cleared, all items removed, and new model items added for the rule types.

        :param rule_types: The set of rule types to initialize with
        :type rule_types: list<ValidationRuleType>
        """

        self.beginResetModel()

        if rule_types is None:
            # No rules provided, this will refresh the model. Save the current rules before resetting them.
            rule_types = self._rules_types

        self.clear()
        self._rule_types = rule_types

        for rule_type in self._rule_types:
            rule_model_item = self.ValidationRuleTypeModelItem(rule_type)
            self.invisibleRootItem().appendRow(rule_model_item)

        self.endResetModel()

    def get_item_for_rule_type(self, rule_type):
        """
        Get the model item for the rule type.

        :param rule_type: The rule type (id or object) to get the model item for.
        :type rule_type: int | ValidationRuleType

        :return: The model item found for the rule type. None if not found.
        :rtype: QtGui.QStandardItem
        """

        if isinstance(rule_type, int):
            role = self.RULE_TYPE_ID_ROLE
        elif isinstance(rule_type, ValidationRuleType):
            role = self.RULE_TYPE_ROLE
        else:
            raise TypeError("Invalid rule type '{}'".format(rule_type))

        rows = self.rowCount()
        for row in range(rows):
            item = self.item(row)
            if item.data(role) == rule_type:
                return item
        return None

    def set_check_state_for_rule_type(
        self, rule_type, check_state, emit_checked_signal=False
    ):
        """
        Get the model item for the rule type, and update its check state.

        :param rule_type: The rule type (id or object) to get the model item to update check state on.
        :type rule_type: int | ValidationRuleType
        :param emit_checked_signal: True will emit the the specific checked signal, else False will
            only emit the item's generic data change signal.
        :type emit_checked_signal: bool
        """

        model_item = self.get_item_for_rule_type(rule_type)
        if model_item:
            model_item.set_check_state(check_state, emit_checked_signal)
            model_item.emitDataChanged()

    def set_statuses(self, valid, errors, incomplete):
        """
        Iterate through all items in the model and update the status of each item.

        :param valid: The rule types (ids) thate are valid.
        :type valid: list<int>
        :param errors: The rule types (ids) thate are not valid (have errors).
        :type errors: list<int>
        :param incomplete: The rule types (ids) thate are neither valid or have errors.
        :type incomplete: list<int>
        """

        rows = self.rowCount()

        for row in range(rows):
            item = self.item(row)
            rule_type = item.data(self.RULE_TYPE_ID_ROLE)

            if rule_type in valid:
                status = self.RULE_TYPE_STATUS_OK
            elif rule_type in errors:
                status = self.RULE_TYPE_STATUS_ERROR
            elif rule_type in incomplete:
                status = self.RULE_TYPE_STATUS_INCOMPLETE
            else:
                status = None

            item.setData(status, self.RULE_TYPE_STATUS_ROLE)
