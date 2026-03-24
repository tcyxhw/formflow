"""
测试 tenant_id 是否正确工作
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.workflow import FlowDefinition
from app.core.database import get_db

db = next(get_db())

# 检查 FlowDefinition 的映射
print("FlowDefinition columns:")
for column in FlowDefinition.__table__.columns:
    print(f"  {column.name}: {column.type}, nullable={column.nullable}, default={column.default}")

# 检查 tenant_id 列
tenant_id_col = FlowDefinition.__table__.columns.get('tenant_id')
if tenant_id_col is not None:
    print(f"\ntenant_id column found: nullable={tenant_id_col.nullable}, default={tenant_id_col.default}")
else:
    print("\ntenant_id column NOT found in table!")

# 尝试创建一个简单的对象
print("\n尝试创建 FlowDefinition 对象...")
fd = FlowDefinition(
    form_id=1,
    version=1,
    name="测试流程"
)
print(f"  Created object")
print(f"  tenant_id value (before commit): {getattr(fd, 'tenant_id', 'NOT SET')}")

# 尝试显式设置
fd2 = FlowDefinition(
    form_id=1,
    version=2,
    name="测试流程2",
    tenant_id=1
)
print(f"  tenant_id value (explicit): {getattr(fd2, 'tenant_id', 'NOT SET')}")