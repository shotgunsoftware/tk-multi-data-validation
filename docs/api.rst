.. _validation-api:

API Reference
====================

The Data Validation API provides an interface to use components of the App, without running the App from a GUI.

Validation Manager
------------------------------------

.. py:currentmodule:: tk_multi_data_validation.api

.. autoclass:: ValidationManager
    :show-inheritance:
    :members:

.. _validation-api-manager:

.. _validation-api-data:

Data
------------------

The data drives the App display and functionality. A set of data :ref:`Validation Rules <validation-api-data-rule>` are defined by the :ref:`hook <validation-hooks-data-validator>` method :class:`hooks.data_validation.AbstractDataValidationHook.get_validation_data`. The App will display the rule set and provide actions to related to the validation rules. See the :ref:`validation-api-data-rule` class reference for more details.

.. _validation-api-data-rule:

Validation Rule
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:currentmodule:: tk_multi_data_validation.api.data

.. autoclass:: ValidationRule
    :show-inheritance:
    :members:

.. _validation-api-data-rule-type:

Validation Rule Type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ValidationRuleType
    :show-inheritance:
    :members:
