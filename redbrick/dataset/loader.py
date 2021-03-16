"""A higher level abstraction."""
from typing import Union, Dict, List, Any

# import numpy as np  # type: ignore
import requests
import json

from redbrick.dataset.dataset_base import DatasetBase
from redbrick.api import RedBrickApi
from redbrick.logging import print_info, print_error


class DatasetLoader(DatasetBase):
    """Dataset loader class."""

    def __init__(self, org_id: str, data_set_name: str) -> None:
        """Construct Loader."""
        self.org_id = org_id
        self.data_set_name = data_set_name
        self.api_client = RedBrickApi(cache=False)

        print_info("Retrieving dataset ...")

        # Dataset info
        try:
            dataset = self.api_client.get_datapointset(self.org_id, self.data_set_name)[
                "dataPointSet"
            ]
        except Exception as err:
            print_error(err)
            return

        print_info("Dataset successfully retrieved!")

        self.org_id = dataset["orgId"]
        self.data_set_name = dataset["name"]
        self.data_type = dataset["dataType"]
        self.datapoint_count = dataset["datapointCount"]
        self.desc = dataset["desc"]
        self.createdAt = dataset["createdAt"]
        self.createdBy = dataset["createdBy"]
        self.status = dataset["status"]

    def upload_items(self, items: str, storage_id: str) -> None:
        """Upload a list of items to the backend."""

        # Getting item list presign
        itemsListUploadInfo_ = self.api_client.get_itemListUploadPresign(
            org_id=self.org_id, file_name="upload-sdk.json"
        )["itemListUploadPresign"]
        presignedUrl_ = itemsListUploadInfo_["presignedUrl"]
        filePath_ = itemsListUploadInfo_["filePath"]
        fileName_ = itemsListUploadInfo_["fileName"]
        uploadId_ = itemsListUploadInfo_["uploadId"]
        createdAt_ = itemsListUploadInfo_["createdAt"]

        # Uploading items to presigned url
        print_info("Uploading file '{}'".format(items))
        with open(items, "rb") as f:
            json_payload = json.load(f)
            response = requests.put(presignedUrl_, json=json_payload)

        # Call item list upload success
        if response.ok:
            itemsListUploadSuccessInput_ = {
                "orgId": self.org_id,
                "filePath": filePath_,
                "fileName": fileName_,
                "uploadId": uploadId_,
                "taskType": "ITEMS",
                "dataType": self.data_type,
                "storageId": storage_id,
                "dpsName": self.data_set_name,
            }
            uploadSuccessPayload_ = self.api_client.itemListUploadSuccess(
                org_id=self.org_id,
                itemsListUploadSuccessInput=itemsListUploadSuccessInput_,
            )["itemListUploadSuccess"]
            importId_ = uploadSuccessPayload_["upload"]["importId"]
            print_info(
                "Upload is processing, this is your importId: {}".format(importId_)
            )
        else:
            print_error("Something went wrong uploading your file {}.".format(items))

    def upload_items_with_labels(
        self, items: str, storage_id: str, label_set_name: str, task_type: str
    ) -> None:
        """Upload a list of items with labels to the backend."""

        # Getting item list presign
        itemsListUploadInfo_ = self.api_client.get_itemListUploadPresign(
            org_id=self.org_id, file_name="upload-sdk.json"
        )["itemListUploadPresign"]
        presignedUrl_ = itemsListUploadInfo_["presignedUrl"]
        filePath_ = itemsListUploadInfo_["filePath"]
        fileName_ = itemsListUploadInfo_["fileName"]
        uploadId_ = itemsListUploadInfo_["uploadId"]
        createdAt_ = itemsListUploadInfo_["createdAt"]

        # Uploading items to presigned url
        print_info("Uploading file '{}'".format(items))
        with open(items, "rb") as f:
            json_payload = json.load(f)
            response = requests.put(presignedUrl_, json=json_payload)

        # Call item list upload success
        if response.ok:
            itemsListUploadSuccessInput_ = {
                "orgId": self.org_id,
                "filePath": filePath_,
                "fileName": fileName_,
                "uploadId": uploadId_,
                "taskType": task_type,
                "dataType": self.data_type,
                "storageId": storage_id,
                "dpsName": self.data_set_name,
                "cstName": label_set_name,
            }
            uploadSuccessPayload_ = self.api_client.itemListUploadSuccess(
                org_id=self.org_id,
                itemsListUploadSuccessInput=itemsListUploadSuccessInput_,
            )["itemListUploadSuccess"]
            importId_ = uploadSuccessPayload_["upload"]["importId"]
            print_info(
                "Upload is processing, this is your importId: {}".format(importId_)
            )
        else:
            print_error("Something went wrong uploading your file {}.".format(items))
