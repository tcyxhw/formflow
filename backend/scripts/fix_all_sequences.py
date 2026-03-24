#!/usr/bin/env python3
"""
修复所有表的主键序列
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import get_db

def fix_all_sequences():
    """修复所有表的主键序列"""
    
    db = next(get_db())
    
    try:
        print("=" * 80)
        print("修复所有表的主键序列")
        print("=" * 80)
        
        # 需要修复的表
        tables = [
            'process_instance',
            'task',
            'task_action_log',
            'flow_node',
            'flow_route',
            'flow_snapshot',
            'flow_draft',
            'flow_definition',
        ]
        
        for table in tables:
            try:
                # 查询当前表中的最大ID
                query = text(f"SELECT MAX(id) FROM {table}")
                result = db.execute(query).fetchone()
                max_id = result[0] if result and result[0] else 0
                
                # 重置序列
                reset_query = text(f"SELECT setval('{table}_id_seq', {max_id})")
                db.execute(reset_query)
                
                print(f"  - {table}: 序列已重置为 {max_id}")
                
            except Exception as e:
                print(f"  - {table}: 修复失败 - {e}")
        
        db.commit()
        
        print("\n" + "=" * 80)
        print("修复完成")
        print("=" * 80)
        
    finally:
        db.close()


if __name__ == "__main__":
    fix_all_sequences()
