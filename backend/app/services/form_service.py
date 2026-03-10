# app/services/form_service.py
"""
表单业务逻辑服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.models.form import Form, FormVersion
from app.schemas.form_schemas import (
    FormCreateRequest, FormUpdateRequest, FormQueryRequest,
    FormStatus
)
from app.core.exceptions import (
    NotFoundError, ValidationError, BusinessError, AuthorizationError
)
from app.services.formula_service import FormulaService
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FormService:
    """表单服务"""

    @staticmethod
    def create_form(
            request: FormCreateRequest,
            tenant_id: int,
            user_id: int,
            db: Session
    ) -> Form:
        """
        创建表单（草稿状态）

        Args:
            request: 创建请求
            tenant_id: 租户ID
            user_id: 创建者ID
            db: 数据库会话

        Returns:
            创建的表单对象
        """
        # ✅ 校验配置（使用新字段名）
        if request.form_schema:
            FormService._validate_schema(request.form_schema.model_dump())

        # 创建表单
        form = Form(
            tenant_id=tenant_id,
            name=request.name,
            category=request.category,
            access_mode=request.access_mode.value,
            owner_user_id=user_id,
            status=FormStatus.DRAFT.value,
            submit_deadline=request.submit_deadline,
            allow_edit=request.allow_edit,
            max_edit_count=request.max_edit_count
        )

        db.add(form)
        db.flush()  # 获取ID但不提交

        # ✅ 如果提供了配置，创建第一个版本（草稿版本）
        if request.form_schema:
            version = FormVersion(
                tenant_id=tenant_id,
                form_id=form.id,
                version=0,  # 版本0表示草稿
                # ✅ Pydantic字段名 → 数据库字段名
                schema_json=request.form_schema.model_dump() if request.form_schema else None,
                ui_schema_json=request.ui_schema.model_dump() if request.ui_schema else None,
                logic_json=request.logic_json.model_dump() if request.logic_json else None,  # ✅ 修复
                published_at=None
            )
            db.add(version)

        db.commit()
        db.refresh(form)

        logger.info(f"Created form: id={form.id}, name={form.name}, tenant={tenant_id}")
        return form

    @staticmethod
    def update_form(
            form_id: int,
            request: FormUpdateRequest,
            tenant_id: int,
            user_id: int,
            db: Session
    ) -> Form:
        """更新表单"""
        # 查询表单
        form = FormService.get_form_by_id(form_id, tenant_id, db)

        # 权限检查
        if form.owner_user_id != user_id:
            raise AuthorizationError("只有创建者可以编辑表单")

        # ❌ 删除这段限制代码
        # if form.status == FormStatus.PUBLISHED.value:
        #     if request.form_schema or request.ui_schema or request.logic_json:
        #         raise BusinessError("已发布的表单不能修改配置，请先取消发布或创建新版本")

        # 更新基础信息
        if request.name is not None:
            form.name = request.name
        if request.category is not None:
            form.category = request.category
        if request.access_mode is not None:
            form.access_mode = request.access_mode.value
        if request.submit_deadline is not None:
            form.submit_deadline = request.submit_deadline
        if request.allow_edit is not None:
            form.allow_edit = request.allow_edit
        if request.max_edit_count is not None:
            form.max_edit_count = request.max_edit_count

        # ✅ 修改配置：始终允许更新草稿版本（不管表单状态）
        if request.form_schema or request.ui_schema or request.logic_json:
            # 校验配置
            if request.form_schema:
                FormService._validate_schema(request.form_schema.model_dump())

            # 查询草稿版本
            draft_version = db.query(FormVersion).filter(
                FormVersion.form_id == form_id,
                FormVersion.version == 0
            ).first()

            if not draft_version:
                # ✅ 如果没有草稿版本，创建一个
                # 对于已发布的表单，复制最新版本作为草稿基础
                if form.status == FormStatus.PUBLISHED.value:
                    latest_version = db.query(FormVersion).filter(
                        FormVersion.form_id == form_id,
                        FormVersion.version > 0
                    ).order_by(FormVersion.version.desc()).first()

                    draft_version = FormVersion(
                        tenant_id=tenant_id,
                        form_id=form_id,
                        version=0,
                        schema_json=latest_version.schema_json if latest_version else None,
                        ui_schema_json=latest_version.ui_schema_json if latest_version else None,
                        logic_json=latest_version.logic_json if latest_version else None,
                        published_at=None
                    )
                else:
                    # 草稿状态，创建空草稿
                    draft_version = FormVersion(
                        tenant_id=tenant_id,
                        form_id=form_id,
                        version=0,
                        schema_json=None,
                        ui_schema_json=None,
                        logic_json=None,
                        published_at=None
                    )

                db.add(draft_version)
                db.flush()

            # ✅ 更新配置（无论表单状态）
            if request.form_schema:
                draft_version.schema_json = request.form_schema.model_dump()
            if request.ui_schema:
                draft_version.ui_schema_json = request.ui_schema.model_dump()
            if request.logic_json:
                draft_version.logic_json = request.logic_json.model_dump()

        db.commit()
        db.refresh(form)

        logger.info(f"Updated form: id={form_id}, tenant={tenant_id}")
        return form

    @staticmethod
    def publish_form(
            form_id: int,
            tenant_id: int,
            user_id: int,
            db: Session,
            flow_definition_id: Optional[int] = None
    ) -> FormVersion:
        """
        发布表单（创建新版本）

        Args:
            form_id: 表单ID
            tenant_id: 租户ID
            user_id: 当前用户ID
            db: 数据库会话
            flow_definition_id: 关联流程定义ID（可选）

        Returns:
            新创建的版本对象
        """
        # 查询表单
        form = FormService.get_form_by_id(form_id, tenant_id, db)

        # 权限检查
        if form.owner_user_id != user_id:
            raise AuthorizationError("只有创建者可以发布表单")

        # 查询草稿版本
        draft_version = db.query(FormVersion).filter(
            FormVersion.form_id == form_id,
            FormVersion.version == 0
        ).first()

        if not draft_version or not draft_version.schema_json:
            raise ValidationError("表单配置不完整，无法发布")

        # 校验配置
        FormService._validate_schema(draft_version.schema_json)

        # 如果指定了流程定义，验证流程存在且属于当前租户
        if flow_definition_id:
            from app.models.workflow import FlowDefinition
            flow = db.query(FlowDefinition).filter(
                FlowDefinition.id == flow_definition_id,
                FlowDefinition.tenant_id == tenant_id
            ).first()
            if not flow:
                raise ValidationError("指定的流程定义不存在")
            # 绑定流程到表单
            form.flow_definition_id = flow_definition_id
            logger.info(f"Bound flow {flow_definition_id} to form {form_id}")

        # 查询当前最大版本号
        max_version = db.query(func.max(FormVersion.version)).filter(
            FormVersion.form_id == form_id,
            FormVersion.version > 0
        ).scalar() or 0

        new_version_num = max_version + 1

        # 创建新版本（复制草稿配置）
        new_version = FormVersion(
            tenant_id=tenant_id,
            form_id=form_id,
            version=new_version_num,
            schema_json=draft_version.schema_json,
            ui_schema_json=draft_version.ui_schema_json,
            logic_json=draft_version.logic_json,
            published_at=datetime.now()
        )
        db.add(new_version)

        # 更新表单状态
        form.status = FormStatus.PUBLISHED.value

        db.commit()
        db.refresh(new_version)

        logger.info(f"Published form: id={form_id}, version={new_version_num}, tenant={tenant_id}")
        return new_version

    @staticmethod
    def unpublish_form(
            form_id: int,
            tenant_id: int,
            user_id: int,
            db: Session
    ) -> Form:
        """
        取消发布表单（改为草稿状态）

        Args:
            form_id: 表单ID
            tenant_id: 租户ID
            user_id: 当前用户ID
            db: 数据库会话

        Returns:
            更新后的表单对象
        """
        form = FormService.get_form_by_id(form_id, tenant_id, db)

        if form.owner_user_id != user_id:
            raise AuthorizationError("只有创建者可以取消发布")

        if form.status != FormStatus.PUBLISHED.value:
            raise BusinessError("表单未发布")

        # 检查是否有提交记录
        from app.models.form import Submission
        has_submissions = db.query(Submission).filter(
            Submission.form_id == form_id
        ).count() > 0

        if has_submissions:
            raise BusinessError("已有提交记录的表单不能取消发布，建议归档")

        form.status = FormStatus.DRAFT.value
        db.commit()
        db.refresh(form)

        logger.info(f"Unpublished form: id={form_id}, tenant={tenant_id}")
        return form

    @staticmethod
    def archive_form(
            form_id: int,
            tenant_id: int,
            user_id: int,
            db: Session
    ) -> Form:
        """归档表单"""
        form = FormService.get_form_by_id(form_id, tenant_id, db)

        if form.owner_user_id != user_id:
            raise AuthorizationError("只有创建者可以归档表单")

        form.status = FormStatus.ARCHIVED.value
        db.commit()
        db.refresh(form)

        logger.info(f"Archived form: id={form_id}, tenant={tenant_id}")
        return form

    @staticmethod
    def delete_form(
            form_id: int,
            tenant_id: int,
            user_id: int,
            db: Session
    ) -> bool:
        """
        删除表单（软删除，只能删除草稿状态的表单）

        Args:
            form_id: 表单ID
            tenant_id: 租户ID
            user_id: 当前用户ID
            db: 数据库会话

        Returns:
            是否删除成功
        """
        form = FormService.get_form_by_id(form_id, tenant_id, db)

        if form.owner_user_id != user_id:
            raise AuthorizationError("只有创建者可以删除表单")

        if form.status != FormStatus.DRAFT.value:
            raise BusinessError("只能删除草稿状态的表单，已发布的表单请归档")

        # 删除关联的版本
        db.query(FormVersion).filter(
            FormVersion.form_id == form_id
        ).delete()

        # 删除表单
        db.delete(form)
        db.commit()

        logger.info(f"Deleted form: id={form_id}, tenant={tenant_id}")
        return True

    @staticmethod
    def get_form_by_id(
            form_id: int,
            tenant_id: int,
            db: Session,
            include_config: bool = False
    ) -> Form:
        """
        根据ID查询表单

        Args:
            form_id: 表单ID
            tenant_id: 租户ID
            db: 数据库会话
            include_config: 是否包含配置信息

        Returns:
            表单对象
        """
        form = db.query(Form).filter(
            Form.id == form_id,
            Form.tenant_id == tenant_id
        ).first()

        if not form:
            raise NotFoundError(f"表单不存在: id={form_id}")

        return form

    @staticmethod
    def get_form_detail(
            form_id: int,
            tenant_id: int,
            db: Session
    ) -> Tuple[Form, Optional[FormVersion], List[FormVersion]]:
        """
        获取表单详情（包含当前配置和版本历史）

        Returns:
            (表单对象, 当前版本, 版本历史列表)
        """
        form = FormService.get_form_by_id(form_id, tenant_id, db)

        # 获取当前生效的版本
        if form.status == FormStatus.PUBLISHED.value:
            # 已发布：使用最新发布版本
            current_version = db.query(FormVersion).filter(
                FormVersion.form_id == form_id,
                FormVersion.version > 0
            ).order_by(FormVersion.version.desc()).first()
        else:
            # 草稿：使用草稿版本
            current_version = db.query(FormVersion).filter(
                FormVersion.form_id == form_id,
                FormVersion.version == 0
            ).first()

        # 获取版本历史（不包括草稿版本）
        versions = db.query(FormVersion).filter(
            FormVersion.form_id == form_id,
            FormVersion.version > 0
        ).order_by(FormVersion.version.desc()).all()

        return form, current_version, versions

    @staticmethod
    def list_forms(
            request: FormQueryRequest,
            tenant_id: int,
            user_id: Optional[int] = None,
            db: Session = None
    ) -> Tuple[List[Form], int]:
        """
        查询表单列表

        Args:
            request: 查询请求
            tenant_id: 租户ID
            user_id: 当前用户ID（可选，用于权限过滤）
            db: 数据库会话

        Returns:
            (表单列表, 总数)
        """
        query = db.query(Form).filter(Form.tenant_id == tenant_id)

        # 关键词搜索
        if request.keyword:
            query = query.filter(
                or_(
                    Form.name.ilike(f"%{request.keyword}%"),
                    Form.category.ilike(f"%{request.keyword}%")
                )
            )

        # 分类筛选
        if request.category:
            query = query.filter(Form.category == request.category)

        # 状态筛选
        if request.status:
            query = query.filter(Form.status == request.status.value)

        # 创建者筛选
        if request.owner_user_id:
            query = query.filter(Form.owner_user_id == request.owner_user_id)

        # 先统计总数（使用 func.count 避免子查询问题）
        total = db.query(func.count(Form.id)).filter(Form.tenant_id == tenant_id).scalar()

        # 重新应用筛选条件
        query = db.query(Form).filter(Form.tenant_id == tenant_id)

        if request.keyword:
            query = query.filter(
                or_(
                    Form.name.ilike(f"%{request.keyword}%"),
                    Form.category.ilike(f"%{request.keyword}%")
                )
            )

        if request.category:
            query = query.filter(Form.category == request.category)

        if request.status:
            query = query.filter(Form.status == request.status.value)

        if request.owner_user_id:
            query = query.filter(Form.owner_user_id == request.owner_user_id)

        # 分页
        offset = (request.page - 1) * request.page_size
        forms = query.order_by(Form.created_at.desc()).offset(offset).limit(request.page_size).all()

        return forms, total

    @staticmethod
    def get_form_statistics(
            form_id: int,
            tenant_id: int,
            db: Session
    ) -> Dict[str, Any]:
        """
        获取表单统计信息

        Returns:
            {
                "total_submissions": 提交总数,
                "total_versions": 版本总数,
                "current_version": 当前版本号
            }
        """
        from app.models.form import Submission

        form = FormService.get_form_by_id(form_id, tenant_id, db)

        # 统计提交数
        total_submissions = db.query(func.count(Submission.id)).filter(
            Submission.form_id == form_id
        ).scalar()

        # 统计版本数
        total_versions = db.query(func.count(FormVersion.id)).filter(
            FormVersion.form_id == form_id,
            FormVersion.version > 0
        ).scalar()

        # 当前版本号
        current_version = db.query(func.max(FormVersion.version)).filter(
            FormVersion.form_id == form_id,
            FormVersion.version > 0
        ).scalar() or 0

        return {
            "total_submissions": total_submissions or 0,
            "total_versions": total_versions or 0,
            "current_version": current_version
        }

    @staticmethod
    def _validate_schema(schema_json: Dict[str, Any]) -> None:
        """
        校验表单Schema

        Args:
            schema_json: 表单配置

        Raises:
            ValidationError: 校验失败
        """
        if not schema_json:
            raise ValidationError("表单配置不能为空")

        fields = schema_json.get("fields", [])
        if not fields:
            raise ValidationError("表单至少需要一个字段")

        # 检查字段ID唯一性
        field_ids = [f.get("id") for f in fields]
        if len(field_ids) != len(set(field_ids)):
            raise ValidationError("字段ID必须唯一")

        # 检查必需字段
        for field in fields:
            if not field.get("id"):
                raise ValidationError("字段必须有ID")
            if not field.get("type"):
                raise ValidationError(f"字段 {field.get('id')} 缺少类型")
            if not field.get("label"):
                raise ValidationError(f"字段 {field.get('id')} 缺少标签")

        # 检查计算字段的循环依赖
        calculated_fields = [f for f in fields if f.get("type") == "calculated"]
        if calculated_fields:
            if FormulaService.check_circular_dependency(fields):
                raise ValidationError("检测到计算字段循环依赖")

        logger.debug(f"Schema validation passed: {len(fields)} fields")

    @staticmethod
    def clone_form(
            form_id: int,
            new_name: str,
            tenant_id: int,
            user_id: int,
            db: Session
    ) -> Form:
        """
        克隆表单

        Args:
            form_id: 源表单ID
            new_name: 新表单名称
            tenant_id: 租户ID
            user_id: 当前用户ID
            db: 数据库会话

        Returns:
            新创建的表单
        """
        # 获取源表单和配置
        source_form, source_version, _ = FormService.get_form_detail(form_id, tenant_id, db)

        # 创建新表单
        new_form = Form(
            tenant_id=tenant_id,
            name=new_name,
            category=source_form.category,
            access_mode=source_form.access_mode,
            owner_user_id=user_id,
            status=FormStatus.DRAFT.value,
            submit_deadline=source_form.submit_deadline,
            allow_edit=source_form.allow_edit,
            max_edit_count=source_form.max_edit_count
        )
        db.add(new_form)
        db.flush()

        # 复制配置
        if source_version:
            new_version = FormVersion(
                tenant_id=tenant_id,
                form_id=new_form.id,
                version=0,  # 草稿版本
                schema_json=source_version.schema_json,
                ui_schema_json=source_version.ui_schema_json,
                logic_json=source_version.logic_json,
                published_at=None
            )
            db.add(new_version)

        db.commit()
        db.refresh(new_form)

        logger.info(f"Cloned form: source={form_id}, new={new_form.id}, tenant={tenant_id}")
        return new_form