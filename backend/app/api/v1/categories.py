"""
模块用途: 表单分类API端点
依赖配置: FastAPI, SQLAlchemy
数据流向: HTTP请求 -> 路由处理 -> 业务逻辑 -> HTTP响应
函数清单:
    - list_categories(): 获取分类列表
    - create_category(): 创建分类
    - update_category(): 更新分类
    - delete_category(): 删除分类
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_tenant_id
from app.models.user import User
from app.schemas.category_schemas import (
    CategoryCreateRequest,
    CategoryUpdateRequest,
    CategoryResponse,
    CategoryListResponse
)
from app.services.category_service import CategoryService
from app.core.response import success_response, error_response
from app.core.exceptions import ValidationError, ConflictError, NotFoundError, AuthorizationError
from app.utils.audit import audit_log
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", summary="获取分类列表", response_model=dict)
async def list_categories(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    获取当前租户的分类列表（分页）

    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最多100条
    """
    try:
        categories, total = CategoryService.get_categories(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            db=db
        )

        response = CategoryListResponse(
            items=[CategoryResponse.from_orm(cat) for cat in categories],
            total=total,
            page=page,
            page_size=page_size
        )

        return success_response(data=response.model_dump())

    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        return error_response(str(e), status_code=500)


@router.post("", summary="创建分类", response_model=dict, status_code=201)
async def create_category(
        request: CategoryCreateRequest,
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    创建新分类

    - **name**: 分类名称（1-50个字符）
    """
    try:
        category = CategoryService.create_category(
            tenant_id=tenant_id,
            name=request.name,
            db=db
        )

        audit_log(
            user_id=current_user.id,
            tenant_id=tenant_id,
            action="create_category",
            resource_type="category",
            resource_id=category.id,
            details={"name": category.name}
        )

        response = CategoryResponse.from_orm(category)
        return success_response(data=response.model_dump(), status_code=201)

    except ValidationError as e:
        return error_response(str(e), status_code=400)
    except ConflictError as e:
        return error_response(str(e), status_code=409)
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        return error_response(str(e), status_code=500)


@router.put("/{category_id}", summary="更新分类", response_model=dict)
async def update_category(
        category_id: int = Path(..., ge=1, description="分类ID"),
        request: CategoryUpdateRequest = None,
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    更新分类信息

    - **category_id**: 分类ID
    - **name**: 新的分类名称（1-50个字符）
    """
    try:
        category = CategoryService.update_category(
            category_id=category_id,
            tenant_id=tenant_id,
            name=request.name,
            db=db
        )

        audit_log(
            user_id=current_user.id,
            tenant_id=tenant_id,
            action="update_category",
            resource_type="category",
            resource_id=category.id,
            details={"name": category.name}
        )

        response = CategoryResponse.from_orm(category)
        return success_response(data=response.model_dump())

    except ValidationError as e:
        return error_response(str(e), status_code=400)
    except ConflictError as e:
        return error_response(str(e), status_code=409)
    except NotFoundError as e:
        return error_response(str(e), status_code=404)
    except Exception as e:
        logger.error(f"Error updating category: {e}")
        return error_response(str(e), status_code=500)


@router.delete("/{category_id}", summary="删除分类", status_code=204)
async def delete_category(
        category_id: int = Path(..., ge=1, description="分类ID"),
        current_user: User = Depends(get_current_user),
        tenant_id: int = Depends(get_current_tenant_id),
        db: Session = Depends(get_db)
):
    """
    删除分类

    删除分类时，该分类下的所有表单将被重新分配到默认分类

    - **category_id**: 分类ID
    """
    try:
        CategoryService.delete_category(
            category_id=category_id,
            tenant_id=tenant_id,
            db=db
        )

        audit_log(
            user_id=current_user.id,
            tenant_id=tenant_id,
            action="delete_category",
            resource_type="category",
            resource_id=category_id,
            details={}
        )

        return None  # 204 No Content

    except ValidationError as e:
        return error_response(str(e), status_code=400)
    except NotFoundError as e:
        return error_response(str(e), status_code=404)
    except Exception as e:
        logger.error(f"Error deleting category: {e}")
        return error_response(str(e), status_code=500)
