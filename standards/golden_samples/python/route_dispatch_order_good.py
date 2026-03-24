"""
正例: 更具体的路由优先

适用范围:
- Starlette / FastAPI 这类按注册顺序匹配路由优先级的框架

设计要点:
- 固定路径放在参数路径前面
- 避免 /users/me 被 /users/{username} 意外捕获
"""

routes = [
    ("/users/me", "current_user_handler"),
    ("/users/{username}", "user_detail_handler"),
]
