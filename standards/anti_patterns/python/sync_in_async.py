"""
反例: 在 async 中调用阻塞 IO
"""

import requests


async def bad_fetch(url: str):
    response = requests.get(url, timeout=10)
    return response.json()
