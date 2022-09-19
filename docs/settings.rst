.. _data-validation-settings:

App Config Settings
=================================

The Data Validation App settings are defined in the Toolkit App Config settings file ``tk-multi-data-validation.yml``. The app supports the following settings:

    hook_data_validation:
        The hook to define the Validation Rule Set and sanitize validation results.

    rules:
        The list of active validation rules (these will be shown in the Data Validation App if found in the Validation Rule Set). Each item in the list must include an ``id`` and ``name``, which are the unique identifier and display name of the rule. Optionally, items may define a ``data_type``, which categorizes the rule for a grouped display.

An example of the settings file that is set up for Alias and VRED:

.. code-block:: yaml
    :caption: tk-multi-data-validation.yml settings for the VRED Engine

    settings.tk-multi-data-validation.alias:
      location: "@apps.tk-multi-data-validation.location"
      hook_data_validation: "{engine}/tk-multi-data-validation/basic/data_validation.py"
      rules:
        - id: delete_null_nodes
        - id: zero_transforms
        - id: remove_empty_layers

    settings.tk-multi-data-validation.vred:
      location: "@apps.tk-multi-data-validation.location"
      hook_data_validation: "{engine}/tk-multi-data-validation/basic/data_validation.py"
      rules:
        - id: delete_hidden_nodes
          data_type: Scene Graph
        - id: delete_unused_materials
          data_type: Materials
        - id: unload_references
          data_type: References

Notice that the Alias set up does not define the ``data_type`` field for its rules, while VRED does; this means that in the Data Validation App for VRED, the rules can be grouped by the data type. Also remember that the config settings may only activate the listed rules, but the Engine's may have more validation rules available (which are hidden until listed here in the config settings).
