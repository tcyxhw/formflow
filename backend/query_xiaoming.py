#!/usr/bin/env python3
"""
查询数据库中关于"小明"的所有信息
"""
import sys
sys.path.insert(0, '/home/tcyuuu/code/formflow修改版/backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

DATABASE_URL = "postgresql://postgres:13579qwe@localhost:5432/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def search_xiaoming():
    results = {}
    
    with SessionLocal() as db:
        print("=" * 60)
        print("查询数据库中关于'小明'的所有信息")
        print("=" * 60)
        
        # 1. 查询用户表中名为小明的用户
        print("\n【1. 用户表 (user) - 查询姓名包含'小明'】")
        print("-" * 40)
        query = text("""
            SELECT id, tenant_id, account, name, email, phone, department_id, is_active, created_at
            FROM "user" 
            WHERE name LIKE '%小明%'
        """)
        users = db.execute(query).fetchall()
        if users:
            for user in users:
                print(f"  用户ID: {user.id}")
                print(f"  租户ID: {user.tenant_id}")
                print(f"  账号: {user.account}")
                print(f"  姓名: {user.name}")
                print(f"  邮箱: {user.email}")
                print(f"  手机: {user.phone}")
                print(f"  部门ID: {user.department_id}")
                print(f"  是否启用: {user.is_active}")
                print(f"  创建时间: {user.created_at}")
                print("  " + "-" * 30)
            results['users'] = [dict(user._mapping) for user in users]
        else:
            print("  未找到名为'小明'的用户")
        
        # 2. 查询用户扩展信息表
        print("\n【2. 用户扩展信息表 (user_profile) - 关联查询】")
        print("-" * 40)
        query = text("""
            SELECT up.id, up.user_id, u.name, up.identity_no, up.identity_type, 
                   up.entry_year, up.grade, up.major, up.title, up.research_area,
                   up.office, up.emergency_contact, up.emergency_phone
            FROM user_profile up
            JOIN "user" u ON up.user_id = u.id
            WHERE u.name LIKE '%小明%'
        """)
        profiles = db.execute(query).fetchall()
        if profiles:
            for p in profiles:
                print(f"  档案ID: {p.id}")
                print(f"  用户ID: {p.user_id}")
                print(f"  姓名: {p.name}")
                print(f"  学号/工号: {p.identity_no}")
                print(f"  身份类型: {p.identity_type}")
                print(f"  入学/入职年份: {p.entry_year}")
                print(f"  年级: {p.grade}")
                print(f"  专业: {p.major}")
                print(f"  职称: {p.title}")
                print(f"  研究方向: {p.research_area}")
                print(f"  办公室: {p.office}")
                print(f"  紧急联系人: {p.emergency_contact}")
                print(f"  紧急联系电话: {p.emergency_phone}")
                print("  " + "-" * 30)
            results['profiles'] = [dict(p._mapping) for p in profiles]
        else:
            print("  未找到相关用户扩展信息")
        
        # 3. 查询用户角色
        print("\n【3. 用户角色关联表 (user_role)】")
        print("-" * 40)
        query = text("""
            SELECT ur.id, ur.user_id, u.name as user_name, r.name as role_name, r.description
            FROM user_role ur
            JOIN "user" u ON ur.user_id = u.id
            JOIN role r ON ur.role_id = r.id
            WHERE u.name LIKE '%小明%'
        """)
        roles = db.execute(query).fetchall()
        if roles:
            for r in roles:
                print(f"  关联ID: {r.id}")
                print(f"  用户ID: {r.user_id}")
                print(f"  用户名: {r.user_name}")
                print(f"  角色名: {r.role_name}")
                print(f"  角色描述: {r.description}")
                print("  " + "-" * 30)
            results['roles'] = [dict(r._mapping) for r in roles]
        else:
            print("  未找到相关用户角色")
        
        # 4. 查询用户部门关联
        print("\n【4. 用户部门关联表 (user_department)】")
        print("-" * 40)
        query = text("""
            SELECT ud.id, ud.user_id, u.name as user_name, d.name as dept_name, ud.is_primary
            FROM user_department ud
            JOIN "user" u ON ud.user_id = u.id
            JOIN department d ON ud.department_id = d.id
            WHERE u.name LIKE '%小明%'
        """)
        depts = db.execute(query).fetchall()
        if depts:
            for d in depts:
                print(f"  关联ID: {d.id}")
                print(f"  用户ID: {d.user_id}")
                print(f"  用户名: {d.user_name}")
                print(f"  部门名: {d.dept_name}")
                print(f"  是否主部门: {d.is_primary}")
                print("  " + "-" * 30)
            results['departments'] = [dict(d._mapping) for d in depts]
        else:
            print("  未找到相关用户部门关联")
        
        # 5. 查询用户岗位
        print("\n【5. 用户岗位关联表 (user_position)】")
        print("-" * 40)
        query = text("""
            SELECT up.id, up.user_id, u.name as user_name, p.name as position_name, 
                   up.effective_from, up.effective_to
            FROM user_position up
            JOIN "user" u ON up.user_id = u.id
            JOIN position p ON up.position_id = p.id
            WHERE u.name LIKE '%小明%'
        """)
        positions = db.execute(query).fetchall()
        if positions:
            for p in positions:
                print(f"  关联ID: {p.id}")
                print(f"  用户ID: {p.user_id}")
                print(f"  用户名: {p.user_name}")
                print(f"  岗位名: {p.position_name}")
                print(f"  生效开始: {p.effective_from}")
                print(f"  生效结束: {p.effective_to}")
                print("  " + "-" * 30)
            results['positions'] = [dict(p._mapping) for p in positions]
        else:
            print("  未找到相关用户岗位")
        
        # 6. 查询表单提交记录中包含"小明"的数据
        print("\n【6. 表单提交记录 (submission) - JSON数据中包含'小明'】")
        print("-" * 40)
        query = text("""
            SELECT s.id, s.form_id, s.submitter_user_id, u.name as submitter_name,
                   s.data_jsonb, s.status, s.created_at
            FROM submission s
            LEFT JOIN "user" u ON s.submitter_user_id = u.id
            WHERE s.data_jsonb::text LIKE '%小明%'
        """)
        submissions = db.execute(query).fetchall()
        if submissions:
            for s in submissions:
                print(f"  提交ID: {s.id}")
                print(f"  表单ID: {s.form_id}")
                print(f"  提交人ID: {s.submitter_user_id}")
                print(f"  提交人姓名: {s.submitter_name}")
                print(f"  状态: {s.status}")
                print(f"  创建时间: {s.created_at}")
                print(f"  数据内容: {json.dumps(s.data_jsonb, ensure_ascii=False, indent=4)}")
                print("  " + "-" * 30)
            results['submissions'] = [dict(s._mapping) for s in submissions]
        else:
            print("  未找到包含'小明'的表单提交记录")
        
        # 7. 查询表单草稿中包含"小明"的数据
        print("\n【7. 表单草稿 (form_draft) - JSON数据中包含'小明'】")
        print("-" * 40)
        query = text("""
            SELECT fd.id, fd.form_id, fd.user_id, u.name as user_name,
                   fd.draft_data, fd.status, fd.created_at
            FROM form_draft fd
            LEFT JOIN "user" u ON fd.user_id = u.id
            WHERE fd.draft_data::text LIKE '%小明%'
        """)
        drafts = db.execute(query).fetchall()
        if drafts:
            for d in drafts:
                print(f"  草稿ID: {d.id}")
                print(f"  表单ID: {d.form_id}")
                print(f"  用户ID: {d.user_id}")
                print(f"  用户姓名: {d.user_name}")
                print(f"  状态: {d.status}")
                print(f"  创建时间: {d.created_at}")
                print(f"  草稿数据: {json.dumps(d.draft_data, ensure_ascii=False, indent=4)}")
                print("  " + "-" * 30)
            results['drafts'] = [dict(d._mapping) for d in drafts]
        else:
            print("  未找到包含'小明'的表单草稿")
        
        # 8. 查询审批小组成员
        print("\n【8. 审批小组成员 (approval_group_member)】")
        print("-" * 40)
        query = text("""
            SELECT agm.id, agm.group_id, ag.name as group_name, 
                   agm.user_id, u.name as user_name
            FROM approval_group_member agm
            JOIN approval_group ag ON agm.group_id = ag.id
            JOIN "user" u ON agm.user_id = u.id
            WHERE u.name LIKE '%小明%'
        """)
        group_members = db.execute(query).fetchall()
        if group_members:
            for g in group_members:
                print(f"  成员ID: {g.id}")
                print(f"  小组ID: {g.group_id}")
                print(f"  小组名: {g.group_name}")
                print(f"  用户ID: {g.user_id}")
                print(f"  用户名: {g.user_name}")
                print("  " + "-" * 30)
            results['approval_group_members'] = [dict(g._mapping) for g in group_members]
        else:
            print("  未找到相关审批小组成员")
        
        # 9. 查询代理人设置
        print("\n【9. 代理人设置 (delegation) - 作为委托人或代理人】")
        print("-" * 40)
        query = text("""
            SELECT d.id, d.delegator_user_id, u1.name as delegator_name,
                   d.delegate_user_id, u2.name as delegate_name,
                   d.type, d.scope, d.start_time, d.end_time, d.enabled
            FROM delegation d
            JOIN "user" u1 ON d.delegator_user_id = u1.id
            JOIN "user" u2 ON d.delegate_user_id = u2.id
            WHERE u1.name LIKE '%小明%' OR u2.name LIKE '%小明%'
        """)
        delegations = db.execute(query).fetchall()
        if delegations:
            for d in delegations:
                print(f"  代理ID: {d.id}")
                print(f"  委托人ID: {d.delegator_user_id}")
                print(f"  委托人姓名: {d.delegator_name}")
                print(f"  代理人ID: {d.delegate_user_id}")
                print(f"  代理人姓名: {d.delegate_name}")
                print(f"  代理类型: {d.type}")
                print(f"  代理范围: {d.scope}")
                print(f"  开始时间: {d.start_time}")
                print(f"  结束时间: {d.end_time}")
                print(f"  是否启用: {d.enabled}")
                print("  " + "-" * 30)
            results['delegations'] = [dict(d._mapping) for d in delegations]
        else:
            print("  未找到相关代理人设置")
        
        # 10. 查询用户创建的表单
        print("\n【10. 用户创建的表单 (form)】")
        print("-" * 40)
        query = text("""
            SELECT f.id, f.name, f.status, f.access_mode, f.created_at,
                   u.name as owner_name
            FROM form f
            JOIN "user" u ON f.owner_user_id = u.id
            WHERE u.name LIKE '%小明%'
        """)
        forms = db.execute(query).fetchall()
        if forms:
            for f in forms:
                print(f"  表单ID: {f.id}")
                print(f"  表单名: {f.name}")
                print(f"  状态: {f.status}")
                print(f"  访问模式: {f.access_mode}")
                print(f"  创建者: {f.owner_name}")
                print(f"  创建时间: {f.created_at}")
                print("  " + "-" * 30)
            results['forms'] = [dict(f._mapping) for f in forms]
        else:
            print("  未找到相关用户创建的表单")
        
        # 11. 查询通知记录
        print("\n【11. 通知记录 (notification_log) - 发送给小明】")
        print("-" * 40)
        query = text("""
            SELECT nl.id, nl.recipient_id, u.name as user_name, nl.title, 
                   nl.content, nl.type, nl.status, nl.sent_at, nl.created_at
            FROM notification_log nl
            JOIN "user" u ON nl.recipient_id = u.id
            WHERE u.name LIKE '%小明%'
        """)
        notifications = db.execute(query).fetchall()
        if notifications:
            for n in notifications:
                print(f"  通知ID: {n.id}")
                print(f"  接收人ID: {n.recipient_id}")
                print(f"  接收人姓名: {n.user_name}")
                print(f"  标题: {n.title}")
                print(f"  内容: {n.content[:100] if n.content else None}...")
                print(f"  类型: {n.type}")
                print(f"  状态: {n.status}")
                print(f"  发送时间: {n.sent_at}")
                print(f"  创建时间: {n.created_at}")
                print("  " + "-" * 30)
            results['notifications'] = [dict(n._mapping) for n in notifications]
        else:
            print("  未找到相关通知记录")
        
        # 12. 查询部门信息
        print("\n【12. 用户所属部门详情】")
        print("-" * 40)
        query = text("""
            SELECT d.id, d.name, d.type, d.parent_id, d.is_root, d.sort_order
            FROM department d
            WHERE d.id IN (SELECT department_id FROM "user" WHERE name LIKE '%小明%')
        """)
        departments = db.execute(query).fetchall()
        if departments:
            for d in departments:
                print(f"  部门ID: {d.id}")
                print(f"  部门名: {d.name}")
                print(f"  类型: {d.type}")
                print(f"  上级部门ID: {d.parent_id}")
                print(f"  是否根部门: {d.is_root}")
                print(f"  排序: {d.sort_order}")
                print("  " + "-" * 30)
            results['user_department'] = [dict(d._mapping) for d in departments]
        else:
            print("  未找到相关部门信息")
        
        # 13. 查询租户信息
        print("\n【13. 用户所属租户(学校)信息】")
        print("-" * 40)
        query = text("""
            SELECT t.id, t.name
            FROM tenant t
            WHERE t.id IN (SELECT tenant_id FROM "user" WHERE name LIKE '%小明%')
        """)
        tenants = db.execute(query).fetchall()
        if tenants:
            for t in tenants:
                print(f"  租户ID: {t.id}")
                print(f"  租户名(学校名): {t.name}")
                print("  " + "-" * 30)
            results['tenant'] = [dict(t._mapping) for t in tenants]
        else:
            print("  未找到相关租户信息")
        
        # 14. 查询审计日志
        print("\n【14. 审计日志 (audit_log) - 小明的操作记录】")
        print("-" * 40)
        query = text("""
            SELECT al.id, al.actor_user_id, u.name as actor_name, al.action,
                   al.resource_type, al.resource_id, al.ip, al.created_at
            FROM audit_log al
            JOIN "user" u ON al.actor_user_id = u.id
            WHERE u.name LIKE '%小明%'
            ORDER BY al.created_at DESC
            LIMIT 20
        """)
        audit_logs = db.execute(query).fetchall()
        if audit_logs:
            for a in audit_logs:
                print(f"  日志ID: {a.id}")
                print(f"  操作人ID: {a.actor_user_id}")
                print(f"  操作人姓名: {a.actor_name}")
                print(f"  动作: {a.action}")
                print(f"  资源类型: {a.resource_type}")
                print(f"  资源ID: {a.resource_id}")
                print(f"  IP: {a.ip}")
                print(f"  时间: {a.created_at}")
                print("  " + "-" * 30)
            results['audit_logs'] = [dict(a._mapping) for a in audit_logs]
        else:
            print("  未找到相关审计日志")
        
        # 15. 查询刷新令牌
        print("\n【15. 刷新令牌 (refresh_token) - 小明的登录会话】")
        print("-" * 40)
        query = text("""
            SELECT rt.id, rt.user_id, u.name as user_name, rt.family_id,
                   rt.expires_at, rt.active, rt.created_at
            FROM refresh_token rt
            JOIN "user" u ON rt.user_id = u.id
            WHERE u.name LIKE '%小明%'
            ORDER BY rt.created_at DESC
            LIMIT 10
        """)
        tokens = db.execute(query).fetchall()
        if tokens:
            for t in tokens:
                print(f"  令牌ID: {t.id}")
                print(f"  用户ID: {t.user_id}")
                print(f"  用户名: {t.user_name}")
                print(f"  家族ID: {t.family_id}")
                print(f"  过期时间: {t.expires_at}")
                print(f"  是否有效: {t.active}")
                print(f"  创建时间: {t.created_at}")
                print("  " + "-" * 30)
            results['tokens'] = [dict(t._mapping) for t in tokens]
        else:
            print("  未找到相关刷新令牌")
        
        print("\n" + "=" * 60)
        print("查询完成")
        print("=" * 60)
        
        return results

if __name__ == "__main__":
    search_xiaoming()
