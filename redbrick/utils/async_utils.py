"""Async utils."""

import asyncio
from contextlib import asynccontextmanager
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Coroutine,
    List,
    Tuple,
    TypeVar,
    Optional,
)
import aiohttp
import tqdm.asyncio  # type: ignore

from redbrick.common.constants import MAX_CONCURRENCY, REQUEST_TIMEOUT
from redbrick.config import config

ReturnType = TypeVar("ReturnType")  # pylint: disable=invalid-name


async def return_value(value: ReturnType) -> ReturnType:
    """Return the same parameter value."""
    return value


async def gather_with_concurrency(
    max_concurrency: int,
    *tasks: Awaitable[ReturnType],
    progress_bar_name: Optional[str] = None,
    keep_progress_bar: bool = False,
    return_exceptions: bool = False,
) -> List[ReturnType]:
    """Utilizes a Semaphore to limit concurrency to n."""
    # pylint: disable=too-many-locals
    if not tasks:
        return []

    max_concurrency = max(1, min(max_concurrency, MAX_CONCURRENCY))

    if not config.log_info:
        keep_progress_bar = False

    if max_concurrency == 1:
        output: List[ReturnType] = []
        progress = (
            tqdm.tqdm(tasks, desc=progress_bar_name, leave=keep_progress_bar)
            if progress_bar_name
            else tasks
        )
        for task in progress:
            try:
                output.append(await task)
            except Exception as exc:  # pylint: disable=broad-except
                if return_exceptions:
                    output.append(exc)  # type: ignore
                else:
                    raise exc
        return output

    semaphore = asyncio.Semaphore(max_concurrency)

    async def sem_task(task: Awaitable[ReturnType]) -> ReturnType:
        async with semaphore:
            return await task

    coros = [sem_task(task) for task in tasks]
    if not progress_bar_name:
        return await asyncio.gather(  # type: ignore
            *coros, return_exceptions=return_exceptions
        )

    async def ordered_coroutine(
        idx: int, task: Coroutine[Any, Any, ReturnType]
    ) -> Tuple[int, bool, ReturnType]:
        """Return the index and result of a task."""
        try:
            return idx, True, await task
        except Exception as exc:  # pylint: disable=broad-except
            return idx, False, exc  # type: ignore

    ordered_coros = [ordered_coroutine(idx, task) for idx, task in enumerate(coros)]
    result: List[Tuple[int, ReturnType]] = []

    for coro in tqdm.asyncio.tqdm.as_completed(
        ordered_coros, desc=progress_bar_name, leave=keep_progress_bar
    ):
        temp: Coroutine[Any, Any, Tuple[int, bool, ReturnType]] = coro
        idx, success, value = await temp
        if not success and not return_exceptions:
            raise value  # type: ignore

        result.append((idx, value))

    return [res[1] for res in sorted(result, key=lambda x: x[0])]


@asynccontextmanager
async def get_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Get async client session."""
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(verify_ssl=config.verify_ssl),
        timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
        trust_env=True,
    ) as session:
        yield session
        await asyncio.sleep(0.250)
