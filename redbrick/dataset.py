"""Interface for interacting with your RedBrick AI Datasets."""

from redbrick.common.context import RBContext
from redbrick.common.entities import RBDataset


class RBDatasetImpl(RBDataset):
    """
    Representation of RedBrick dataset.

    The :attr:`redbrick.RBDataset` object allows you to programmatically interact with
    your RedBrick dataset. You can upload data, assign tasks, and query your data with this object. Retrieve the dataset object in the following way:

    .. code:: python

        >>> dataset = redbrick.get_dataset(api_key="", org_id="", dataset_name="")
    """

    def __init__(self, context: RBContext, org_id: str, dataset_name: str) -> None:
        """Construct RBDataset."""
        # pylint: disable=import-outside-toplevel, cyclic-import
        from redbrick.upload import DatasetUploadImpl
        from redbrick.export import DatasetExportImpl

        self.context = context

        self._org_id = org_id
        self._dataset_name = dataset_name

        # check if dataset exists on backend to validate
        self._get_dataset()

        self.upload = DatasetUploadImpl(self)
        self.export = DatasetExportImpl(self)

    @property
    def org_id(self) -> str:
        """
        Read only property.

        Retrieves the unique Organization UUID that this dataset belongs to
        """
        return self._org_id

    @property
    def dataset_name(self) -> str:
        """
        Read only name property.

        Retrieves the dataset name.
        """
        return self._dataset_name

    def _get_dataset(self) -> None:
        """Get dataset to confirm it exists."""
        self.context.dataset.get_dataset(self.org_id, self.dataset_name)

    def __str__(self) -> str:
        """Get string representation of RBDataset object."""
        return f"RedBrick Dataset - {self.dataset_name} - id:( {self.dataset_name} )"

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self)
