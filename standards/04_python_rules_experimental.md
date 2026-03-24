# Python Experimental Rules

## 候选规则 1：异步路径纯异步化
适用：
- FastAPI 异步路由
- 异步 service / client

要求：
- 异步路径中避免阻塞 IO
- 如果必须调用同步库，应显式隔离

## 候选规则 2：结构化日志优先
适用：
- 任务调度
- 外部接口调用
- 数据清洗
- 审计关键流程

要求：
- 记录关键上下文键值
- 禁止只输出无上下文字符串

## 候选规则 3：异步资源优先 async with
适用：
- HTTP client
- 异步数据库连接
- 异步会话资源

要求：
- 优先使用 async with 管理生命周期
- 避免手动 close/cleanup 遗漏
