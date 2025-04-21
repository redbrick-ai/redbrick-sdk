"""Graphql Client responsible for make API requests."""

from abc import ABC, abstractmethod
import time
import json
import base64
import gzip
from typing import Dict
import requests  # type: ignore

import aiohttp
import tenacity
from tenacity.retry import retry_if_not_exception_type
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential

from redbrick.common.constants import (
    DEFAULT_URL,
    MAX_RETRY_ATTEMPTS,
    REQUEST_TIMEOUT,
    PEERLESS_ERRORS,
)
from redbrick.config import config
from redbrick.utils.logging import assert_validation, log_error, logger


class RBClient(ABC):
    """Client to communicate with RedBrick AI GraphQL Server."""

    api_key: str
    url: str

    @property
    @abstractmethod
    def headers(self) -> Dict:
        """Get request headers."""

    @abstractmethod
    def execute_query(
        self, query: str, variables: Dict, raise_for_error: bool = True
    ) -> Dict:
        """Execute a graphql query."""

    @abstractmethod
    async def execute_query_async(
        self,
        aio_session: aiohttp.ClientSession,
        query: str,
        variables: Dict,
        raise_for_error: bool = True,
    ) -> Dict:
        """Execute a graphql query using asyncio."""


class RBClientImpl(RBClient):
    """Client to communicate with RedBrick AI GraphQL Server."""

    def __init__(self, api_key: str, url: str) -> None:
        """Construct RBClient."""
        self.url = (url or DEFAULT_URL).lower().rstrip("/")
        if DEFAULT_URL in self.url:
            self.url = DEFAULT_URL
        elif "amazonaws.com" not in self.url and "localhost" not in self.url:
            self.url = self.url.replace("https://", "", 1).replace("http://", "", 1)
            pos = self.url.find("/")
            pos = pos if pos >= 0 else len(self.url)
            self.url = "https://" + self.url[:pos] + "/api"

        self.url += "/graphql/"
        self.session = requests.Session()

        self.api_key = api_key
        assert_validation(
            len(self.api_key) == 43,
            "Invalid Api Key length, make sure you've copied it correctly",
        )

    def __del__(self) -> None:
        """Garbage collect and close session."""
        self.session.close()

    @property
    def headers(self) -> Dict:
        """Get request headers."""
        return {
            "RB-SDK-Version": config.version,
            "ApiKey": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Content-Encoding-RB": "gzip",
            "Accept-Encoding": "br, gzip",
        }

    def prepare_query(self, query: str, variables: Dict) -> bytes:
        """Prepare query to be sent to the server."""
        return base64.b64encode(
            gzip.compress(
                json.dumps(
                    {"query": query, "variables": variables}, separators=(",", ":")
                ).encode("utf-8")
            )
        )

    @tenacity.retry(
        reraise=True,
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_not_exception_type(PEERLESS_ERRORS),
    )
    def execute_query(
        self, query: str, variables: Dict, raise_for_error: bool = True
    ) -> Dict:
        """Execute a graphql query."""
        start_time = time.time()
        logger.debug("Executing: " + query.strip().split("\n")[0])
        response = self.session.post(
            self.url,
            timeout=REQUEST_TIMEOUT,
            headers=self.headers,
            data=self.prepare_query(query, variables),
        )
        self._check_status_msg(response.status_code, start_time)
        return self._process_json_response(response.json(), raise_for_error)

    @tenacity.retry(
        reraise=True,
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_not_exception_type(PEERLESS_ERRORS),
    )
    async def execute_query_async(
        self,
        aio_session: aiohttp.ClientSession,
        query: str,
        variables: Dict,
        raise_for_error: bool = True,
    ) -> Dict:
        """Execute a graphql query using asyncio."""
        start_time = time.time()
        logger.debug("Executing async: " + query.strip().split("\n")[0])
        async with aio_session.post(
            self.url,
            timeout=aiohttp.ClientTimeout(REQUEST_TIMEOUT),
            headers=self.headers,
            data=self.prepare_query(query, variables),
        ) as response:
            self._check_status_msg(response.status, start_time)
            return self._process_json_response(await response.json(), raise_for_error)

    @staticmethod
    def _check_status_msg(response_status: int, start_time: float) -> None:
        total_time = time.time() - start_time
        logger.debug(f"Response status: {response_status} took {total_time} seconds")
        if response_status == 413 or response_status >= 500:
            if response_status == 413 or total_time >= 26:
                raise TimeoutError(
                    "Request timed out/too large. Please consider using lower concurrency"
                )
            raise ConnectionError(
                "Internal Server Error: You are probably using an invalid API key"
            )
        if response_status in (401, 403):
            raise PermissionError("Problem authenticating with Api Key")

    @staticmethod
    def _process_json_response(
        response_data: Dict, raise_for_error: bool = True
    ) -> Dict:
        """Process JSON resonse."""
        if "errors" in response_data:
            errors = []
            for error in response_data["errors"]:
                errors.append(error["message"])
                log_error(error["message"])

            if raise_for_error:
                raise ValueError("\n".join(errors))

            del response_data["errors"]

        res = {}
        if "data" in response_data:
            res = response_data["data"]
        else:
            res = response_data
        return res
