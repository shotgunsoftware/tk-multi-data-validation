# Copyright (c) 2022 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.


class ValidationRuleType(object):
    """
    A validation rule type categorizes a :class:`ValidationRule`.

    **Default Rule Types**
        none
            :id none: 0
            :name none: "All"
            :description none: A placeholder type to give to a validation rule that has no type.
        auto
            :id auto: 1
            :name auto: "Auto"
            :description auto: A rule of this type will automatically be applied to the data for validation.
        required
            :id required: 2
            :name required: "Required"
            :description required: A rule of this type is required to be applied to the data for validation.
        optional
            :id optional: 3
            :name optional: "Optional"
            :description optional: A rule of this type is not required to be applied to the data for validation.
        manual
            :id manual: 4
            :name manual: "Manual"
            :description manual: A rule of this type is required but must be manually checked (cannot be automated).
    """

    # Validation rule type ids
    # TODO allow user to create on demand rule types as they wish
    (
        RULE_TYPE_NONE,
        RULE_TYPE_AUTO,
        RULE_TYPE_REQUIRED,
        RULE_TYPE_OPTIONAL,
        RULE_TYPE_MANUAL,
        RULE_TYPE_ACTIVE,
    ) = range(6)

    def __init__(self, rule_type_id):
        """
        Create a ValidationRuleType object.

        :param rule_type_id: The unique identifier for this rule type.
        :type rule_type: int (see RULE_TYPES for supported type ids)
        """

        self._id = rule_type_id
        self._data = self.get_data_for_type(rule_type_id)
        self._name = self._data.get("name")
        self._sg_icon = self._data.get("sg_icon")
        self._sg_checkbox_icon = self._data.get("sg_checkbox_icon")
        self._icon = None
        self._checkbox_icon = None

        if self.id == self.RULE_TYPE_ACTIVE:
            self._accept_rule_func = lambda rule: rule.required or rule.checked
        else:
            self._accept_rule_func = None

    def __eq__(self, other):
        """
        Implement the equal operator for ValidationRuleType objects.

        The rule types are equal if their ids are equal.

        :param other: The other validation rule type to compare with
        :type other: ValidationRuleType

        :return: True if this rule type is equal to other, else False.
        :rtype: bool
        """

        return self.id == other.id

    @classmethod
    def get_data_for_type(cls, type_id):
        """
        Get the validation rule type data for the given type.

        :param type_id: The rule type id to get the data for.
        :type type_id: int

        :return: The validation rule type data.
        :rtype: dict

        **Return dict format**
            name
                :type: str
                :description: The display name for the validation rule type.
            icon
                :type: QtGui.QIcon
                :description: The display icon for the validation rule type.
            checkbox_icon
                :type: QtGui.QIcon
                :description: The icon to use to display a checkbox for the rule type.
        """

        # TODO let this icons be configurable

        if type_id == cls.RULE_TYPE_NONE:
            return {
                "name": "All",
                # TODO Design icon
                # "sg_icon": SGQIcon.Info(),
                "sg_icon": "Info",
            }

        if type_id == cls.RULE_TYPE_AUTO:
            return {
                "name": "Automated",
                # TODO Design icon
                "sg_icon": "GreenCheckMark",
            }

        if type_id == cls.RULE_TYPE_REQUIRED:
            return {
                "name": "Required",
                # TODO Design icon
                "sg_icon": "GreenCheckMark",
            }

        if type_id == cls.RULE_TYPE_OPTIONAL:
            # Toggle icon to display a toggle button since Qt does not have a wiget for this.
            return {
                "name": "Optional",
                # TODO Design icon
                "sg_icon": "Lock",
                "sg_checkbox_icon": "Info",
            }

        if type_id == cls.RULE_TYPE_MANUAL:
            return {
                "name": "Manual",
                # TODO Design icon
                "sg_icon": "RedRefresh",
            }

        if type_id == cls.RULE_TYPE_ACTIVE:
            return {
                "name": "Active",
                # TODO Design icon
                "sg_icon": "RedRefresh",
            }

        return None

    @classmethod
    def get_type_for_rule(cls, rule):
        """
        Create a ValidationRuleType object for the given rule.

        :param rule: The rule to get the type object for
        :type rule: ValidationRule

        :return: The type object for the rule.
        :rtype: ValidationRuleType
        """

        if rule.required:
            return cls(cls.RULE_TYPE_REQUIRED)

        # Else optional
        return cls(cls.RULE_TYPE_OPTIONAL)

    @property
    def id(self):
        """Get the id for this validaiton rule type."""
        return self._id

    @property
    def name(self):
        """Get the display name for this validation rule type."""
        return self._name

    @property
    def sg_icon(self):
        """Get the ShotGrid icon class name to create the icon for this validation rule type."""
        return self._sg_icon

    @property
    def sg_checkbox_icon(self):
        """Get the ShotGrid icon class name to create the checkbox icon for this validation rule type."""
        return self._sg_checkbox_icon

    @property
    def icon(self):
        """Get or set the icon for this validation rule type."""
        return self._icon

    @icon.setter
    def icon(self, value):
        self._icon = value

    @property
    def checkbox_icon(self):
        """Get or set the checkbox icon for this validation rule type."""
        return self._checkbox_icon

    @checkbox_icon.setter
    def checkbox_icon(self, value):
        self._checkbox_icon = value

    @property
    def is_valid(self):
        """Get the property indicating if this rule type obejct is valid."""
        return self._data is not None

    def is_rule_accepted(self, rule):
        """
        Check if the rule type accepts this rule into its grouping.

        Default behaviour is this rule type will accept a rule if the rule's type matches the this rule type.
        A rule type may define a custom acceptance function to accept rules across different types, for
        example, see RULE_TYPE_ACTIVE.

        :param rule: The rule to check if it is accepted by this type
        :type rule: ValidationRule
        """

        if not rule:
            return False

        if self._accept_rule_func is None:
            return rule.type == self

        return self._accept_rule_func(rule)
