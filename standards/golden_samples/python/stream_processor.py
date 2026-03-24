"""
模块用途: 流式处理正例
依赖配置: 无
数据流向: 输入文件 -> 逐行读取 -> 过滤 -> 聚合
函数清单:
    - stream_non_empty_lines(path): 流式读取非空行
"""

from collections.abc import Generator


def stream_non_empty_lines(path: str) -> Generator[str, None, None]:
    """
    流式读取非空行。

    :param path: 文件路径
    :yields: 非空文本行
    :raises ValueError: 路径为空

    Time: O(N), Space: O(1)
    """
    if not path:
        raise ValueError("path cannot be empty")

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                yield stripped
