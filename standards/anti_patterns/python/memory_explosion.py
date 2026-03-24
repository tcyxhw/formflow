"""
反例: 大文件一次性载入内存
"""

def bad_read_all(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()
