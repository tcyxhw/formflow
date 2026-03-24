# reset_database.py
"""
数据库重置脚本
"""
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.core.database import reset_db, init_db

# -- 重新插入租户数据
# INSERT INTO tenant (name, created_at, updated_at) VALUES
# ('仲恺农业工程学院', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
# ('中山大学', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
# ('华南理工大学', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
# ('暨南大学', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
# ('华南师范大学', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
# ('华南农业大学', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
# ('深圳大学', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
# ('南方科技大学', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
# ('广东工业大学', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
# ('汕头大学', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
# ('广州大学', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
def main():
    """主函数"""
    print("数据库重置工具")
    print("=" * 40)

    # 确认操作
    confirm = input("⚠️ 这将删除所有数据，确定要继续吗？(输入 'yes' 确认): ")

    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return

    try:
        print("\n🔄 开始重置数据库...")
        reset_db()
        print("✅ 数据库重置成功！")

    except Exception as e:
        print(f"❌ 重置失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()