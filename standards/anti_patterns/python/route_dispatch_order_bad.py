"""
反例: 参数路由抢在固定路由前面

适用范围:
- Starlette / FastAPI 这类按注册顺序匹配路由优先级的框架

问题:
- /users/{username} 会把 "me" 当作 username 参数
- /users/me 永远不会被匹配到
- 这类 bug 在开发阶段可能不被发现，上线后才出问题
"""

routes = [
    ("/users/{username}", "user_detail_handler"),
    ("/users/me", "current_user_handler"),
]
