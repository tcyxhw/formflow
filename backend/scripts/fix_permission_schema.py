"""修复 form_permission 表结构"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from sqlalchemy import text

def fix_schema():
    with engine.connect() as conn:
        # 添加缺失的列
        conn.execute(text("""
            ALTER TABLE form_permission 
            ADD COLUMN IF NOT EXISTS include_children BOOLEAN DEFAULT TRUE
        """))
        conn.commit()
        print("✅ 已添加 include_children 列")

if __name__ == "__main__":
    fix_schema()
