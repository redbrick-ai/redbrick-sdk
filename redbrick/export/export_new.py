"""Export to standard RedBrick format."""


from redbrick.api import RedBrickApi
import redbrick


class LabelsetLabelsIterator:
    def __init__(self, org_id: str, labelset_name: str) -> None:
        """Construct LabelsetLabelsIterator."""
        self.labelset_name = labelset_name
        self.org_id = org_id
        self.cursor = None
        self.api = RedBrickApi()

    def _get_batch(self) -> None:
        print(self.api.get_datapoints_paged(self.org_id, self.labelset_name))

    def __next__(self) -> dict:
        """Get next labels / datapoint."""


class ExportRedbrick:
    def __init__(self, labelset_name: str, target_dir: str) -> None:
        """Construct ExportRedbrick."""
        self.labelset_name = labelset_name
        self.target_dir = target_dir

    def export(self) -> None:
        # dp_ids
        for i in tqdm(range(len(self.labelset.dp_ids))):
            dp_ = self.labelset.__getitem__(i)


# LOW LEVEL: want an iterator that handles the loading of individual tasks / datapoints from a labelset


if __name__ == "__main__":
    redbrick.init(
        "bxayadULXtvX_D4sXzD7nRkmjNDKQkM6-jaXUEE7u8E", "http://localhost:4000/graphql"
    )

    iterator = LabelsetLabelsIterator("3b209401-4704-448d-96b1-1a9689a041b2", "lset")

    iterator._get_batch()
