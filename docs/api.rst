.. _validation-api:

API
====================

The Data Validation API provides an interface to use components of the App, without running the App from a GUI.

.. _validation-api-manager:

Validation Manager
------------------------------------

.. py:currentmodule:: tk_multi_data_validation.api

.. autoclass:: ValidationManager
    :show-inheritance:
    :members:


.. _validation-widget:

Validation Widget
-----------------------

.. py:currentmodule:: tk_multi_data_validation.widgets

.. autoclass:: ValidationWidget
    :show-inheritance:
    :members:


.. _validation-api-data-rule:

Validation Rule
------------------

The data drives the App display and functionality. A set of data :ref:`Validation Rules <validation-api-data-rule>` are defined by the :ref:`hook <validation-hooks-data-validation>` method :class:`hooks.data_validation.AbstractDataValidationHook.get_validation_data`. The App will display the rule set and provide actions to related to the validation rules. See the :ref:`validation-api-data-rule` class reference for more details.

.. py:currentmodule:: tk_multi_data_validation.api.data

.. autoclass:: ValidationRule
    :show-inheritance:
    :members:
