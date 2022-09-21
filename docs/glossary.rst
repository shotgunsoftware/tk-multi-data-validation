.. _glossary:

Glossary
====================

The terminology used in the Data Validation App.


.. _validation-rule-item:

Validation Rule
------------------------------------

A validaiton rule defines how the data is evaluated and determines if the data is in the proper format or not. The data is valid if it passes the validation for each rule in the :ref:`validation-rule-set`.

The rule may optionally define a fix action that will modify the data such that it will pass the rule's validation.

.. _validation-rule-check-func:

Check Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a rule's validation can be automated, it will define a "check function". This is the function that runs to validate the data by the rule's criteria. This is also refered to as the "validate function".

.. _validation-rule-fix-func:

Fix Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a rule's fix can be automated, it will define a "fix function". This is the function that runs to modify the data to comply with the rule's validation.

.. _validation-rule-actions:

Actions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A rule has two main functions, the :ref:`validation-rule-check-func` and :ref:`validation-rule-fix-func`, but it can also have other action functions defined. These action functions are typically functions to visualize the :ref:`validation-affected-objects`; for example, selecting all of the affected objects in the DCC.

.. _validation-rule-item-actions:

Item Actions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Item actions are similar to :ref:`validation-rule-actions`, the only difference is that the item action is applied to a single :ref:`validation-affected-objects`, instead of all of the affected objects.

.. _validation-affected-objects:

Affected Objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When a rule's :ref:`validation-rule-check-func` is run, it gathers any data objects that do not comply with the rule's validation. These data objects are the **Affected Objects**, but may also be referred to as the **data errors** or **error objects**. These objects are dispalyed in the details panel list view.

.. _validation-rule-set:

Validation Rule Set
------------------------------------

The Validation Rule Set refers to the validation rules that determine how the DCC data is processed and modified. The app will display the list of validation rules in the main view. The "Validate" and "Fix All" actions will execute the check and fix actions for each rule in the set.

See :ref:`engine-setup-override-hook` on how the rule set is created, and refer to :ref:`validation-customization` on how to modify the rule set to your specific needs.
