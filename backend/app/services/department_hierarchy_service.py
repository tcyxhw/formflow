"""
模块用途: 部门层级服务 - 处理部门树形结构和祖先链查询
依赖配置: PostgreSQL (支持递归 CTE)
数据流向: Service -> 递归 CTE 查询 -> 部门ID集合
函数清单:
    - get_ancestor_department_ids_cte(): 使用递归CTE获取部门祖先链
    - get_user_all_department_ids(): 获取用户所有部门ID（含祖先）
"""
from typing import Set
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import UserDepartment, Department


class DepartmentHierarchyService:
    """部门层级服务"""
    
    @staticmethod
    def get_ancestor_department_ids_cte(department_id: int, db: Session) -> Set[int]:
        """使用递归 CTE 一次查询获取所有祖先部门ID（含自身）
        
        Args:
            department_id: 部门ID
            db: 数据库会话
            
        Returns:
            包含自身和所有祖先部门的ID集合
            
        Time: O(depth), Space: O(depth)
        """
        sql = text("""
            WITH RECURSIVE dept_tree AS (
                -- 基础查询：起始部门
                SELECT id, parent_id 
                FROM department 
                WHERE id = :dept_id
                
                UNION ALL
                
                -- 递归查询：向上查找父部门
                SELECT d.id, d.parent_id
                FROM department d
                INNER JOIN dept_tree dt ON d.id = dt.parent_id
            )
            SELECT id FROM dept_tree
        """)
        
        result = db.execute(sql, {"dept_id": department_id})
        return {row[0] for row in result}
    
    @staticmethod
    def get_user_all_department_ids(user_id: int, db: Session) -> Set[int]:
        """获取用户所属的所有部门ID（包含直接部门和所有祖先部门）
        
        Args:
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            用户所有部门及其祖先部门的ID集合
            
        Time: O(N * depth), Space: O(N * depth)
        """
        # 获取用户直接关联的所有部门
        user_departments = (
            db.query(UserDepartment.department_id)
            .filter(UserDepartment.user_id == user_id)
            .all()
        )
        
        if not user_departments:
            return set()
        
        # 合并所有部门的祖先链
        all_dept_ids: Set[int] = set()
        for (dept_id,) in user_departments:
            ancestors = DepartmentHierarchyService.get_ancestor_department_ids_cte(dept_id, db)
            all_dept_ids.update(ancestors)
        
        return all_dept_ids
