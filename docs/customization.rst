.. _validation-customization:

Customizing the Validation
=================================

Before customizing the Data Validation App (DVA), it is assumed that the Engine hook has been set up as described :ref:`here <engine-setup-hook>`.

To further customize the data validation for an Engine, we need to override the Engine hook:

.. code-block:: yaml
    :caption: Data Validation App config settings file (tk-multi-data-validation.yml)

    settings.tk-multi-data-validation.vred:
      location: "@apps.tk-multi-data-validation.location"
      hook_data_validation: "{engine}/tk-multi-data-validation/basic/data_validation.py:{config}/tk-multi-data-validation/my_custom_vred_data_validation.py"

Notice that another hook file is appended to ``hook_data_validation``. This is our custom hook file where we will add our modifications. The ``my_custom_vred_data_validation.py`` hook file is stored in your configuration hooks folder, for example: ``tk-config-default2/hooks/tk-multi-data-validation/my_custom_vred_data_validation.py``. Let's start implementing the custom hook:

.. code-block:: python
    :caption: Example: my_custom_data_validation.py hook file

        import sgtk
        HookBaseClass = sgtk.get_hook_baseclass()

        class MyCustomVREDDataValidationHook(HookBaseClass):
            """Subclass the VRED Engine hook class VREDDataValidationHook."""

            def get_validation_data(self):
                """Override the VRED Engine hook method to modify the Validation Rule Set."""

                # This will call the base VRED Engine hook to get the default rule set
                vred_rule_set = super(MyCustomVREDDataValidationHook, self).get_validation_data()

                # Modify the rule set as desired. Examples will be provided later on.

                # Return the modified rule set
                return vred_rule_set

.. _customize-new-rule:

Adding a New Rule
------------------------------------------

Now that the custom hook has been set up, we can add new :ref:`validation-rule-item` to the default set of rules. To add a new rule, we will modify the :ref:`validation-rule-set` dictionary returned by the VRED Engine hook:

.. code-block:: python
    :caption: Example: Adding a new rule in my_custom_data_validation.py

        def get_validation_data(self):
            """Override the VRED Engine hook method to tweak the VRED Validation Rule Set."""

            vred_rule_set = super(MyCustomVREDDataValidationHook, self).get_validation_data()

            # Create a simple new rule
            my_new_rule = {
                "name": "My New Rule",
                "check_func": my_new_rule_check,
                "fix_func": my_new_fix_rule
            }

            # Add the new rule to the set, using rule id ``my_new_rule``
            vred_rule_set["my_new_rule"] = my_new_rule

            return vred_rule_set

        def my_new_rule_check(self):
            """Implement the new rule check function here.""""

        def my_new_rule_fix(self):
            """Implement the new rule fix function here."

The new rule has been added to the validation rule set, and now the DVA has access to it. To tell the DVA to show the new rule in the GUI, we need to add it to the app config:

.. code-block:: yaml
    :caption: Example: Update the app config tk-multi-data-validation.yml to show the new rule

    settings.tk-multi-data-validation.vred:
      location: "@apps.tk-multi-data-validation.location"
      hook_data_validation: "{engine}/tk-multi-data-validation/basic/data_validation.py:{config}/tk-multi-data-validation/my_custom_vred_data_validation.py"
      rules:
        - id: delete_hidden_nodes # a default rule
        - id: my_new_rule         # your custom rule

.. _customize-remove-rule:

Removing a Rule
------------------------------------------

A :ref:`validation-rule-item` can be removed by deleting rule dictionary items from the :ref:`validation-rule-set`:

.. code-block:: python
    :caption: Example: Removing the rule delete_hidden_nodes

        def get_validation_data(self):
            """Override the VRED Engine hook method to tweak the VRED Validation Rule Set."""

            vred_rule_set = super(MyCustomVREDDataValidationHook, self).get_validation_data()

            # Remove the rule with id 'delete_hidden_nodes' by deleting the dict item
            del vred_rule_set["delete_hidden_nodes"]

            return vred_rule_set

Optionally, a rule can instead be removed by omitting the rule id in the :ref:`data-validation-settings`:

.. code-block:: yaml
    :caption: Example: Remove delete_hidden_nodes rule using the config tk-multi-data-validation.yml

    settings.tk-multi-data-validation.vred:
      location: "@apps.tk-multi-data-validation.location"
      hook_data_validation: "{engine}/tk-multi-data-validation/basic/data_validation.py:{config}/tk-multi-data-validation/my_custom_vred_data_validation.py"
      rules:
        - id: my_new_rule         # your custom rule

.. _customize-modify-rule:

Modifying an Existing Rule
------------------------------------------

An exisiting :ref:`validation-rule-item` can be modified by updating the :ref:`validation-rule-set`:

.. code-block:: python
    :caption: Modify rule ``delete_hidden_nodes``

        def get_validation_data(self):
            """Override the VRED Engine hook method to tweak the VRED Validation Rule Set."""

            vred_rule_set = super(MyCustomVREDDataValidationHook, self).get_validation_data()

            # Update the ``delete_hidden_nodes`` rule name and error message
            vred_rule_set["delete_hidden_nodes"]["name"] = "Delete all the Nodes!!!"
            vred_rule_set["delete_hidden_nodes"]["error_msg"] = "Oh no, we found an issue..."

            return vred_rule_set

If a callback function needs to be modified, the hook method can be overriden directly. For example, the VRED Engine hook defines the method ``find_hidden_nodes`` for tthe ``delete_hidden_nodes`` rule check function. To modify the check function, we can override the hook method:

.. code-block:: python
    :caption: my_custom_data_validation.py hook file

        class MyCustomVREDDataValidationHook(HookBaseClass):
            """Subclass the VRED Engine hook class VREDDataValidationHook."""

            def find_hidden_nodes(self):
                """
                Override the VRED Engine hook method.

                Tweak this method to only find geometry nodes.
                """

                # Call the base VRED Engine hook method to find all hidden nodes
                nodes = super(MyCustomVREDDataValidationHook, self).find_hidden_nodes()

                # Filter out the list of nodes to only include geometry nodes.
                my_geometry_nodes = []
                for node in nodes:
                    if isinstance(node, vrdGeometryNode):
                        my_geometry_nodes.append(node)

                # Return the modified node list
                return my_geometry_nodes

The rule's fix, action and item action callback functions can be overridden the same was as shown above for the check function.
