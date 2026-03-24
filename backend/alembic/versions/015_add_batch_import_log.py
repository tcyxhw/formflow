"""添加批量导入历史记录表

Revision ID: 015
Revises: 014
Create Date: 2024-03-20 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查表是否已存在
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    
    if 'batch_import_log' in inspector.get_table_names():
        return
    
    # 创建批量导入日志表
    op.create_table('batch_import_log',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('tenant_id', sa.Integer(), nullable=False, comment='租户ID'),
        sa.Column('filename', sa.String(255), nullable=False, comment='导入文件名'),
        sa.Column('total_rows', sa.Integer(), nullable=False, comment='总行数'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0', comment='成功数量'),
        sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0', comment='失败数量'),
        sa.Column('default_password', sa.String(50), nullable=False, comment='使用的默认密码'),
        sa.Column('error_details', sa.Text(), nullable=True, comment='错误详情（JSON格式）'),
        sa.Column('created_by', sa.Integer(), nullable=False, comment='操作人ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], )
    )
    
    # 创建索引
    op.create_index('ix_batch_import_log_id', 'batch_import_log', ['id'])
    op.create_index('ix_batch_import_log_tenant_id', 'batch_import_log', ['tenant_id'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('ix_batch_import_log_tenant_id', table_name='batch_import_log')
    op.drop_index('ix_batch_import_log_id', table_name='batch_import_log')
    
    # 删除表
    op.drop_table('batch_import_log')
