.. _formats:

Formats
==============================
This section will document the structure used for importing and exporting data from RedBrick AI.

Import
~~~~~~~~~~~~~~~~~~~~~~~~~
The RedBrick AI SDK uses a list of :class:`redbrick.types.task.InputTask` objects for importing data. To import data through the CLI or SDK, create a JSON file that follows the same format.

.. autoclass:: redbrick.types.task.InputTask
   :members:

.. autoclass:: redbrick.types.task.Series
   :members:

   .. autoattribute:: items


Export
~~~~~~~~~~~~~~~~~~~~~~~~~
The RedBrick SDK will export a list of :class:`redbrick.types.task.OutputTask` objects, along with NIfTI segmentation files if they exist, written to the disk. The CLI will export in the same format in a JSON file.

.. autoclass:: redbrick.types.task.OutputTask
   :members:

.. autoclass:: redbrick.types.task.ConsensusScore
   :members:

.. autoclass:: redbrick.common.enums.TaskStates
   :members:


.. Add hidden links to other pages
.. toctree::
  :hidden:

  annotations
  taxonomy
