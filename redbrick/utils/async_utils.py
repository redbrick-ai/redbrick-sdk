"""Async utils."""

import asyncio
from typing import Generator, Sequence, Awaitable, List, TypeVar

ReturnType = TypeVar("ReturnType")


async def gather_with_concurrency(
    max_concurrency: int, *tasks: Awaitable[ReturnType]
) -> List[ReturnType]:
    """Utilizes a Semaphore to limit concurrency to n."""
    semaphore = asyncio.Semaphore(max_concurrency)

    async def sem_task(task: Awaitable[ReturnType]) -> ReturnType:
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))
