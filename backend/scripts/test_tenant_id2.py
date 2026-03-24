"""
测试 tenant_id 直接设置
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.workflow import FlowDefinition
from app.core.database import get_db

db = next(get_db())

# 尝试创建对象并直接设置属性
print("测试1: 在构造函数中传递 tenant_id")
fd1 = FlowDefinition(
    form_id=1,
    version=1,
    name="测试流程1",
    tenant_id=1
)
print(f"  tenant_id value: {fd1.tenant_id}")

print("\n测试2: 创建后设置 tenant_id")
fd2 = FlowDefinition(
    form_id=1,
    version=2,
    name="测试流程2"
)
fd2.tenant_id = 1
print(f"  tenant_id value: {fd2.tenant_id}")

print("\n测试3: 刷新前检查")
fd3 = FlowDefinition(
    form_id=1,
    version=3,
    name="测试流程3"
)
print(f"  tenant_id before flush: {fd3.tenant_id}")
fd3.tenant_id = 1
print(f"  tenant_id after set: {fd3.tenant_id}")

# 尝试添加到数据库
print("\n测试4: 实际插入数据库")
fd4 = FlowDefinition(
    form_id=1,
    version=4,
    name="测试流程4",
    tenant_id=1
)
db.add(fd4)
try:
    db.flush()
    print(f"  插入成功! tenant_id: {fd4.tenant_id}")
    db.rollback()
except Exception as e:
    print(f"  插入失败: {e}")