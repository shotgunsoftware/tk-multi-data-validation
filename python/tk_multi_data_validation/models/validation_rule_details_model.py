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

from ..utils.framework_qtwidgets import ViewItemRolesMixin


class ValidationRuleDetailsModel(QtGui.QStandardItemModel, ViewItemRolesMixin):
    """
    A model to manage validation rules data.
    """

    # Additional data roles defined for the model
    _BASE_ROLE = QtCore.Qt.UserRole + 1
    (
        IS_GROUP_ITEM_ROLE,
        IS_FOOTER_ROLE,
        FOOTER_TEXT_ROLE,
        DETAILS_ITEM_ID_ROLE,
        DISPLAY_NUM_ROLE,
        NEXT_AVAILABLE_ROLE,  # Keep track of the next available custome role. Insert new roles above.
    ) = range(_BASE_ROLE, _BASE_ROLE + 6)

    # The max number of items the model can display at a time. TODO handle large data sets with pagination
    MAX_DISPLAY_NUM = 150
    INCREMENT_DISPLAY_NUM = 150

    class ValidationRuleDetailsGroupModelItem(QtGui.QStandardItem):
        """
        A group header item for the ValidationRuleDetailsModel.
        """

        def __init__(self, text):
            """
            Create the ValidationRuleDetailsGroupModelItem.

            :param text: The text to display in the item
            :type text: str
            """

            super(
                ValidationRuleDetailsModel.ValidationRuleDetailsGroupModelItem, self
            ).__init__()

            self._text = text

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
                return self._text

            if role == ValidationRuleDetailsModel.IS_GROUP_ITEM_ROLE:
                return True

            if role == ValidationRuleDetailsModel.VIEW_ITEM_HEADER_ROLE:
                return self._text

            if role == ValidationRuleDetailsModel.VIEW_ITEM_SUBTITLE_ROLE:
                num_display = self.model().display_num
                num_total = len(self.model().details_items)
                if num_display < num_total:
                    return "SHOWING {displaying} OF {total}".format(
                        displaying=num_display, total=num_total
                    )

                return "{} Items".format(num_total)

            if role == ValidationRuleDetailsModel.VIEW_ITEM_SEPARATOR_ROLE:
                return True

            return super(
                ValidationRuleDetailsModel.ValidationRuleDetailsGroupModelItem, self
            ).data(role)

    class ValidationRuleDetailsModelItem(QtGui.QStandardItem):
        """
        A  model item in the ValidationRuleDetailsModel.
        """

        def __init__(self, details, is_footer=False):
            """
            Create a ValidationRuleDetailsModelItem.

            :param details: A dictionary containing data for details model item.
            :type details: dict

            **data dict format**
                id
                    :type: str
                    :description: The unique identifier for this details item.
                name
                    :type: str
                    :description: The display name for this details item.

            :param rule: The rule that this data item violates.
            :type rule: ValidationRule
            :param is_footer: Flag indicating if the model item is a special footer item.
            :type is_footer: bool
            """

            super(
                ValidationRuleDetailsModel.ValidationRuleDetailsModelItem, self
            ).__init__()

            self._details = details
            self._is_footer = is_footer

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
                return self._details.get("name")

            if role == ValidationRuleDetailsModel.VIEW_ITEM_HEADER_ROLE:
                return self._details.get("name")

            if role == ValidationRuleDetailsModel.VIEW_ITEM_SUBTITLE_ROLE:
                return None

            if role == ValidationRuleDetailsModel.VIEW_ITEM_TEXT_ROLE:
                return None

            if role == ValidationRuleDetailsModel.IS_GROUP_ITEM_ROLE:
                return False

            if role == ValidationRuleDetailsModel.IS_FOOTER_ROLE:
                return self._is_footer

            if role == ValidationRuleDetailsModel.DETAILS_ITEM_ID_ROLE:
                return self._details.get("id")

            if role == ValidationRuleDetailsModel.FOOTER_TEXT_ROLE:
                if self._is_footer:
                    return self.model().get_footer_text()

            if role == ValidationRuleDetailsModel.DISPLAY_NUM_ROLE:
                return self._display_num

            return super(
                ValidationRuleDetailsModel.ValidationRuleDetailsModelItem, self
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

            if role == ValidationRuleDetailsModel.DISPLAY_NUM_ROLE:
                # This role is a special case which modifies the model data, instead of the particular index
                # data. This is triggered from setting data on the footer.
                if self._is_footer:
                    self.model().toggle_display_items()

            else:
                super(
                    ValidationRuleDetailsModel.ValidationRuleDetailsModelItem, self
                ).setData(value, role)

    ######################################################################################################
    # ValidationRuleDetailsModel methods
    #

    def __init__(self, parent, group_by=None):
        """
        Create the ValidationRuleDetailsModel.

        :param parent: The parent widget of this model
        :type parent: QtGui.QWidget
        :param group_by: (optional) The field to group the model items by
        :type group_by: str
        """

        QtGui.QStandardItemModel.__init__(self, parent)

        self._details_items = []
        self._display_num = self.MAX_DISPLAY_NUM

        # Add additional roles defined by the ViewItemRolesMixin class.
        self.NEXT_AVAILABLE_ROLE = self.initialize_roles(self.NEXT_AVAILABLE_ROLE)

    ######################################################################################################
    # Properties
    #

    @property
    def details_items(self):
        """Get the raw details item data."""
        return self._details_items

    @property
    def display_num(self):
        """Get the maximum number of items the model will show."""
        return self._display_num

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

        self._details_items = []

        super(ValidationRuleDetailsModel, self).clear()

    def initialize_data(self, data=None, display_num=None):
        """
        Initialize the model with the set of details items for the given validation rule.

        The model will be cleared, all items removed, and new model items added for the details item.

        :param data: The data to initialize the model with.
        :type data: list<dict>
        """

        self.beginResetModel()

        if data is None:
            data = self._details_items

        self.clear()
        self._details_items = data
        self._display_num = display_num or self.MAX_DISPLAY_NUM

        group_item = ValidationRuleDetailsModel.ValidationRuleDetailsGroupModelItem(
            "Affected Objects"
        )
        self.invisibleRootItem().appendRow(group_item)

        for item_data in self._details_items[: self._display_num]:
            model_item = ValidationRuleDetailsModel.ValidationRuleDetailsModelItem(
                item_data
            )
            group_item.appendRow(model_item)

        num_items = len(self._details_items)
        if num_items > self._display_num or num_items > self.MAX_DISPLAY_NUM:
            footer_item = ValidationRuleDetailsModel.ValidationRuleDetailsModelItem(
                {}, is_footer=True
            )
            group_item.appendRow(footer_item)

        self.endResetModel()

    def toggle_display_items(self):
        """
        Toggle the number of items displayed in the model.

        This toggle action is triggered when the footer item is clicked. More items will be shown if not all
        items are currently showing. If all item are showing, then the number of items shown will be reset to
        the initial maxium.
        """

        num_items = len(self._details_items)

        if num_items < self.MAX_DISPLAY_NUM:
            return

        if num_items > self._display_num:
            # Show more
            new_display_num = self._display_num + self.INCREMENT_DISPLAY_NUM

            # NOTE this method and the initialize_data method do very similar things - they could be merged
            # into a single method for easier maintenance

            # Get the root group item to add the new items to
            group_item = self.item(0)
            if not group_item or group_item.rowCount() <= 0:
                return

            # Get the footer and add it back to the end after all the new items are added.
            # footer_item = self.item(self.rowCount()-1)
            footer_item = group_item.takeRow(group_item.rowCount() - 1)[0]
            if not footer_item or not footer_item.data(
                ValidationRuleDetailsModel.IS_FOOTER_ROLE
            ):
                footer_item = ValidationRuleDetailsModel.ValidationRuleDetailsModelItem(
                    {}, is_footer=True
                )

            # Add the new items
            for item_data in self._details_items[self._display_num : new_display_num]:
                model_item = ValidationRuleDetailsModel.ValidationRuleDetailsModelItem(
                    item_data
                )
                group_item.appendRow(model_item)

            num_items = len(self._details_items)
            if num_items > new_display_num or num_items > self.MAX_DISPLAY_NUM:
                group_item.appendRow(footer_item)

            # Update the display number
            self._display_num = new_display_num

        else:
            # Show less (revert to original max number of items)
            self.initialize_data()

    def get_footer_text(self):
        """
        Get the display text for the footer item in the model.

        There should only ever be one footer item in the model data set at a time.

        :return: The display text for the footer item.
        :rtype: str
        """

        num_items = len(self._details_items)

        if num_items < self.MAX_DISPLAY_NUM:
            return None

        if num_items > self._display_num:
            return "Show More..."

        # Else, items exceeded the max but now are all showing.
        return "Show Less..."
