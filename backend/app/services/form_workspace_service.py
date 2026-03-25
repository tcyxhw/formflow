"""
模块用途: 表单填写工作区服务 - 提供可填写表单列表、搜索、筛选、排序、分页功能
依赖配置: 无
数据流向: API -> FormWorkspaceService -> FormPermissionService -> ORM -> 数据库
函数清单:
    - get_fillable_forms(): 获取用户可填写的表单列表（含权限检查、搜索、筛选、排序、分页）
    - add_quick_access(): 添加表单到快捷入口
    - remove_quick_access(): 从快捷入口移除表单
    - get_quick_access_forms(): 获取用户的快捷入口表单列表
    - _compute_form_status(): 计算表单状态（是否过期、是否关闭、是否可填写）
    - _apply_search_filter(): 应用搜索关键词过滤
    - _apply_status_filter(): 应用状态筛选
    - _apply_category_filter(): 应用类别筛选
    - _apply_sorting(): 应用排序
    - _apply_pagination(): 应用分页
"""
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import or_, and_, desc, asc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from app.models.form import Form
from app.models.user import User
from app.models.user_quick_access import UserQuickAccess
from app.schemas.form_permission_schemas import PermissionType
from app.schemas.workspace_schemas import (
    FillableFormsQuery,
    FillableFormItem,
    FillableFormsResponse,
    QuickAccessResponse,
)
from app.services.form_permission_service import FormPermissionService


class FormWorkspaceService:
    """表单填写工作区业务逻辑"""

    @staticmethod
    def get_fillable_forms(
        user_id: int,
        tenant_id: int,
        query: FillableFormsQuery,
        db: Session,
    ) -> FillableFormsResponse:
        """获取用户可填写的表单列表
        
        业务流程：
        1. 查询所有已发布的表单
        2. 通过 FormPermissionService 过滤出用户有 FILL 权限的表单
        3. 应用搜索关键词过滤（标题、描述）
        4. 应用状态和类别筛选
        5. 执行排序
        6. 计算总数
        7. 应用分页
        8. 计算每个表单的状态标识（is_expired, is_closed, can_fill）
        9. 返回分页结果
        
        Args:
            user_id: 用户ID
            tenant_id: 租户ID
            query: 查询参数（分页、搜索、筛选、排序）
            db: 数据库会话
            
        Returns:
            可填写表单列表响应（包含分页信息）
            
        Time: O(N * M), Space: O(N)
        其中 N 为表单数量，M 为权限检查复杂度
        """
        # 第1步：构建基础查询 - 只查询已发布的表单
        base_query = (
            db.query(Form)
            .filter(
                Form.tenant_id == tenant_id,
                Form.status == "published",  # 只显示已发布的表单
            )
        )
        
        # 第2步：获取所有表单并进行权限过滤
        # 注意：这里需要先获取所有表单，然后逐个检查权限
        # 在实际生产环境中，可以优化为批量权限检查
        all_forms = base_query.all()
        
        fillable_forms: List[Form] = []
        for form in all_forms:
            # 检查用户是否有 FILL 权限
            perm_overview = FormPermissionService.get_user_permissions(
                form_id=form.id,
                tenant_id=tenant_id,
                user_id=user_id,
                db=db,
            )
            if perm_overview.can_fill:
                fillable_forms.append(form)
        
        # 第3步：应用搜索关键词过滤
        if query.keyword:
            fillable_forms = FormWorkspaceService._apply_search_filter(
                fillable_forms, query.keyword, query.search_type, db
            )
        
        # 第4步：应用状态筛选
        if query.status:
            fillable_forms = FormWorkspaceService._apply_status_filter(
                fillable_forms, query.status
            )
        
        # 第5步：应用类别筛选
        if query.category:
            fillable_forms = FormWorkspaceService._apply_category_filter(
                fillable_forms, query.category
            )
        
        # 第6步：应用排序
        fillable_forms = FormWorkspaceService._apply_sorting(
            fillable_forms, query.sort_by, query.sort_order
        )
        
        # 第7步：计算总数
        total = len(fillable_forms)
        total_pages = (total + query.page_size - 1) // query.page_size
        
        # 第8步：应用分页
        paginated_forms = FormWorkspaceService._apply_pagination(
            fillable_forms, query.page, query.page_size
        )
        
        # 第9步：构建响应数据，计算表单状态
        items: List[FillableFormItem] = []
        for form in paginated_forms:
            # 获取表单创建者信息
            stmt = select(User).filter(User.id == form.owner_user_id)
            result = db.execute(stmt).scalars()
            owner = result.one_or_none()
            owner_name = owner.name if owner else "未知用户"
            
            # 获取分类名称
            category_name = None
            if form.category_id:
                from app.models.category import Category
                stmt = select(Category).filter(Category.id == form.category_id)
                result = db.execute(stmt).scalars()
                category = result.one_or_none()
                category_name = category.name if category else None
            
            # 计算表单状态
            is_expired, is_closed, is_fill_limit_reached, can_fill = FormWorkspaceService._compute_form_status(form)
            
            # 构建表单项
            item = FillableFormItem(
                id=form.id,
                name=form.name,
                category=category_name,
                status=form.status,
                owner_name=owner_name,
                created_at=form.created_at,
                updated_at=form.updated_at,
                submit_deadline=form.submit_deadline,
                is_expired=is_expired,
                is_closed=is_closed,
                is_fill_limit_reached=is_fill_limit_reached,
                can_fill=can_fill,
                description=None,  # Form 模型中没有 description 字段，暂时设为 None
            )
            items.append(item)
        
        # 返回分页响应
        return FillableFormsResponse(
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
        )

    @staticmethod
    def add_quick_access(
        user_id: int,
        tenant_id: int,
        form_id: int,
        db: Session,
    ) -> UserQuickAccess:
        """添加表单到快捷入口
        
        业务流程：
        1. 检查是否已存在该快捷入口（幂等性）
        2. 如果已存在，直接返回现有记录
        3. 如果不存在，计算新的排序顺序（最大值+1）
        4. 创建新的快捷入口记录
        5. 提交到数据库
        
        Args:
            user_id: 用户ID
            tenant_id: 租户ID
            form_id: 表单ID
            db: 数据库会话
            
        Returns:
            快捷入口记录
            
        Time: O(N), Space: O(1)
        其中 N 为用户的快捷入口数量
        """
        # 第1步：检查是否已存在（去重处理）
        existing = (
            db.query(UserQuickAccess)
            .filter(
                UserQuickAccess.tenant_id == tenant_id,
                UserQuickAccess.user_id == user_id,
                UserQuickAccess.form_id == form_id,
            )
            .first()
        )
        
        # 第2步：如果已存在，直接返回（幂等性）
        if existing:
            return existing
        
        # 第3步：计算新的排序顺序
        # 查询当前用户的最大排序值
        max_sort_order = (
            db.query(UserQuickAccess.sort_order)
            .filter(
                UserQuickAccess.tenant_id == tenant_id,
                UserQuickAccess.user_id == user_id,
            )
            .order_by(UserQuickAccess.sort_order.desc())
            .first()
        )
        
        # 新记录的排序值为最大值+1，如果没有记录则为0
        new_sort_order = (max_sort_order[0] + 1) if max_sort_order else 0
        
        # 第4步：创建新的快捷入口记录
        quick_access = UserQuickAccess(
            tenant_id=tenant_id,
            user_id=user_id,
            form_id=form_id,
            sort_order=new_sort_order,
        )
        
        # 第5步：保存到数据库
        db.add(quick_access)
        db.commit()()
        db.refresh(quick_access)
        
        return quick_access

    @staticmethod
    def remove_quick_access(
        user_id: int,
        tenant_id: int,
        form_id: int,
        db: Session,
    ) -> bool:
        """从快捷入口移除表单
        
        业务流程：
        1. 查找对应的快捷入口记录
        2. 如果存在，删除该记录
        3. 返回是否成功删除
        
        Args:
            user_id: 用户ID
            tenant_id: 租户ID
            form_id: 表单ID
            db: 数据库会话
            
        Returns:
            是否成功删除（True: 删除成功, False: 记录不存在）
            
        Time: O(1), Space: O(1)
        """
        # 第1步：查找快捷入口记录
        quick_access = (
            db.query(UserQuickAccess)
            .filter(
                UserQuickAccess.tenant_id == tenant_id,
                UserQuickAccess.user_id == user_id,
                UserQuickAccess.form_id == form_id,
            )
            .first()
        )
        
        # 第2步：如果不存在，返回False
        if not quick_access:
            return False
        
        # 第3步：删除记录
        db.delete(quick_access)
        db.commit()()
        
        return True

    @staticmethod
    def get_quick_access_forms(
        user_id: int,
        tenant_id: int,
        db: Session,
    ) -> QuickAccessResponse:
        """获取用户的快捷入口表单列表
        
        业务流程：
        1. 查询用户的所有快捷入口记录（按排序顺序）
        2. 获取对应的表单详情
        3. 计算表单状态
        4. 构建响应数据
        
        Args:
            user_id: 用户ID
            tenant_id: 租户ID
            db: 数据库会话
            
        Returns:
            快捷入口表单列表响应
            
        Time: O(N), Space: O(N)
        其中 N 为快捷入口数量
        """
        # 第1步：查询快捷入口记录，按排序顺序
        quick_access_records = (
            db.query(UserQuickAccess)
            .filter(
                UserQuickAccess.tenant_id == tenant_id,
                UserQuickAccess.user_id == user_id,
            )
            .order_by(UserQuickAccess.sort_order.asc())
            .all()
        )
        
        # 第2步：获取表单详情
        items: List[FillableFormItem] = []
        for record in quick_access_records:
            # 查询表单
            stmt = select(Form).filter(Form.id == record.form_id)
            result = db.execute(stmt)
            form = result.scalar_one_or_none()
            
            # 如果表单不存在或已删除，跳过
            if not form:
                continue
            
            # 获取表单创建者信息
            stmt = select(User).filter(User.id == form.owner_user_id)
            result = db.execute(stmt)
            owner = result.scalar_one_or_none()
            owner_name = owner.name if owner else "未知用户"
            
            # 获取分类名称
            category_name = None
            if form.category_id:
                from app.models.category import Category
                stmt = select(Category).filter(Category.id == form.category_id)
                result = db.execute(stmt)
                category = result.scalar_one_or_none()
                category_name = category.name if category else None
            
            # 第3步：计算表单状态
            is_expired, is_closed, is_fill_limit_reached, can_fill = FormWorkspaceService._compute_form_status(form)
            
            # 第4步：构建表单项
            item = FillableFormItem(
                id=form.id,
                name=form.name,
                category=category_name,
                status=form.status,
                owner_name=owner_name,
                created_at=form.created_at,
                updated_at=form.updated_at,
                submit_deadline=form.submit_deadline,
                is_expired=is_expired,
                is_closed=is_closed,
                is_fill_limit_reached=is_fill_limit_reached,
                can_fill=can_fill,
                description=None,  # Form 模型中没有 description 字段
            )
            items.append(item)
        
        # 返回响应
        return QuickAccessResponse(items=items)

    @staticmethod
    def _compute_form_status(form: Form) -> Tuple[bool, bool, bool, bool]:
        """计算表单状态标识
        
        Args:
            form: 表单对象
            
        Returns:
            (is_expired, is_closed, is_fill_limit_reached, can_fill) 元组
            - is_expired: 是否已过期（超过截止时间）
            - is_closed: 是否已关闭（状态为 archived）
            - is_fill_limit_reached: 是否达到填写上限
            - can_fill: 是否可以填写（未过期且未关闭且未达上限）
            
        Time: O(1), Space: O(1)
        """
        now = datetime.utcnow()
        
        # 检查是否过期
        is_expired = False
        if form.submit_deadline:
            is_expired = now > form.submit_deadline
        
        # 检查是否关闭
        is_closed = form.status == "archived"
        
        # 检查是否达到填写上限
        is_fill_limit_reached = False
        max_submissions = getattr(form, 'max_submissions', None)
        current_submissions = getattr(form, 'current_submissions', 0)
        if max_submissions is not None:
            is_fill_limit_reached = current_submissions >= max_submissions
        
        # 可填写条件：未过期且未关闭且未达上限
        can_fill = not is_expired and not is_closed and not is_fill_limit_reached
        
        return is_expired, is_closed, is_fill_limit_reached, can_fill

    @staticmethod
    def _apply_search_filter(forms: List[Form], keyword: str, search_type: str = "name", db: Session = None) -> List[Form]:
        """应用搜索关键词过滤
        
        搜索范围：表单标题（name）或发布人（owner_name）
        
        Args:
            forms: 表单列表
            keyword: 搜索关键词
            search_type: 搜索类型，name 或 owner
            db: 数据库会话（按发布人搜索时需要）
            
        Returns:
            过滤后的表单列表
            
        Time: O(N), Space: O(N)
        """
        if not keyword:
            return forms
        
        keyword_lower = keyword.lower().strip()
        if not keyword_lower:
            return forms
        
        filtered_forms = []
        for form in forms:
            if search_type == "name":
                # 搜索表单标题
                if form.name and keyword_lower in form.name.lower():
                    filtered_forms.append(form)
            elif search_type == "owner" and db:
                # 搜索发布人
                from app.models.user import User
                from sqlalchemy import select
                stmt = select(User).filter(User.id == form.owner_user_id)
                result = db.execute(stmt).scalars()
                owner = result.one_or_none()
                if owner and owner.name and keyword_lower in owner.name.lower():
                    filtered_forms.append(form)
        
        return filtered_forms

    @staticmethod
    def _apply_status_filter(forms: List[Form], status: str) -> List[Form]:
        """应用状态筛选
        
        Args:
            forms: 表单列表
            status: 状态筛选条件
            
        Returns:
            过滤后的表单列表
            
        Time: O(N), Space: O(N)
        """
        if not status:
            return forms
        
        filtered_forms = []
        now = datetime.utcnow()
        
        for form in forms:
            is_expired, is_closed, is_fill_limit_reached, can_fill = FormWorkspaceService._compute_form_status(form)
            
            # 根据状态筛选条件进行过滤
            if status == "active" and can_fill:
                filtered_forms.append(form)
            elif status == "expired" and is_expired:
                filtered_forms.append(form)
            elif status == "closed" and is_closed:
                filtered_forms.append(form)
        
        return filtered_forms

    @staticmethod
    def _apply_category_filter(forms: List[Form], category: str) -> List[Form]:
        """应用类别筛选
        
        Args:
            forms: 表单列表
            category: 类别筛选条件（分类名称）
            
        Returns:
            过滤后的表单列表
            
        Time: O(N), Space: O(N)
        """
        if not category:
            return forms
        
        # 通过分类名称过滤（需要访问关系属性 category_obj）
        return [form for form in forms if form.category_obj and form.category_obj.name == category]

    @staticmethod
    def _apply_sorting(
        forms: List[Form], sort_by: str, sort_order: str
    ) -> List[Form]:
        """应用排序
        
        支持的排序字段：
        - created_at: 创建时间
        - updated_at: 更新时间
        - submit_deadline: 截止时间
        - name: 表单名称
        
        Args:
            forms: 表单列表
            sort_by: 排序字段
            sort_order: 排序方向（asc/desc）
            
        Returns:
            排序后的表单列表
            
        Time: O(N log N), Space: O(N)
        """
        reverse = (sort_order == "desc")
        
        # 根据排序字段选择排序键
        if sort_by == "created_at":
            forms.sort(key=lambda f: f.created_at or datetime.min, reverse=reverse)
        elif sort_by == "updated_at":
            forms.sort(key=lambda f: f.updated_at or datetime.min, reverse=reverse)
        elif sort_by == "submit_deadline":
            # 截止时间排序：None 值放在最后
            forms.sort(
                key=lambda f: (f.submit_deadline is None, f.submit_deadline or datetime.max),
                reverse=reverse,
            )
        elif sort_by == "name":
            forms.sort(key=lambda f: f.name or "", reverse=reverse)
        else:
            # 默认按创建时间倒序
            forms.sort(key=lambda f: f.created_at or datetime.min, reverse=True)
        
        return forms

    @staticmethod
    def _apply_pagination(
        forms: List[Form], page: int, page_size: int
    ) -> List[Form]:
        """应用分页
        
        Args:
            forms: 表单列表
            page: 页码（从1开始）
            page_size: 每页数量
            
        Returns:
            分页后的表单列表
            
        Time: O(1), Space: O(page_size)
        """
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        return forms[start_index:end_index]
