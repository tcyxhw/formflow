"""
正例: 为真实多实现或测试隔离建立抽象

适用场景:
- 存在多个生产实现（如: MinIO / S3 / 本地文件）
- 或只有一个生产实现，但测试中需要替换为 fake/mock
- 或作为框架/库对外暴露的扩展接口

设计要点:
- 抽象定义契约，不包含实现
- 在 ABC + @abstractmethod 场景中，方法体用 ... 更简洁

参考:
- Python abc 模块文档
"""

from abc import ABC, abstractmethod
import os


class Storage(ABC):
    @abstractmethod
    def upload(self, path: str, content: bytes) -> str: ...

    @abstractmethod
    def exists(self, path: str) -> bool: ...


class MinioStorage(Storage):
    def upload(self, path: str, content: bytes) -> str:
        return f"minio://{path}"

    def exists(self, path: str) -> bool:
        return False


class LocalStorage(Storage):
    def upload(self, path: str, content: bytes) -> str:
        return f"/tmp/{path}"

    def exists(self, path: str) -> bool:
        return os.path.exists(f"/tmp/{path}")


class FakeStorage(Storage):
    """测试用: 即使只有一个生产实现，这个 fake 也证明了抽象的价值。"""

    def __init__(self) -> None:
        self.uploaded: dict[str, bytes] = {}

    def upload(self, path: str, content: bytes) -> str:
        self.uploaded[path] = content
        return f"fake://{path}"

    def exists(self, path: str) -> bool:
        return path in self.uploaded
