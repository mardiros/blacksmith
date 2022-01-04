import asyncio
import time


async def AsyncSleep(ttl: float):
    await asyncio.sleep(ttl)


def SyncSleep(ttl: float):
    time.sleep(ttl)
