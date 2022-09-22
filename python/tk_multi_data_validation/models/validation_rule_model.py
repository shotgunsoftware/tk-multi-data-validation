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
from sgtk import TankError
from sgtk.platform.qt import QtGui, QtCore

from .validation_rule_type_model import ValidationRuleTypeModel
from ..api.data.validation_rule import ValidationRule
from ..utils.framework_qtwidgets import SGQIcon, ViewItemRolesMixin


class ValidationRuleModel(QtGui.QStandardItemModel, ViewItemRolesMixin):
    """A model to manage validation rules data."""

    UI_CONFIG_HOOK_PATH = "hook_ui_config"

    # Additional data roles defined for the model
    _BASE_ROLE = QtCore.Qt.UserRole + 1
    (
        CHECKBOX_ICON_ROLE,  # Icon used to draw the checkbox (e.g. for toggle buttons that Qt does not support)
        IS_GROUP_ITEM_ROLE,  # True if item is a group, else False
        IS_RULE_ITEM_ROLE,  # True if item represents a rule (non-group), else False
        GROUP_ITEM_ID_ROLE,  # The unique ID for the group
        RULE_TYPE_ID_ROLE,  # The rule type ID for the item
        RULE_TYPE_ROLE,  # The rule type object for the item
        RULE_ITEM_ROLE,  # The rule object for this item
        RULE_ITEMS_ROLE,  # The rule objects for this group item
        RULE_ITEM_ID_ROLE,  # The ID for the rule object (only if RULE_ITEM_ROLE is valid)
        RULE_CHECK_NAME_ROLE,  # The name for the validation operation of the rule(s)
        RULE_CHECK_FUNC_ROLE,  # The validation function for the rule(s)
        RULE_FIX_NAME_ROLE,  # The name of the fix operation of the rule(s)
        RULE_FIX_FUNC_ROLE,  # The fix function for the rule(s)
        RULE_VALIDATION_RAN,  # False if the rule check function has never been executed, else True
        RULE_FIX_RAN,  # False if the rule fix function has never been executed, else True
        RULE_VALID_ROLE,  # True if the last time the rule was validated, it was successful
        RULE_HAS_ERROR_ROLE,  # True if the last time the rule was validated, it was not successful
        RULE_ACTIONS_ROLE,  # Action items that can be executed against the rule
        RULE_ERROR_ITEMS_ROLE,  # The data that is found to have validation errors
        RULE_MANUAL_CHECK_STATE_ROLE,  # True if the rule is a manual check
        RULE_STATUS_ICON_ROLE,  # The status icon for the current state of the rule
        NEXT_AVAILABLE_ROLE,  # Keep track of the next available custome role. Insert new roles above.
    ) = range(_BASE_ROLE, _BASE_ROLE + 22)

    #
    # Signals
    #
    # Emit when the validation rule model item check state has changed
    rule_check_state_changed = QtCore.Signal(ValidationRule, QtCore.Qt.CheckState)

    class BaseModelItem(QtGui.QStandardItem):
        """The base model item class for QStandardItem objects in the ValidationRuleModel."""

        def data(self, role):
            """
            Override the :class:`sgtk.platform.qt.QtGui.QStandardItem` method.

            Return the data for the item for the specified role. This method will look up the
            callback function set up for the given role, and call that function to retrieve
            the data for the role. See the ValidationRuleModel constructor for the set up of
            the data role to callback function, using the ``role_methods`` property.

            :param role: The :class:`sgtk.platform.qt.QtCore.Qt.ItemDataRole` role.
            :return: The data for the specified roel.
            """

            # Check if the model has a method defined for retrieving the item data for this role.
            data_method = self.model().get_method_for_role(role)

            if data_method:
                try:
                    return data_method(self.index())
                except TypeError as error:
                    raise TankError(
                        "Failed to execute the method defined to retrieve item data for role `{role}`.\nError: {msg}".format(
                            role=role, msg=error
                        )
                    )

            # Default to the base implementation
            return super(ValidationRuleModel.BaseModelItem, self).data(role)

    class ValidationRuleGroupModelItem(BaseModelItem):
        """A group header item for a validation rule in the ValidationRulemodel."""

        def __init__(self, group_id, group_name):
            """
            Create the ValidationRuleGroupModelItem.

            :param group_id: The unique id for this group item.
            :type group_id: str
            :param group_name: The display name for this group
            :type group_name: str
            :param args: The arguments list to pass to the base QtGui.QStandardItem class.
            :type args: list
            :param kwargs: The keyword arguments dict to pass to the base QtGui.QStandardItem class.
            :type kwargs: dict
            """

            super(ValidationRuleModel.ValidationRuleGroupModelItem, self).__init__()

            self._id = group_id
            self._name = group_name

        def data(self, role):
            """
            Override the :class:`sgtk.platform.qt.QtGui.QStandardItem` method.

            Return the data for the item for the specified role.

            NOTE: data for roles may be retrieved by the function set up by the
            ``role_methods`` property. See the ValidationRuleModel constructor for which roles
            have a function set up to retrieve its data. This is to support customizing the
            data returned for a model role by using a hook method.

            :param role: The :class:`sgtk.platform.qt.QtCore.Qt.ItemDataRole` role.
            :return: The data for the specified roel.
            """

            if role == QtCore.Qt.DisplayRole:
                return self._name

            if role == ValidationRuleModel.IS_GROUP_ITEM_ROLE:
                return True

            if role == ValidationRuleModel.GROUP_ITEM_ID_ROLE:
                return self._id

            if role == ValidationRuleModel.IS_RULE_ITEM_ROLE:
                return False

            if role == ValidationRuleModel.RULE_ITEMS_ROLE:
                return self._get_rules()

            if role == ValidationRuleModel.RULE_CHECK_NAME_ROLE:
                return "Validate {}".format(self._name)

            if role == ValidationRuleModel.RULE_FIX_NAME_ROLE:
                return "Fix {}".format(self._name)

            if role == ValidationRuleModel.RULE_VALIDATION_RAN:
                # Group items say validation has already ran if any single child item
                # validation has executed
                for row in range(self.rowCount()):
                    child_item = self.child(row)
                    if child_item.data(ValidationRuleModel.RULE_VALIDATION_RAN):
                        return True
                return False

            if role == ValidationRuleModel.VIEW_ITEM_HEADER_ROLE:
                return self._name

            if role == ValidationRuleModel.VIEW_ITEM_SUBTITLE_ROLE:
                num_errors = 0
                count = self.rowCount()
                for row in range(count):
                    child_item = self.child(row)
                    if child_item:
                        executed = child_item.data(
                            ValidationRuleModel.RULE_VALIDATION_RAN
                        )
                        if executed:
                            valid = child_item.data(ValidationRuleModel.RULE_VALID_ROLE)
                            if not valid:
                                num_errors += 1

                if num_errors:
                    return "{} ERROR{}".format(
                        num_errors, "S" if num_errors > 1 else ""
                    )

                return "{} TOTAL".format(count)

            if role == ValidationRuleModel.VIEW_ITEM_SEPARATOR_ROLE:
                return True

            if role == ValidationRuleModel.VIEW_ITEM_HEIGHT_ROLE:
                # Fix the group header row height to a single line
                return 20

            if role == ValidationRuleModel.VIEW_ITEM_LOADING_ROLE:
                # Do not show a loading icon for the group item
                return False

            return super(ValidationRuleModel.ValidationRuleGroupModelItem, self).data(
                role
            )

        def _get_rules(self):
            """
            Return the list of validation rules of the child items in this grouping.

            :return: The list of validation rule objects.
            :rtype: list<ValidationRule>
            """

            rules = []

            for row in range(self.rowCount()):
                child = self.child(row)
                rules.append(child.data(ValidationRuleModel.RULE_ITEM_ROLE))

            return rules

    class ValidationRuleModelItem(BaseModelItem):
        """An item for validation rule data in the ValidationRuleModel."""

        def __init__(self, rule=None):
            """
            Create the ValidationRuleModelItem.

            :param rule: The rule that this item represents
            :type rule: ValidationRule
            """

            # Call the base QStandardItem constructor
            super(ValidationRuleModel.ValidationRuleModelItem, self).__init__()

            # Initialize our file mode item data
            self._rule = rule

            self._checkbox_icon = None
            if self._rule.type and self._rule.type.sg_checkbox_icon:
                if hasattr(SGQIcon, self._rule.type.sg_checkbox_icon):
                    self._checkbox_icon = getattr(
                        SGQIcon, self._rule.type.sg_checkbox_icon
                    )()

            # UI properties
            self._is_loading = False

        def data(self, role):
            """
            Override the :class:`sgtk.platform.qt.QtGui.QStandardItem` method.

            Return the data for the item for the specified role.

            NOTE: data for roles may be retrieved by the function set up by the
            ``role_methods`` property. See the ValidationRuleModel constructor for which roles
            have a function set up to retrieve its data. This is to support customizing the
            data returned for a model role by using a hook method.

            :param role: The :class:`sgtk.platform.qt.QtCore.Qt.ItemDataRole` role.
            :return: The data for the specified role.
            """

            if role == QtCore.Qt.CheckStateRole:
                return QtCore.Qt.Checked if self._rule.checked else QtCore.Qt.Unchecked

            if role == ValidationRuleModel.VIEW_ITEM_SEPARATOR_ROLE:
                return False

            if role == ValidationRuleModel.VIEW_ITEM_LOADING_ROLE:
                return self._is_loading

            if role == ValidationRuleModel.VIEW_ITEM_HEIGHT_ROLE:
                return None

            if role == ValidationRuleModel.IS_GROUP_ITEM_ROLE:
                return False

            if role == ValidationRuleModel.IS_RULE_ITEM_ROLE:
                return True

            if role == ValidationRuleModel.RULE_ITEM_ROLE:
                return self._rule

            if role == ValidationRuleModel.RULE_ERROR_ITEMS_ROLE:
                if not self._rule:
                    return []
                return self._rule.errors

            if role == ValidationRuleModel.RULE_ITEM_ID_ROLE:
                if not self._rule:
                    return None
                return self._rule.id

            if role == ValidationRuleModel.VIEW_ITEM_HEADER_ROLE:
                if not self._rule:
                    return None
                return "<b>{}</b>".format(self._rule.name)

            if role == ValidationRuleModel.VIEW_ITEM_TEXT_ROLE:
                if not self._rule:
                    return None

                if self._rule.optional and not self._rule.checked:
                    return "<div style='line-height:1.2;'>{}</div>".format(
                        self._rule.description
                    )

                lines = []
                error_messages = self._rule.get_error_messages()
                if (
                    self.data(ValidationRuleModel.RULE_HAS_ERROR_ROLE)
                    and error_messages
                ):
                    lines.append(
                        "<span style='color:#EB5555;'>{}</span>".format(
                            "<br/>".join(error_messages)
                        )
                    )

                warning_messages = self._rule.get_warning_messages()
                if warning_messages:
                    lines.append(
                        "<span style='color:#FBB549;'>{}</span>".format(
                            "<br/>".join(warning_messages)
                        )
                    )
                lines.append(self._rule.description)
                return "<div style='line-height:1.2;'>{}</div>".format(
                    "<br/>".join(lines)
                )

            if role == ValidationRuleModel.RULE_TYPE_ID_ROLE:
                if not self._rule:
                    return None
                return self._rule.type.id

            if role == ValidationRuleModel.RULE_TYPE_ROLE:
                if not self._rule:
                    return None
                return self._rule.type

            if role == ValidationRuleModel.RULE_CHECK_NAME_ROLE:
                if not self._rule:
                    return None
                if self._rule.manual:
                    return None
                return self._rule.check_name

            if role == ValidationRuleModel.RULE_CHECK_FUNC_ROLE:
                if not self._rule:
                    return None
                return self._rule.check_func

            if role == ValidationRuleModel.RULE_FIX_NAME_ROLE:
                if not self._rule:
                    return None
                return self._rule.fix_name

            if role == ValidationRuleModel.RULE_FIX_FUNC_ROLE:
                if not self._rule:
                    return None
                return self._rule.fix_func

            if role == ValidationRuleModel.RULE_VALIDATION_RAN:
                if not self._rule:
                    return None
                return self._rule.valid is not None

            if role == ValidationRuleModel.RULE_FIX_RAN:
                if not self._rule:
                    return None
                return self._rule.fix_executed

            if role == ValidationRuleModel.RULE_VALID_ROLE:
                if not self._rule:
                    return None
                return self._rule.valid

            if role == ValidationRuleModel.RULE_HAS_ERROR_ROLE:
                if not self._rule:
                    return False

                if self._rule.optional and not self._rule.checked:
                    # Optional rules that are not active do not have errors
                    return False

                if not self.data(ValidationRuleModel.RULE_VALIDATION_RAN):
                    # Do not report errors until validation has run at least once
                    return False

                if not self._rule.manual and not self._rule.check_func:
                    # Special case for rules that do not have a check func, but have a fix func:
                    # Show as error if its fix has never been executed or there are error messages
                    # set from running the fix
                    if not self._rule.fix_executed:
                        return True

                    error_messages = self._rule.get_error_messages()
                    if error_messages:
                        return True

                    # Found no errors
                    return False

                if self._rule.manual and not self._rule.manual_checked:
                    # Manual rules that are not checked are an error
                    return True

                # Rule is active and has been executed, check its valid status.
                return not self.data(ValidationRuleModel.RULE_VALID_ROLE)

            if role == ValidationRuleModel.RULE_STATUS_ICON_ROLE:
                if not self._rule:
                    return None

                if self._rule.optional and not self._rule.checked:
                    # Optional rules that are not active do not have errors
                    return None

                if not self.data(ValidationRuleModel.RULE_VALIDATION_RAN):
                    # Not status to report if the rule has not been validated yet
                    return None

                # TODO revist this special case handling for rules that do not have an automated validate
                # function, but do have an autoamted fix (semi-automated)
                if not self._rule.manual and not self._rule.check_func:
                    if self._rule.fix_executed:
                        return self.model().ok_status_icon
                    return self.model().warning_status_icon

                if self._rule.manual:
                    if self._rule.manual_checked:
                        return self.model().ok_status_icon
                    return self.model().warning_status_icon

                if self.data(ValidationRuleModel.RULE_VALID_ROLE):
                    return self.model().ok_status_icon

                # Check for errors after warning and ok status has been checked
                if self.data(ValidationRuleModel.RULE_HAS_ERROR_ROLE):
                    return self.model().error_status_icon

                return None

            if role == ValidationRuleModel.CHECKBOX_ICON_ROLE:
                return self._checkbox_icon

            if role == ValidationRuleModel.RULE_ACTIONS_ROLE:
                if not self._rule:
                    return None
                return self._rule.get_actions_data()

            if role == ValidationRuleModel.RULE_MANUAL_CHECK_STATE_ROLE:
                if not self._rule:
                    return None
                return (
                    QtCore.Qt.Checked
                    if self._rule.manual_checked
                    else QtCore.Qt.Unchecked
                )

            return super(ValidationRuleModel.ValidationRuleModelItem, self).data(role)

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
                self._rule.checked = bool(value == QtCore.Qt.Checked)
                self.emitDataChanged()

                # Emit signal indicating the updated check state for this rule type group
                check_state = self.model().get_check_state_for_rule_type(
                    self._rule.type
                )
                self.model().rule_check_state_changed.emit(self._rule, check_state)

            if role == ValidationRuleModel.RULE_MANUAL_CHECK_STATE_ROLE:
                self._rule.manual_checked = bool(value == QtCore.Qt.Checked)
                self.emitDataChanged()

            if role == ValidationRuleModel.RULE_ITEM_ROLE:
                self._rule = value
                self.emitDataChanged()

            elif role == ValidationRuleModel.VIEW_ITEM_LOADING_ROLE:
                self._is_loading = value
                self.emitDataChanged()

            else:
                super(ValidationRuleModel.ValidationRuleModelItem, self).setData(
                    value, role
                )

    ######################################################################################################
    # ValidationRuleModel methods
    #

    def __init__(self, parent, group_by=None, bundle=None):
        """
        Create the ValidationRuleModel.

        :param parent: The parent widget of this model
        :type parent: QtGui.QWidget
        :param group_by: (optional) The field to group the model items by
        :type group_by: str
        """

        # We need to call the base class constructor explicitly (cannot use super) since the
        # class inherits multiple base classes
        QtGui.QStandardItemModel.__init__(self, parent)

        self._group_by = group_by
        self._rules = []
        self._hierarchical = True

        # Status icons
        self._error_status_icon = SGQIcon.validation_error()
        self._warning_status_icon = SGQIcon.validation_warning()
        self._ok_status_icon = SGQIcon.validation_ok()

        # Add additional roles defined by the ViewItemRolesMixin class.
        self.NEXT_AVAILABLE_ROLE = self.initialize_roles(self.NEXT_AVAILABLE_ROLE)

        bundle = bundle or sgtk.platform.current_bundle()
        ui_config_hook_path = bundle.get_setting(self.UI_CONFIG_HOOK_PATH)
        ui_config_hook = bundle.create_hook_instance(ui_config_hook_path)

        # Create a mapping of model item data roles to the method that will be called to retrieve
        # the data for the item. The methods defined for each role must accept one paramete, which
        # is the item index (QModelIndex) that the data is being retrieved for.
        # NOTE the model item ``data`` methods should not return a value for the roles in this
        # mapping, unless they intend to override these defined callbacks
        self.role_methods = {
            QtCore.Qt.BackgroundRole: ui_config_hook.get_rule_item_background_color,
        }

    ######################################################################################################
    # Properties
    #

    @property
    def rules(self):
        """Get the list of validation rules that this model represnets."""
        return self._rules

    @property
    def group_by(self):
        """Get or set the group by field to create rule groupings."""
        return self._group_by

    @group_by.setter
    def group_by(self, field):
        self._group_by = field
        self.initialize_data()

    @property
    def hierarchical(self):
        """Get or set the flag indicating if the model is hierarchical or not (e.g. flat)."""
        return self._hierarchical

    @hierarchical.setter
    def hierarchical(self, value):
        self._hierarchical = value

    @property
    def error_status_icon(self):
        """Get the error status icon."""
        return self._error_status_icon

    @property
    def warning_status_icon(self):
        """Get the warning status icon."""
        return self._warning_status_icon

    @property
    def ok_status_icon(self):
        """Get the ok status icon."""
        return self._ok_status_icon

    ######################################################################################################
    # Public methods
    #

    def destroy(self):
        """
        Override the base method.

        Clear the model before destroying it.
        """

        self.clear()

    def clear(self):
        """
        Override the base class method.

        Clear the model and reset its properties.
        """

        self._rules = []

        super(ValidationRuleModel, self).clear()

    def initialize_data(self, rules=None):
        """
        Initialize the model with the set of rules given.

        The model will be cleared, all items removed, and new model items added for the rules.

        :param rules: The set of rule to initialize with
        :type rules: list<ValidationRule>
        """

        self.beginResetModel()

        if rules is None:
            # No rules provided, this will refresh the model. Save the current rules before resetting them.
            rules = self._rules

        self.clear()
        self._rules = rules

        # Set up the groupings for hierarchical model mode
        if self.hierarchical and self.group_by:
            group_items = {r.get_data(self.group_by): None for r in self._rules}

            if None in group_items:
                # Create the "Ungrouped" item for any rules that may not define a grouping
                group_items[None] = ValidationRuleModel.ValidationRuleGroupModelItem(
                    None, ""
                )
        else:
            group_items = {}

        # Flag to indicate if there are ungrouped items to add to the model
        append_ungrouped_item = False

        for rule in self._rules:
            rule_model_item = ValidationRuleModel.ValidationRuleModelItem(rule)
            group_name = rule.get_data(self.group_by)

            if group_items:
                if group_name is None:
                    append_ungrouped_item = True

                rule_model_group_item = group_items.get(group_name)
                if rule_model_group_item:
                    rule_model_group_item.appendRow(rule_model_item)
                else:
                    group_item = ValidationRuleModel.ValidationRuleGroupModelItem(
                        group_name, group_name
                    )
                    group_items[group_name] = group_item
                    self.invisibleRootItem().appendRow(group_item)
                    group_item.appendRow(rule_model_item)

            else:
                # This rule does not have a group, add it to the root item.
                self.invisibleRootItem().appendRow(rule_model_item)

        if append_ungrouped_item:
            # There were ungrouped rules, add the "Ungrouped" group item to the model
            self.invisibleRootItem().appendRow(group_items[None])

        self.endResetModel()

    def emit_all_data_changed(self):
        """
        Emit the data changed signal for each item in the model.

        NOTE that using the model's dataChanged signal to emit one signal for all items does not seem to work
        as expected, so for now just emit the model item signal for each item.
        """

        rows = self.rowCount()
        for row in range(rows):
            model_item = self.item(row)
            model_item.emitDataChanged()
            row_count = model_item.rowCount()
            for child_row in range(row_count):
                child = model_item.child(child_row)
                child.emitDataChanged()

    def get_group_item_by_id(self, group_id):
        """
        Get the group header model item for the given group id.

        :param group_id: The id to get the group header item by.
        :type group_id: str

        :return: The group header item.
        :rtype: QtGui.QStandardItem
        """

        rows = self.rowCount()

        for row in range(rows):
            group_item = self.item(row)
            if group_id == group_item.data(ValidationRuleModel.GROUP_ITEM_ID_ROLE):
                return group_item

        return None

    ######################################################################################################
    # Methods iterating over items in the model assume that the model data structure is flat (single level
    # hierarchy) or two-level hierarchy (parent->child, does not go further nested than that)
    #
    def get_item_for_rule(self, rule):
        """
        Iterate over the model items to find the item representing the given rule.

        :param rule: The rule id to get the model item for.
        :type rule: int

        :return: The model item found for the rule. None if not found.
        :rtype: QtGui.QStandardItem
        """

        rows = self.rowCount()

        for row in range(rows):
            model_item = self.item(row)
            if model_item.data(
                ValidationRuleModel.IS_RULE_ITEM_ROLE
            ) and rule.id == model_item.data(ValidationRuleModel.RULE_ITEM_ID_ROLE):
                return model_item

            child_rows = model_item.rowCount()
            for child_row in range(child_rows):
                child_item = model_item.child(child_row)
                if child_item.data(
                    ValidationRuleModel.IS_RULE_ITEM_ROLE
                ) and rule.id == child_item.data(ValidationRuleModel.RULE_ITEM_ID_ROLE):
                    return child_item

        return None

    def get_errors(self):
        """
        Iterate over the model items to find all items with errors.

        :return: The list of items with errors.
        :rtype: list<QtGui.QStandardItem>
        """

        errors = []
        rows = self.rowCount()

        for row in range(rows):
            model_item = self.item(row)
            if model_item.data(
                ValidationRuleModel.IS_RULE_ITEM_ROLE
            ) and model_item.data(ValidationRuleModel.RULE_HAS_ERROR_ROLE):
                errors.append(model_item)

            child_rows = model_item.rowCount()
            for child_row in range(child_rows):
                child_item = model_item.child(child_row)
                if child_item.data(
                    ValidationRuleModel.IS_RULE_ITEM_ROLE
                ) and child_item.data(ValidationRuleModel.RULE_HAS_ERROR_ROLE):
                    errors.append(child_item)

        return errors

    def get_check_state_for_rule_type(self, rule_type):
        """
        Iterate over the model items to compute the check state for the rule type.

        The check state for the rule type is dependent on all ValidationRuleModelItem that are of the given
        rule type.

        The check state for the rule type will be checked if all ValidationRuleModelItem items with the rule
        type are checked, unchecked if not one item with the rule type is checked, and partially checked if
        some but not all the items are checked.

        :param rule_type: The rule type to get the check state for
        :type rule_type: ValidationRuleType
        :return: The check state for the rule type:
                    QtCore.Qt.Checked - all rules are checked for the rule type
                    QtCore.Qt.PartiallyChecked - some rules are checked for the rule type
                    QtCore.Qt.Unchecked - no rules are checked for the rule type
        :rtype: QtCore.Qt.CheckState
        """

        def get_check_status(model_item, rule_type, has_checked, has_unchecked):
            """
            Helper function to get the check status for the rule type.

            :param model_item: The model item that affects the checked status
            :type model_item: QtGui.QStandardItem
            :param rule_type: The rule type to get the checked status for
            :type rule_type: ValidationRuleType
            :param has_checked: True if another model item has already been processed that is checked, else
                no other model item has been processed yet that is checked.
            :type has_checked: bool
            :param has_unchecked: True if another model item has already been processed that is not checked,
                else no other model item has been processed yet that is not checked.
            :type has_unchecked: bool

            :return: A tuple containing (1) the updated has_checked value (2) the updated has_unchecked value
                (3) True if the checked status partial, else False
            """

            is_partial = None

            if not model_item.data(ValidationRuleModel.IS_RULE_ITEM_ROLE):
                return (has_checked, has_unchecked, is_partial)

            rule = model_item.data(ValidationRuleModel.RULE_ITEM_ROLE)
            if not rule:
                return (has_checked, has_unchecked, is_partial)

            if rule.type != rule_type:
                return (has_checked, has_unchecked, is_partial)

            checked = bool(
                model_item.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked
            )
            if checked:
                if has_unchecked:
                    is_partial = True
                has_checked = True
            else:
                if has_checked:
                    is_partial = True
                has_unchecked = True

            return (has_checked, has_unchecked, is_partial)

        has_checked = False
        has_unchecked = False
        rows = self.rowCount()

        for row in range(rows):
            model_item = self.item(row)
            has_checked, has_unchecked, is_partial = get_check_status(
                model_item, rule_type, has_checked, has_unchecked
            )
            if is_partial:
                return QtCore.Qt.PartiallyChecked

            child_rows = model_item.rowCount()
            for child_row in range(child_rows):
                child_item = model_item.child(child_row)
                has_checked, has_unchecked, is_partial = get_check_status(
                    child_item, rule_type, has_checked, has_unchecked
                )
                if is_partial:
                    return QtCore.Qt.PartiallyChecked

        # No partial check found, either all checked or all unchecked
        return QtCore.Qt.Checked if has_checked else QtCore.Qt.Unchecked

    def set_check_state_for_rule_type(
        self, rule_type, check_state, emit_checked_signal=False
    ):
        """
        Iterate over the model items to update ValidationRuleModelItem check states.

        :param rule_type: The type of rules to update
        :type rule_type: ValidationRuleType
        :param check_state: The check state to update the rule to
        :type check_state: QtCore.Qt.CheckState
        :param emit_checked_signal: True will emit the specific signal for check state changed.
            NOTE that the generic model item data changed signal will be emitted regardless.
        :type emit_checked_signal: bool
        """

        def update_check_state(model_item, rule_type, check_state, emit_checked_signal):
            """
            Helper function to update the check state for the model item.

            :param model_item: The model item to update
            :type model_item: QtGui.QStandardItem
            :param rule_type: Only model items with rule type will be updated.
            :type rule_type: ValidationRuleType
            :param check_state: The check state value to update to.
            :type check_state: QtCore.Qt.CheckState
            :param emit_checked_signal: True will emit signal specific to check state change.
            :type emit_checked_signal: bool
            """

            if not model_item.data(ValidationRuleModel.IS_RULE_ITEM_ROLE):
                return

            rule = model_item.data(ValidationRuleModel.RULE_ITEM_ROLE)
            if not rule:
                return

            if rule.type != rule_type:
                return

            if emit_checked_signal:
                model_item.setData(check_state, QtCore.Qt.CheckStateRole)
            else:
                rule.checked = bool(check_state == QtCore.Qt.Checked)
                model_item.emitDataChanged()

        rows = self.rowCount()

        for row in range(rows):
            model_item = self.item(row)
            update_check_state(model_item, rule_type, check_state, emit_checked_signal)

            child_rows = model_item.rowCount()
            for child_row in range(child_rows):
                child_item = model_item.child(child_row)
                update_check_state(
                    child_item, rule_type, check_state, emit_checked_signal
                )

    def get_status_for_rule_type(self, rule_type):
        """
        Iterate over the model items and compute the status for the rule type.

        The status is computed by checking each ValidationRuleModelItem:
            - An incomplete status is returned if any of the model items for the rule type have not been run
            - An error status is returend if all model items for the ruel have run, but not all passed
            - A success status is returend if all model items for the ruel have run and all passed

        :return: The rule type status:
                     ValidationRuleTypeModel.RULE_TYPE_STATUS_INCOMPLETE - not all rules have been checked
                     ValidationRuleTypeModel.RULE_TYPE_STATUS_ERROR - all rules checked but not all passed
                     ValidationRuleTypeModel.RULE_TYPE_STATUS_OK - all rules checked and passed
        :rtype: int
        """

        def get_status(model_item, rule_type):
            """
            Helper function to get the status for the rule type based on the model item.

            :param model_item: The model item that affects the status of the rule type
            :type model_item: QtGui.QStandardItem
            :param rule_type: Only model items with rule type will be checked.
            :type rule_type: ValidationRuleType

            :return: The status:
                ValidationRuleModelItem.RULE_TYPE_STATUS_INCOMPLETE - the rule was not checked but did not passed
                ValidationRuleModelItem.RULE_TYPE_STATUS_ERROR - the rule was checked but did not passed
                ValidationRuleModelItem.RULE_TYPE_STATUS_OK - the rule was checked and passed
            :rtype: int
            """

            if not model_item.data(ValidationRuleModel.IS_RULE_ITEM_ROLE):
                return None

            rule = model_item.data(ValidationRuleModel.RULE_ITEM_ROLE)
            if not rule:
                return None

            if rule.type != rule_type:
                return None

            if rule.optional and not rule.checked:
                # Optional checks that are not turned on are trivally OK
                return ValidationRuleTypeModel.RULE_TYPE_STATUS_OK

            executed = model_item.data(ValidationRuleModel.RULE_VALIDATION_RAN)
            if not executed:
                return ValidationRuleTypeModel.RULE_TYPE_STATUS_INCOMPLETE

            is_valid = model_item.data(ValidationRuleModel.RULE_VALID_ROLE)
            if not is_valid:
                return ValidationRuleTypeModel.RULE_TYPE_STATUS_ERROR

            return ValidationRuleTypeModel.RULE_TYPE_STATUS_OK

        has_errors = False
        rows = self.rowCount()

        for row in range(rows):
            model_item = self.item(row)
            status = get_status(model_item, rule_type)

            if status == ValidationRuleTypeModel.RULE_TYPE_STATUS_INCOMPLETE:
                # Incomplete status takes precedence - return immediately
                return status

            if status == ValidationRuleTypeModel.RULE_TYPE_STATUS_ERROR:
                has_errors = True

            child_rows = model_item.rowCount()
            for child_row in range(child_rows):
                child_item = model_item.child(child_row)
                status = get_status(child_item, rule_type)

                if status == ValidationRuleTypeModel.RULE_TYPE_STATUS_INCOMPLETE:
                    # Incomplete status takes precedence - return immediately
                    return status

                if status == ValidationRuleTypeModel.RULE_TYPE_STATUS_ERROR:
                    has_errors = True

        return (
            ValidationRuleTypeModel.RULE_TYPE_STATUS_ERROR
            if has_errors
            else ValidationRuleTypeModel.RULE_TYPE_STATUS_OK
        )

    def get_statuses_for_rule_type(self):
        """
        Iterate over the model items and compute the statuses for each rule type.

        :return: A tuple with
            (1) the set of rule types where all rules have been checked and are vald
            (2) the set of rule tyeps where all rules have been checked but some have errors
            (3) the set of rule tyeps where not all rules have been checked
        :rtype: tupel<set,set,set>
        """

        def update_status(model_item, all_types, incomplete, errors):
            """
            Helper function to update the status sets.

            :param model_item: The model item to update the status sets with.
            :type model_item: QtGui.QStandardItem
            :param all_types: The set of all validation rule types in the model.
            :type all_types: set<int>
            :param incomplete: The set of rule types that have rules that have not been checked yet.
            :type incomplete: set<int>
            :param errors: The set of rule types that have rules that have errors.
            :type errors: set<int>
            """

            if not model_item.data(ValidationRuleModel.IS_RULE_ITEM_ROLE):
                return

            rule = model_item.data(ValidationRuleModel.RULE_ITEM_ROLE)
            if not rule:
                return

            all_types.add(rule.type.id)

            if rule.optional and not rule.checked:
                # Optional checks that are not turned on are skipped
                return

            executed = model_item.data(ValidationRuleModel.RULE_VALIDATION_RAN)
            if not executed:
                incomplete.add(rule.type.id)
            else:
                is_valid = model_item.data(ValidationRuleModel.RULE_VALID_ROLE)
                if not is_valid:
                    errors.add(rule.type.id)

        all_types = set()
        errors = set()
        incomplete = set()
        rows = self.rowCount()

        for row in range(rows):
            model_item = self.item(row)
            update_status(model_item, all_types, incomplete, errors)

            child_rows = model_item.rowCount()
            for child_row in range(child_rows):
                child_item = model_item.child(child_row)
                update_status(child_item, all_types, incomplete, errors)

        valid = all_types - errors - incomplete
        return (valid, errors, incomplete)
