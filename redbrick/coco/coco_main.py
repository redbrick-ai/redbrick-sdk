"""Main file for converting RedBrick format to coco format."""
import asyncio
from typing import Dict, List, Optional, Tuple

import aiohttp
from yarl import URL
import tenacity

from redbrick.utils.async_utils import gather_with_concurrency
from redbrick.utils import aioimgspy
from redbrick.utils.logging import print_warning
from redbrick.common.constants import MAX_CONCURRENCY, MAX_RETRY_ATTEMPTS
from .polygon import rb2coco_polygon
from .bbox import rb2coco_bbox
from .categories import rb_get_class_id, rb2coco_categories_format


async def _get_image_dimension_map(
    datapoints: List[Dict],
) -> Dict[str, Tuple[int, int]]:
    """Get a map from taskId to (width, height) of the images."""

    @tenacity.retry(
        reraise=True,
        stop=tenacity.stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
        retry=tenacity.retry_if_not_exception_type(
            (KeyboardInterrupt, PermissionError, ValueError)
        ),
    )
    async def _get_size(
        session: aiohttp.ClientSession, datapoint: Dict
    ) -> Tuple[str, Tuple[int, int]]:
        if not datapoint["itemsPresigned"] or not datapoint["itemsPresigned"][0]:
            return datapoint["taskId"], (0, 0)
        async with session.get(
            # encode with yarl so that aiohttp doesn't encode again.
            URL(datapoint["itemsPresigned"][0], encoded=True)
        ) as response:
            temp = await aioimgspy.probe(response.content)  # type: ignore
        return datapoint["taskId"], (temp["width"], temp["height"])

    # limit to 30, default is 100, cleanup is done by session
    conn = aiohttp.TCPConnector(limit=MAX_CONCURRENCY)
    async with aiohttp.ClientSession(connector=conn) as session:
        coros = [_get_size(session, dpoint) for dpoint in datapoints]
        all_sizes = await gather_with_concurrency(10, coros, "Getting image dimensions")

    await asyncio.sleep(0.250)  # give time to close ssl connections
    return {temp[0]: temp[1] for temp in all_sizes}


# pylint: disable=too-many-locals
def coco_converter(
    datapoints: List[Dict],
    taxonomy: Dict,
    image_dims_map: Optional[Dict[str, Tuple[int, int]]] = None,
) -> Dict:
    """Convert redbrick labels to standard coco format."""
    coco_categories = rb2coco_categories_format(taxonomy)

    if image_dims_map is None:
        loop = asyncio.get_event_loop()
        image_dims_map = loop.run_until_complete(_get_image_dimension_map(datapoints))

    images: List[Dict] = []
    annotations: List[Dict] = []
    for data in datapoints:
        file_name = data["name"]
        task_id = data["taskId"]
        labels = data["labels"]

        width, height = image_dims_map[task_id]

        current_image_id = len(images)
        image_entry = {
            "id": current_image_id,
            "task_id": task_id,
            "file_name": file_name,
            "raw_url": data["items"][0],
            "height": height,
            "width": width,
        }
        if "itemsPresigned" in data:
            image_entry["signed_url"] = data["itemsPresigned"][0]

        images.append(image_entry)

        skipped_labels = 0
        for label in labels:
            annotation_index = len(annotations)
            try:
                if label.get("bbox2d"):
                    class_id = rb_get_class_id(label["category"][0], taxonomy)
                    coco_label = rb2coco_bbox(
                        label,
                        annotation_index,
                        current_image_id,
                        class_id,
                        width,
                        height,
                    )
                    annotations.append(coco_label)
                elif label.get("polygon"):
                    class_id = rb_get_class_id(label["category"][0], taxonomy)
                    coco_label = rb2coco_polygon(
                        label,
                        annotation_index,
                        current_image_id,
                        class_id,
                        width,
                        height,
                    )
                    annotations.append(coco_label)
                else:
                    skipped_labels += 1
            except Exception:  # pylint: disable=broad-except
                skipped_labels += 1

        if skipped_labels:
            if labels == skipped_labels:
                print_warning(
                    f"No bbox/polygon labels found for task {data['taskId']}, skipping"
                )
            else:
                print_warning(
                    f"Skipped {skipped_labels} non bbox/polygon labels for {data['taskId']}"
                )

    return {
        "images": images,
        "annotations": annotations,
        "categories": coco_categories,
        "info": {},
        "licenses": [],
    }
