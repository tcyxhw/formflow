"""
调试 tenant.id
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.user import Tenant

db = next(get_db())

# 查找或创建租户
tenant = db.query(Tenant).filter(Tenant.name == "测试高校").first()
if not tenant:
    tenant = Tenant(name="测试高校")
    db.add(tenant)
    db.flush()
    print(f"  创建租户: {tenant.name} (ID: {tenant.id})")
else:
    print(f"  找到租户: {tenant.name} (ID: {tenant.id})")

print(f"  tenant.id = {tenant.id}")
print(f"  type(tenant.id) = {type(tenant.id)}")

# 尝试创建 FlowDefinition
from app.models.workflow import FlowDefinition

fd = FlowDefinition(
    form_id=1,
    version=1,
    name="测试流程",
    tenant_id=tenant.id
)
print(f"  fd.tenant_id = {fd.tenant_id}")

db.add(fd)
try:
    db.flush()
    print(f"  插入成功!")
    db.rollback()
except Exception as e:
    print(f"  插入失败: {e}")