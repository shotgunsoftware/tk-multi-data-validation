.. _getting-started:

Getting Started
====================

The Data Validation App (DVA) is a Toolkit App that can be set up to be used with any DCC. It provides a flexible framework to validate the data within a DCC, according to the validation rules that you choose and define.

.. _engine-setup:

Adding Data Validation to the Engine
--------------------------------------------

The DVA must be run within an Engine. The app can be added to an Engine using the config, as like any other Toolkit App:

.. code-block:: yaml
    :caption: Example: VRED Engine config settings file (tk-vred.yml)

    settings.tk-vred.asset_step:
      apps:
        tk-multi-data-validation: "@settings.tk-multi-data-validation.vred"

To start validating your DCC's data, the Engine must be set up to support the data validation workflow. See next steps in :ref:`engine-setup-hook` to modify the Engine accordingly.

For Engines that have already been set up, see :ref:`validation-customization` on how to modify the validation to your specific needs.

.. _engine-setup-hook:

Setting up the data validation hook
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The DVA requires information from the Engine to determine how it will display and perform the data validation. This information is retrieved using this :ref:`hook <validation-hooks-data-validation>`. The DVA config settings must be modified to specify the ``hook_data_validation`` file that the Engine will use to implement the hook methods:

.. code-block:: yaml
    :caption: Data Validation App config settings file (tk-multi-data-validation.yml)

    settings.tk-multi-data-validation.vred:
      location: "@apps.tk-multi-data-validation.location"
      hook_data_validation: "{engine}/tk-multi-data-validation/basic/data_validation.py"

.. _engine-setup-rule-set:

Defining the Validation Rule Set
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The DVA performs the validation on the data in the DCC by using a **Validation Rule Set**. The DVA itself is not DCC specific, and thus does not define the validation rule set. The responsibility is on the Engine, which is DCC specific, to establish the rule set that determines how the data is validated.

In the previous step, the Engine's data validation hook file was set up. Now we need to implement one of the hook's methods to pass the DCC's Validation Rule Set to the DVA. The hook method that returns the Validation Rule Set is :class:`hooks.data_validation.AbstractDataValidationHook.get_validation_data`. To override this hook method, create the ``AbstractDataValidationHook`` subclass and declare the class method ``get_validation_data``, as shown below:

.. code-block:: python
    :caption: Example: VRED Engine data_validation.py hook file

        import sgtk
        HookBaseClass = sgtk.get_hook_baseclass()

        class VREDDataValidationHook(HookBaseClass):
            """Subclass the base tk-multi-data-validation hook class AbstractDataValidationHook."""

            def get_validation_data(self):
                """Override the base hook method to return the VRED Validation Rule Set."""

                return {
                    # An example rule showing the supported key-values
                    "validation_rule_example_id": {
                        "name": "My Example Validation Rule",
                        "description": "Describe what this validation rule does.",
                        "error_msg": "If there is an error, I will be displayed.",
                        "warn_msg": "If there is a warning, I will be displayed.",
                        "check_func": func_called_to_check_all_for_this_rule,
                        "check_name": "Text displayed on the button that calls the check function",
                        "fix_func": funcn_called_to_fix_all_for_this_rule,
                        "fix_name": "Text displayed on the button that calls the fix function",
                        "fix_tooltip": "Helpful text displayed when hovering over the fix button",
                        "actions": [
                            {
                                "name": "My Example Action",
                                "callback": func_called_to_execute_the_action
                            },
                            {
                                "name": "Select All",
                                "callback": select_all_action_func
                            },
                        ],
                        "item_actions": [
                            {
                                "name": "My Example Item Action",
                                "callback": func_called_to_execute_the_item_action
                            },
                            {
                                "name": "Select A Single Item",
                                "callback": select_item_action_func
                            },
                        ],
                        "get_kwargs": func_called_to_get_kwargs_for_fix_action_funcs
                        "dependency_ids": [
                            "the_rule_id_of_another_rule_I_depend_on",
                            "delete_hidden_nodes",
                        ]
                    },
                    # A more real world example for VRED
                    "delete_hidden_nodes": {
                        "name": "Delete Hidden Nodes",
                        "description": "Find and delete all hidden nodes in the scene.",
                        "check_func": find_hidden_nodes,
                        "fix_func": do_delete_hidden_nodes,
                        "actions": [
                            {
                                "name": "Select All Hidden Nodes",
                                "callback": select_nodes
                            }
                        ],
                        "item_actions": [
                            {
                                "name": "Select Node",
                                "callback": select_node
                            }
                        ],
                    }
                }

Defining validation rule functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each validation rule defined in the Validation Rule Set dictionary may specify callback functions:

- ``check_func``: callback to validate the data by this rule
- ``fix_func``: callback to fix the data by this rule
- ``actions``: callbacks to execute on the affected objects by this rule
- ``item_actions``: callbacks to execute on a single affected object by this rule

These callback functions can be implemented as hook methods; for example, these are the functions to implement to make the ``delete_hidden_nodes`` rule effective:

.. code-block:: python
    :caption: Hook methods for ``delete_hidden_nodes`` rule

        class VREDDataValidationHook(HookBaseClass):
            """Subclass the base tk-multi-data-validation hook class AbstractDataValidationHook."""

            #
            # other class methods omitted
            #

            def find_hidden_nodes(self):
                """Implement the check function for the delete hidden nodes rule."""

            def do_delete_hidden_nodes(self, errors=None):
                """Implement the fix function for the delete hidden nodes rule."""

            def select_nodes(self, errors=None):
                """Implement the select action function for the delete hidden nodes rule."""

            def select_node(self, errors=None):
                """Implement the select item action function for the delete hidden nodes rule."""

The purpose of the rule's check function is to validate the current data according to some criteria. For example, the ``find_hidden_nodes`` method should look for hidden nodes in VRED and return a list of node objects:

.. code-block:: python
    :caption: Check function for ``delete_hidden_nodes`` rule

        def find_hidden_nodes(self):
            """
            Find hidden nodes in VRED.

            :return: A list of hidden nodes.
            :rtype: List[vrdNode]
            """

            # Assume the find_nodes function exists and returns a list VRED node objects
            return find_nodes(hidden=True)

Notice that ``find_hidden_nodes`` returns a list of VRED objects ``vrdNode``. The DVA will call this check function and will need to be able to handle the list of VRED objects. The DVA does not have any knowledge of VRED objects, so it will call the hook method
:class:`hooks.data_validation.AbstractDataValidationHook.sanitize_check_result` to convert the list of VRED objects into a standardized format. For example, the VRED Engine overrides this hook method:

.. code-block:: python
    :caption: VRED Engine override hook method ``sanitize_check_result``

        class VREDDataValidationHook(HookBaseClass):
            """Subclass the base tk-multi-data-validation hook class AbstractDataValidationHook."""

            def sanitize_check_result(self, result):
                """
                Return the check result in the Data Validation standardized format.

                :param result: A result returned by any of the VRED rule check functions.
                :type result: list of VRED objects
                """

                # The check result is valid if the result does not report any error objects
                valid = not result

                # Add the VRED objects to this list in the DVA standard format
                errors = []

                # This assumes the result is a list of VRED objects, but you may want to put
                # in some sanifty checks to ensure the value passed is the expected type, or
                # handle different types of check result values
                for item in result:
                    # VRED objects have the following attributes getObjectID, getName, getType
                    error_item = {
                        "id": item.getObjectID(),
                        "name": item.getName(),
                        "type": item.getType()
                    }
                    errors.append(error_item)

                # The DVA expects a dictionary with key-values:
                #   - is_valid (bool): True if result passed the check, else False
                #   - errors (List[dict]): The errors found by the check
                #       Each error item with keys-values:
                #         - id (str|int): Unique identifier for the error object
                #         - name (str): Display name for the error object
                #         - type (str): Display name for the error object type (optional)
                return {
                    "is_valid": valid,
                    "errors": errors
                }

Now that the rule's check function is implemented, and the result is sanitized for the DVA to handle, next the fix function needs to be implemented:

.. code-block:: python
    :caption: Hook methods for ``delete_hidden_nodes`` rule

        def do_delete_hidden_nodes(self, errors=None):
            """
            Delete the given error objects, which are hidden nodes.

            The errors passed in will be the same errors as returned by the check function
            ``find_hidden_nodes`` and sanitized by the ``sanitize_check_result`` function.
            So for example if the check function returned:

                [node_1, node_2]

            , then the sanitize method would yield:

                {
                    "is_valid": False,
                    "errors": [
                        {
                            "id": node_1_id,
                            "name": "Node 1",
                            "type": vrdNode
                        },
                        {
                            "id": node_2_id,
                            "name": "Node 2",
                            "type": vrdNode
                        }
                    ]
                }

            , and so the ``errors`` key value in the dict of the sanitized result is the
            value passed to this function.

            If no errors are given, you can choose to interpret this as delete all hidden
            nodes.

            :param errors: The hidden nodes to delete. If None, delete all hidden nodes.
            :type errors: List[dict] | None
            """

            if errors is None:
                nodes = self.find_hidden_nodes()
            else:
                # Assume the get_nodes function exists and takes the error data and returns a
                # list of VRED objects. Remember that the error data is a list of dicts in
                # the DVA format, that define the error objects
                nodes = self.get_nodes(errors)

            for node in nodes:
                # Again, assume the delete_node function exists
                self.delete_node(n)

Finally, the action and item action functions need to be implemented. These functions are called in the same way that the fix function is called with the list of errors:

.. code-block:: python
    :caption: Hook methods for ``delete_hidden_nodes`` rule

        def select_nodes(self, errors=None):
            """
            Select the given nodes.

            :param errors: The list of nodes to select.
            :type errors: List[dict]
            """"

            if not errors:
                return

            nodes = self.get_nodes(errors)
            self.select_nodes(nodes)

        def select_node(self, errors=None):
            """
            Select the given node.

            TODO double-check this

            :param errors: A list containing a single node.
            :type errors: List[dict]
            """"

            self.select_nodes(errors)

Adding validation rules to the App
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The dictionary value returned by the ``get_validation_data`` method defines all of the available validation rules. To have these rules show up in the DVA, the tk-multi-data-validation.yml config settings file must be updated:

.. code-block:: yaml
    :caption: tk-multi-data-validation.yml

    settings.tk-multi-data-validation.vred:
      location: "@apps.tk-multi-data-validation.location"
      hook_data_validation: "{engine}/tk-multi-data-validation/basic/data_validation.py"
      rules:
        - id: delete_hidden_nodes

Notice that only the ``delete_hidden_nodes`` rule is listed in the config; this means that our Engine has defined the ``validation_rule_example_id`` rule but it will not appear in the DVA. This is an example of how validation rules can be shown or hidden. See :ref:`data-validation-settings` for more details about the tk-multi-data-validation.yml settings file.


Mapping Validation Rule Fields to the User Interface
---------------------------------------------------------------

The validation rule set returned by the hook method ``get_valdidation_data`` (:ref:`described above <engine-setup>`) determines how the data validation is peformed and how the information is displayed to the user. To help visualize and understand what each of the validation rule set fields affect, below is a mapping of the user interface elements to the rule set dictionary fields:

.. image:: images/mapping-ui-fields.png
    :alt: Data Validation User Interface

**1. Validation rule**

    The highlighted item represents a validation rule from the rule set. Each rule in the set will be displayed as an item in the view. The rule's display name and is set by the ``name`` field.

**2. Validation rule description**

   This is the rule's descriptive text and is set by the ``description`` field.

**3. Validation rule error message**

    This is the rule's error message. Error messages are shown when the rule's check function has failed. The ``error_msg`` field will be appended to rule's error message.

**4. Validation rule warning message**

    This is the rule's warning message. Warning messages are always shown (in yellow). The ``warn_msg`` field will be appended to rule's warning message.

**5. Validation rule status icon**

   This is the rule's validation status from the last time its check function ran. The status is determined by running the function set by the ``check_func`` field.

**6. Validate rule button**

   Clicking this button will validate the data according to the rule. The validation is performed by calling the function set by the ``check_func`` field. The button text is set by the ``check_name`` field.

**7. Fix rule button**

   Clicking this button will fix the data according to the rule. The fix is performed by calling the function set by the ``fix_func`` field. The button text is set by the ``fix_name`` field. The rule's validate function may run before the fix, in order to ensure the fix is applied to the most current data.

**8. Rule actions button menu**

   Clicking this button will pop up the actions menu for the rule. The list of menu actions are set by the ``actions`` field. Clicking on any of the menu actions will call that particular action callback function. The actions menu can also be opened by right-clicking on the rule item in the view.

**9. Details panel**

    The details panel will show more information for the currently select rule in the view. The row of buttons are function the same as the buttons on the rule item in the view. They will be shown in this order: validate button, fix button, all action buttons. See the particular button descriptions above for which fields affect these buttons.

**10. Validate all button**

    Clicking this button will run the validate function for all rules. The rule's validate function is set by the ``check_func`` field.

**11. Fix all button**

    Clicking this button will run the fix function for all rules. The rule's fix function is set by the ``fix_func`` field. The rules' validate functions may run before the fix, in order to ensure the fix is applied to the most up to date errors in the data.

**12. Details panel information**

    This is the currently selected rule's detailed information, including dependencies. The rule's dependencies are set by the ``dependency_ids`` field. Dependencies determine the order in which rules are validated and fixed.

**13. Details panel affected objects**

    The view lists the affected objects after validating the current data by the rule. These are essentially data errors found by running the rule's check function.

**14. Affected object item**

    This is a data error found by running the rule's check function. Right click the item to see the list of item actions set by the ``item_actions`` field. Hover over the item to see the first item action. Click any of the item actions to call the corresponding callback function.

**15. Rule grouping**

    This is a grouping of rules. A rule's group is set by the ``data_type`` field, which can also be set in the app :ref:`data-validation-settings`.
