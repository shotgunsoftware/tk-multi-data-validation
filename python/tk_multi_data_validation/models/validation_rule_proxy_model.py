# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

from .validation_rule_model import ValidationRuleModel
from ..utils.framework_qtwidgets import FilterItem, FilterItemTreeProxyModel


class ValidationRuleProxyModel(FilterItemTreeProxyModel):
    """
    A filter proxy model for the ValidationRuleModel.
    """

    def __init__(self, *args, **kwargs):
        """
        Create the validation rule proxy model.

        :param args: The arguments to pass to the base class constructor.
        :type args: list
        :param kwargs: The keyword arguments to pass to the base class constructor.
        :type kwargs: dict
        """

        super(ValidationRuleProxyModel, self).__init__(*args, **kwargs)

        #
        # Additional FiltItem objects (to the `_filter_items` list) that are apply to the model data when to
        # check acceptance
        #
        self._text_filter = None
        self._rule_type_filter = None
        self._rule_type_filter_role = None

        self._error_filter_active = False
        self._error_filter = FilterItem(
            None,
            FilterItem.FilterType.BOOL,
            FilterItem.FilterOp.IS_TRUE,
            filter_role=ValidationRuleModel.RULE_HAS_ERROR_ROLE,
        )

    #########################################################################################################
    # Public methods

    def set_text_filter_value(self, text, filter_role=None, data_func=None):
        """
        Set the text to filter the model data by.

        :param text: The text filter value
        :type text: str
        :param filter_role: The filter role to get the model data by, to compare with the text filter value.
        :type filter_role: int
        :param data_func: The callback to get the model data by, to compare with the text filter value.
            NOTE: if `filter_role` is specified then `data_func` will be ignored.
        :type data_func: function
        """

        if self._text_filter:
            self._text_filter.filter_role = filter_role
            self._text_filter.data_func = data_func
        else:
            self._text_filter = FilterItem(
                None,  # id field is not necessary
                FilterItem.FilterType.STR,
                FilterItem.FilterOp.IN,
                filter_role=filter_role,
                data_func=data_func,
            )

        self._text_filter.filter_value = text
        self._update()

    def set_rule_type(self, rule_type, filter_role):
        """
        Set the rule type to filter the model data by.

        :param rule_type: The validation rule type filter value
        :type rule_type: int
        :param filter_role: The filter role to get the model data by, to compare with the text filter value.
        :type filter_role: int
        """

        self._rule_type_filter = rule_type
        self._rule_type_filter_role = filter_role
        self._update()

    def remove_text_filter(self):
        """
        Remove the text filter from the proxy model. The text filter will no longer be applied when checking
        acceptance of model data.
        """

        self._text_filter = None
        self._update()

    def remove_rule_type_filter(self):
        """
        Remove the rule type filter from the proxy model. The text filter will no longer be applied when
        checking acceptance of model data.
        """

        self._rule_type_filter = None
        self._rule_type_filter_role = None
        self._update()

    def turn_on_error_filter(self, on=None):
        """
        Turn on or off the error filter.

        :param on: Set to True to turn on the error filter, False to turn off, and None to toggle the current
            filter state (if on then it will be off, and vice-versa)
        :param on: bool
        """

        if on is None:
            on = not self._error_filter_active

        self._error_filter_active = on
        self._update()

    #########################################################################################################
    # Protected methods

    def _update(self):
        """
        Invalidate the proxy model filter to re-evaluate the source model data. Each item in the source model
        will be checked.
        """

        self.layoutAboutToBeChanged.emit()
        self.invalidateFilter()
        self.layoutChanged.emit()

    def _is_row_accepted(self, src_row, src_parent_idx, parent_accepted):
        """
        Override the base class method.

        Apply each filter to the data pertaining to the given model item to check if the data is accepted by
        the filters.

        :param src_row: The row in the source model to filter.
        :type src_row: int
        :param src_parent_idx: The parent index of the source model's row to filter.
        :type src_parent_idx: :class:`sgtk.platform.qt.QModelIndex`
        :param parent_accepted: True if the parent is known already to be accepted, else False.
        :type parent_accepted: bool

        :return: True if the row is accepted, else False.
        :rtype: bool
        """

        # Call the base class method to check against the `_filter_items` list of filters
        base_model_accepts = super(ValidationRuleProxyModel, self)._is_row_accepted(
            src_row, src_parent_idx, parent_accepted
        )
        if not base_model_accepts:
            return False

        src_idx = self.sourceModel().index(src_row, 0, src_parent_idx)
        if not src_idx.isValid():
            return False

        # Check the proxy model specific filter items for rule type
        if self._rule_type_filter:
            rule = src_idx.data(self._rule_type_filter_role)
            if not self._rule_type_filter.is_rule_accepted(rule):
                return False

        # Check the proxy model specific filter items for text
        if self._text_filter:
            if not self._text_filter.accepts(src_idx):
                return False

        if self._error_filter_active:
            if not self._error_filter.accepts(src_idx):
                return False

        # All good, accepted!
        return True
