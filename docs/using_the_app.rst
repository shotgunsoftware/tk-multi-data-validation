.. _using-data-validation-app:

Using the Data Validation App
========================================

The purpose of app is to validate the current DCC data accoding to a Validation Rule Set, report any discepancies to the user, and provide the actions to fix the data to be compliant. There are a few ways to validate and fix your data, as pointed out below:

This is the Data Validation App (DVA) in VRED. To point out a few basics of the app:

.. image:: images/basic-ui.png
    :alt: Data Validation User Interface

**1. A Validation Rule Item**

The main app view displays the list of available validation rules. A rule has a name and description that describe what the purpose of the rule is. A rule may provide a **validate** action (sometimes referred to as the check action) that will process the current DCC data, and gather any data objects that do not comply with the rule. The objects that were gathered by the validate step will be shown in the right-hand side details panel, as the **Affected Objects**. A **fix** button action may be provided to modify the data to be compliant with the rule.

**2. Validate and Fix All Actions**

The "Validate" and "Fix All" buttons on the bottom right of the app will execute all of the validate and fix actions for all of the rules shown in the app.

**3. The Details Panel**

.. image:: images/details-panel.png
    :alt: Data Validation Details Panel

The right-hand side details panel can be shown by clicking the "i" toolbutton, or by right-clicking a rule item and selecting "Show Details". The details panel will show extra information about the currently selected rule. After executing the rule's validate action, any data that does not pass the validation will be gathered and displayed in the details list.

.. _understanding-validation:

Understanding How Data is Validated and Fixed
------------------------------------------------

The current data in the DCC can be validated by a single rule, which will call the rule's **check function** to gather any data that is not compliant with the rule. If any data errors were found, then the validation will report a failure and list the data error objects. Validation can also be executed for all rules at once, by clicking the "Validate" action in the bottom right corner of the app. When validation is applied for multiple rules at a time, it sequentially goes through each rule and calls each rule's check function. See the diagram below to visualize the validation steps.

.. image:: images/validation-diagram.png
    :alt: Data Validation Diagram

Similar to validation, data can be fixed by a single rule or by all rules at a time. The app is set up to pre validate before running the fix, to ensure that the error data passed to the fix function reflect the current data accurately, and also post validate to report if the fix was successful or not.

Rule Dependencies
^^^^^^^^^^^^^^^^^^^^^

Rules may have dependencies, meaning that their validate or fix actions should not be executed until other rules have successfully executed their validate or fix action. On validating/fixing all rules, dependencies will determine the order that the rules are validated/fixed in. Rules will not have their validate/fix actions executed if any of their dependencies have failed. When fixing by a single rule, if the rule has dependencies, a dialog will pop up to inform the user that other rule fixes will be executed before running this rule's fix action. This is to ensure the user knows that their data could be modified by another rule that they did not explicitly say to fix by.

.. image:: images/dependencies-dialog.png
    :alt: Dependencies Dialog

If ``rule A`` depends on ``rule B``, if the fix action for ``rule A`` is triggered then the fix action for ``rule B`` will execute first, then if ``rule B`` succeeded, the fix for ``rule A`` will run.
