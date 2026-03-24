"""
反例: 裸 except
"""

import json


def bad_parse(data: str):
    try:
        return json.loads(data)
    except:
        return None
