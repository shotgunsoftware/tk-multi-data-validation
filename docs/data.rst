.. _validation-data:

Data
====================

The data drives the App display and functionality. A set of data :ref:`Validation Rules <validation-data-rule>` are defined by the :ref:`hook <validation-hooks-data-validator>` method :class:`hooks.data_validator.AbstractDataValidatorHook.get_validation_data`. The App will display the rule set and provide actions to related to the validation rules. See the :ref:`validation-data-rule` class reference for more details.

.. _validation-data-rule:

Validation Rule
------------------

.. py:currentmodule:: tk_multi_data_validation.data

.. autoclass:: ValidationRule
    :show-inheritance:
    :members:

.. _validation-data-rule-type:

Validation Rule Type
----------------------

.. autoclass:: ValidationRuleType
    :show-inheritance:
    :members:
