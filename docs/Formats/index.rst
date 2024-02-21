.. _formats: 

Formats
==============================
This section will document the structure used for importing and exporting data from RedBrick AI. For importing & exporting annotations please refer to the :ref:`labeling_type_target`.

Import format
~~~~~~~~~~~~~~~~~~~~~~~~~
The RedBrick AI SDK uses a list of :class:`redbrick.types.task.InputTask` objects for importing data. To import data through the CLI or SDK, create a JSON file that follows the same format.

.. autoclass:: redbrick.types.task.InputTask
   :members:

.. autoclass:: redbrick.types.task.Series
   :members:

   .. autoattribute:: items


Export format
~~~~~~~~~~~~~~~~~~~~~~~~~
The RedBrick SDK will export a list of OutputTasks in an object, along with NIfTI segmentation files if they exist, written to the disk. The CLI will export in the same format in a JSON file.

.. autoclass:: redbrick.types.task.OutputTask
   :members:

.. autoclass:: redbrick.types.task.ConsensusScore
   :members:

.. autoclass:: redbrick.common.enums.TaskStates
   :members:


.. Add hidden links to other pages
.. toctree::
  :hidden:

  Annotation types
  Taxonomy