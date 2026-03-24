## 数据库查询指南

### 问题原因
PostgreSQL 中 `user` 是系统关键字，直接执行 `SELECT * FROM user;` 会返回当前数据库用户名，而不是我们的用户表。

### 正确的查询方式

```sql
-- 查询用户表（必须使用双引号）
SELECT * FROM "user";

-- 查询部门表
SELECT * FROM department;

-- 查询岗位表
SELECT * FROM position;

-- 查询角色表
SELECT * FROM role;

-- 查询部门-岗位关系
SELECT * FROM department_post;

-- 查询用户-部门-岗位关系
SELECT * FROM user_department_post;

-- 查询用户角色关系
SELECT * FROM user_role;
```

### 当前数据库状态

| 表名 | 记录数 |
|------|--------|
| department | 22 |
| position | 28 |
| user | 12 |
| role | 3 |
| department_post | 54 |
| user_department_post | 8 |
| user_role | 9 |

### 测试用户列表（密码: 123456）

```sql
-- 查看所有用户
SELECT id, account, name FROM "user" WHERE tenant_id = 1;
```

| ID | 账号 | 姓名 | 角色 |
|----|------|------|------|
| 1 | 15018816993 | 糖醋鱼 | 管理员 |
| 100 | admin | 系统管理员 | 管理员 |
| 301 | xiaoming | 小明 | 学生 |
| 302 | xiaohong | 小红 | 学生 |
| 501 | zhanglaoshi | 张老师 | 老师 |
| 601 | wangjiaoshou | 王教授 | 老师 |
| 701 | lizhangyuan | 李院长 | 老师 |
| 801 | zhaokuaiji | 赵会计 | 老师 |
| 901 | sunfudaoyuan | 孙辅导员 | 老师 |
| 1001 | zhoujiaoxue | 周教学秘书 | 老师 |

### 验证 ORG_CHAIN_UP 功能

```sql
-- 查看小明的部门
SELECT udp.user_id, u.name as user_name, d.name as dept_name
FROM user_department_post udp
JOIN "user" u ON u.id = udp.user_id
JOIN department d ON d.id = udp.department_id
WHERE u.name = '小明';

-- 查看计算机学院的辅导员
SELECT udp.user_id, u.name as user_name, p.name as post_name
FROM user_department_post udp
JOIN "user" u ON u.id = udp.user_id
JOIN position p ON p.id = udp.post_id
WHERE udp.department_id = 20 AND udp.post_id = 2;
```
