"""
修复 tenant_id 默认值
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # 为所有 workflow 相关表设置 tenant_id 默认值
    tables = ['flow_definition', 'flow_node', 'flow_route', 'flow_snapshot', 'process_instance', 'task', 'task_action_log']
    for table in tables:
        try:
            conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET DEFAULT 1"))
            print(f"  设置 {table}.tenant_id 默认值成功")
        except Exception as e:
            print(f"  设置 {table}.tenant_id 默认值失败: {e}")
    
    conn.commit()