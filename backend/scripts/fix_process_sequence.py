#!/usr/bin/env python3
"""
修复 process_instance 表的主键序列
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import get_db

def fix_process_instance_sequence():
    """修复 process_instance 表的主键序列"""
    
    db = next(get_db())
    
    try:
        print("=" * 80)
        print("修复 process_instance 表的主键序列")
        print("=" * 80)
        
        # 1. 查询当前表中的最大ID
        query = text("SELECT MAX(id) FROM process_instance")
        result = db.execute(query).fetchone()
        max_id = result[0] if result and result[0] else 0
        
        print(f"\n当前 process_instance 表的最大ID: {max_id}")
        
        # 2. 重置序列
        reset_query = text(f"SELECT setval('process_instance_id_seq', {max_id})")
        db.execute(reset_query)
        db.commit()
        
        print(f"序列已重置为: {max_id}")
        
        # 3. 验证序列值
        verify_query = text("SELECT nextval('process_instance_id_seq')")
        result = db.execute(verify_query).fetchone()
        next_val = result[0] if result else None
        
        print(f"下一个序列值: {next_val}")
        
        print("\n" + "=" * 80)
        print("修复完成")
        print("=" * 80)
        
    finally:
        db.close()


if __name__ == "__main__":
    fix_process_instance_sequence()
