"""
模块用途: 表单分类业务逻辑服务
依赖配置: SQLAlchemy, Pydantic
数据流向: 请求 -> 验证 -> 数据库操作 -> 响应
函数清单:
    - create_category(): 创建分类
    - get_categories(): 获取分类列表
    - get_category(): 获取单个分类
    - update_category(): 更新分类
    - delete_category(): 删除分类（级联处理）
    - get_default_category(): 获取默认分类
    - initialize_default_category(): 初始化默认分类
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy import func, or_
from typing import Tuple, List, Optional
from app.models.category import Category
from app.models.form import Form
from app.core.exceptions import ValidationError, ConflictError, NotFoundError, AuthorizationError
from app.core.logger import logger


class CategoryService:
    """表单分类服务"""

    @staticmethod
    def create_category(
            tenant_id: int,
            name: str,
            db: Session
    ) -> Category:
        """
        创建分类

        Args:
            tenant_id: 租户ID
            name: 分类名称
            db: 数据库会话

        Returns:
            创建的分类对象

        Raises:
            ValidationError: 名称验证失败
            ConflictError: 分类名称已存在
        """
        # 验证名称
        if not name or len(name.strip()) == 0:
            raise ValidationError("分类名称不能为空")
        
        if len(name) > 50:
            raise ValidationError("分类名称不能超过50个字符")

        # 检查重复
        stmt = select(Category).filter(
            Category.tenant_id == tenant_id,
            Category.name == name
        )
        result = db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ConflictError("该分类名称已存在")

        # 创建分类
        category = Category(
            tenant_id=tenant_id,
            name=name,
            is_default=False
        )

        db.add(category)
        db.commit()
        db.refresh(category)

        logger.info(f"Created category: id={category.id}, name={name}, tenant={tenant_id}")
        return category

    @staticmethod
    def get_categories(
            tenant_id: int,
            page: int = 1,
            page_size: int = 20,
            db: Session = None
    ) -> Tuple[List[Category], int]:
        """
        获取分类列表（分页）

        Args:
            tenant_id: 租户ID
            page: 页码
            page_size: 每页数量
            db: 数据库会话

        Returns:
            (分类列表, 总数)
        """
        stmt = select(Category).filter(Category.tenant_id == tenant_id)
        result = db.execute(stmt)
        query = result.all()

        # 统计总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        categories = query.order_by(
            Category.is_default.desc(),  # 默认分类优先
            Category.created_at.asc()
        ).offset(offset).limit(page_size).all()

        return categories, total

    @staticmethod
    def get_category(
            category_id: int,
            tenant_id: int,
            db: Session
    ) -> Category:
        """
        获取单个分类

        Args:
            category_id: 分类ID
            tenant_id: 租户ID
            db: 数据库会话

        Returns:
            分类对象

        Raises:
            NotFoundError: 分类不存在
            AuthorizationError: 跨租户访问
        """
        stmt = select(Category).filter(
            Category.id == category_id,
            Category.tenant_id == tenant_id
        )
        result = db.execute(stmt)
        category = result.scalar_one_or_none()

        if not category:
            raise NotFoundError("分类不存在")

        return category

    @staticmethod
    def update_category(
            category_id: int,
            tenant_id: int,
            name: str,
            db: Session
    ) -> Category:
        """
        更新分类

        Args:
            category_id: 分类ID
            tenant_id: 租户ID
            name: 新名称
            db: 数据库会话

        Returns:
            更新后的分类对象

        Raises:
            ValidationError: 名称验证失败
            ConflictError: 新名称已存在
            NotFoundError: 分类不存在
        """
        # 验证名称
        if not name or len(name.strip()) == 0:
            raise ValidationError("分类名称不能为空")
        
        if len(name) > 50:
            raise ValidationError("分类名称不能超过50个字符")

        # 获取分类
        category = CategoryService.get_category(category_id, tenant_id, db)

        # 检查新名称是否重复（排除自己）
        stmt = select(Category).filter(
            Category.tenant_id == tenant_id,
            Category.name == name,
            Category.id != category_id
        )
        result = db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ConflictError("该分类名称已存在")

        # 更新
        category.name = name
        db.commit()()
        db.refresh(category)

        logger.info(f"Updated category: id={category_id}, name={name}, tenant={tenant_id}")
        return category

    @staticmethod
    def delete_category(
            category_id: int,
            tenant_id: int,
            db: Session
    ) -> None:
        """
        删除分类（级联处理）

        删除分类时，将该分类下的所有表单重新分配到默认分类

        Args:
            category_id: 分类ID
            tenant_id: 租户ID
            db: 数据库会话

        Raises:
            ValidationError: 尝试删除默认分类
            NotFoundError: 分类不存在
        """
        # 获取分类
        category = CategoryService.get_category(category_id, tenant_id, db)

        # 防止删除默认分类
        if category.is_default:
            raise ValidationError("不能删除默认分类")

        # 获取默认分类
        default_category = CategoryService.get_default_category(tenant_id, db)

        if not default_category:
            raise ValidationError("租户没有默认分类，无法删除")

        # 将该分类下的所有表单重新分配到默认分类
        stmt = select(Form).filter(
            Form.tenant_id == tenant_id,
            Form.category_id == category_id
        )
        result = db.execute(stmt)
        records = result.scalars().all()
        for record in records:
            for key, value in {Form.category_id: default_category.id}.items():
                setattr(record, key, value)

        # 删除分类
        db.delete(category)
        db.commit()()

        logger.info(f"Deleted category: id={category_id}, tenant={tenant_id}, reassigned to default={default_category.id}")

    @staticmethod
    def get_default_category(
            tenant_id: int,
            db: Session
    ) -> Optional[Category]:
        """
        获取租户的默认分类

        Args:
            tenant_id: 租户ID
            db: 数据库会话

        Returns:
            默认分类对象，如果不存在则返回None
        """
        return db.query(Category).filter(
            Category.tenant_id == tenant_id,
            Category.is_default == True
        ).first()

    @staticmethod
    def initialize_default_category(
            tenant_id: int,
            db: Session
    ) -> Category:
        """
        为租户初始化默认分类

        如果默认分类已存在，则返回现有的；否则创建新的

        Args:
            tenant_id: 租户ID
            db: 数据库会话

        Returns:
            默认分类对象
        """
        # 检查是否已存在
        existing = CategoryService.get_default_category(tenant_id, db)
        if existing:
            return existing

        # 创建默认分类
        default_category = Category(
            tenant_id=tenant_id,
            name="Uncategorized",
            is_default=True
        )

        db.add(default_category)
        db.commit()()
        db.refresh(default_category)

        logger.info(f"Initialized default category: id={default_category.id}, tenant={tenant_id}")
        return default_category
