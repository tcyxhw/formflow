#!/usr/bin/env python3
"""
检查 user_department_post 表的数据
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import get_db

def check_user_department_post():
    """检查 user_department_post 表的数据"""
    
    db = next(get_db())
    
    try:
        print("=" * 80)
        print("检查 user_department_post 表的数据")
        print("=" * 80)
        
        # 1. 查询 user_department_post 表中的所有记录
        print("\n【1. user_department_post 表数据】")
        print("-" * 40)
        
        query = text("""
            SELECT udp.id, udp.user_id, u.name as user_name, 
                   udp.department_id, d.name as dept_name,
                   udp.post_id, p.name as post_name
            FROM user_department_post udp
            JOIN "user" u ON udp.user_id = u.id
            JOIN department d ON udp.department_id = d.id
            LEFT JOIN position p ON udp.post_id = p.id
            WHERE udp.tenant_id = 1
            ORDER BY udp.user_id, udp.department_id, udp.post_id
        """)
        
        results = db.execute(query).fetchall()
        
        if results:
            print(f"共有 {len(results)} 条记录:")
            for row in results:
                print(f"  - ID: {row.id}, 用户: {row.user_name}({row.user_id}), "
                      f"部门: {row.dept_name}({row.department_id}), "
                      f"岗位: {row.post_name}({row.post_id})")
        else:
            print("user_department_post 表中没有数据")
        
        # 2. 检查辅导员张老师（ID: 501）是否有记录
        print("\n【2. 辅导员张老师（ID: 501）的 user_department_post 记录】")
        print("-" * 40)
        
        counselor_query = text("""
            SELECT udp.id, udp.user_id, u.name as user_name, 
                   udp.department_id, d.name as dept_name,
                   udp.post_id, p.name as post_name
            FROM user_department_post udp
            JOIN "user" u ON udp.user_id = u.id
            JOIN department d ON udp.department_id = d.id
            LEFT JOIN position p ON udp.post_id = p.id
            WHERE udp.user_id = 501
        """)
        
        counselor_results = db.execute(counselor_query).fetchall()
        
        if counselor_results:
            print(f"辅导员张老师有 {len(counselor_results)} 条记录:")
            for row in counselor_results:
                print(f"  - ID: {row.id}, 部门: {row.dept_name}({row.department_id}), "
                      f"岗位: {row.post_name}({row.post_id})")
        else:
            print("辅导员张老师在 user_department_post 表中没有记录")
        
        # 3. 检查学生小明（ID: 301）是否有记录
        print("\n【3. 学生小明（ID: 301）的 user_department_post 记录】")
        print("-" * 40)
        
        student_query = text("""
            SELECT udp.id, udp.user_id, u.name as user_name, 
                   udp.department_id, d.name as dept_name,
                   udp.post_id, p.name as post_name
            FROM user_department_post udp
            JOIN "user" u ON udp.user_id = u.id
            JOIN department d ON udp.department_id = d.id
            LEFT JOIN position p ON udp.post_id = p.id
            WHERE udp.user_id = 301
        """)
        
        student_results = db.execute(student_query).fetchall()
        
        if student_results:
            print(f"学生小明有 {len(student_results)} 条记录:")
            for row in student_results:
                print(f"  - ID: {row.id}, 部门: {row.dept_name}({row.department_id}), "
                      f"岗位: {row.post_name}({row.post_id})")
        else:
            print("学生小明在 user_department_post 表中没有记录")
        
        print("\n" + "=" * 80)
        print("检查完成")
        print("=" * 80)
        
    finally:
        db.close()


if __name__ == "__main__":
    check_user_department_post()
