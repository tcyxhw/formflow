"""initialize default categories for existing tenants

Revision ID: 007
Revises: 006
Create Date: 2025-03-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 获取数据库连接
    connection = op.get_bind()
    
    # 为每个现有租户创建默认分类
    # 首先获取所有租户
    tenants = connection.execute(text("SELECT id FROM tenant")).fetchall()
    
    for tenant_row in tenants:
        tenant_id = tenant_row[0]
        
        # 检查该租户是否已有默认分类
        existing_default = connection.execute(
            text("SELECT id FROM category WHERE tenant_id = :tenant_id AND is_default = true"),
            {"tenant_id": tenant_id}
        ).fetchone()
        
        if not existing_default:
            # 创建默认分类
            connection.execute(
                text("""
                    INSERT INTO category (tenant_id, name, is_default, created_at, updated_at)
                    VALUES (:tenant_id, 'Uncategorized', true, now(), now())
                """),
                {"tenant_id": tenant_id}
            )
    
    # 获取所有默认分类的ID
    default_categories = connection.execute(
        text("SELECT tenant_id, id FROM category WHERE is_default = true")
    ).fetchall()
    
    # 为每个租户的所有没有分类的表单分配默认分类
    for tenant_id, category_id in default_categories:
        connection.execute(
            text("""
                UPDATE form 
                SET category_id = :category_id 
                WHERE tenant_id = :tenant_id AND category_id IS NULL
            """),
            {"category_id": category_id, "tenant_id": tenant_id}
        )


def downgrade() -> None:
    # 删除所有默认分类
    connection = op.get_bind()
    connection.execute(
        text("DELETE FROM category WHERE is_default = true")
    )
