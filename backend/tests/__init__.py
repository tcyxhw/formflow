TEST_TABLE_UV_PROMPTS = r"""
[我的要求]:
- 默认仅输出命令；每行一条；不得输出解释、注释、前缀符号、代码块、空行
- 仅当满足以下条件时，方可在命令前添加"说明：…"（小于30字）：
  1. 涉及多机操作（需标注机器）
  2. 有必需的前置手动步骤（如修改配置文件）
  3. 命令执行需要特定上下文（如特定目录）
- 如题目含明显拼写错误，请直接用正确项输出命令（不要输出纠错说明）
- 如涉及两机（在线机/目标机），可用"在线机：/目标机："前缀（对比时可忽略该前缀）

[回复示例]:
# 输出格式1（无说明）
测试ID: <测试编号>
命令:
<命令1>
<命令2>

# 输出格式2（有说明）
测试ID: <测试编号>
说明: <一句话，小于30字>
命令:
<命令1>
<命令2>

# 输出格式1的示例
测试ID: 1
命令:
uv add httpx

# 输出格式2的示例
测试ID: 12
说明: 在目标机项目根目录执行
命令:
uv lock
uv sync --frozen

[uv规范]
<<<UV_SPEC_START
{{UV_SPEC}}
UV_SPEC_END>>>

[测试表]
- 测试名称: 添加依赖（基础）
  - 测试ID: 1
  - 测试目的: 验证最小添加流程：uv add 自动写锁并安装
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：在项目中添加依赖 plotly。

- 测试名称: 添加依赖（拼写容错）
  - 测试ID: 2
  - 测试目的: 检验对明显拼写错误的纠正能力
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：在项目中添加依赖 ploty（若为拼写错误请直接用正确包名给命令）。

- 测试名称: 添加到分组（dev）
  - 测试ID: 3
  - 测试目的: 验证 --group 的使用
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：把 ruff 添加到 dev 分组。

- 测试名称: 安装 extras
  - 测试ID: 4
  - 测试目的: 验证 extras 语法与引号
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：安装 httpx 的 socks extra（注意引号与 shell 解析）。

- 测试名称: 跨平台标记（markers）
  - 测试ID: 5
  - 测试目的: 验证环境标记用法
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：仅在非 Windows 平台添加 uvloop（使用环境标记）。

- 测试名称: 删除依赖
  - 测试ID: 6
  - 测试目的: 验证删除流程
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：删除依赖 httpx。

- 测试名称: 单包受控升级（改约束）
  - 测试ID: 7
  - 测试目的: 验证通过新约束升级单包
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：把 httpx 升级到 0.27.*，但不要跨到 0.28。

- 测试名称: 添加依赖（extras+markers+版本约束组合）
  - 测试ID: 8
  - 测试目的: 验证 PEP 508 组合表达式
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：添加 pydantic 的 email extra，版本 2.8.*，仅 Python 3.11+。

- 测试名称: 全量升级已锁依赖并应用
  - 测试ID: 9
  - 测试目的: 验证 lock --upgrade 后需 sync
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：把锁文件中的所有依赖尽量升级，并同步到环境。

- 测试名称: 严格按锁复现
  - 测试ID: 10
  - 测试目的: 验证 --frozen 的严格校验
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：严格按 uv.lock 复现环境（不一致即报错）。

- 测试名称: CI 复现并运行测试
  - 测试ID: 11
  - 测试目的: 验证 CI 顺序：装 I → 冻结复现 → 运行
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：在 CI 上复现环境并运行 pytest，Python 版本用 3.12。

- 测试名称: 平台特定复现（目标机生成锁）
  - 测试ID: 12
  - 测试目的: 验证在目标机生成 L 再严格复现
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：【目标机操作】在项目根目录生成平台特定锁并严格安装到环境。

- 测试名称: 私有主索引安装（add 用环境变量）
  - 测试ID: 13
  - 测试目的: 验证 uv add 通过 PIP_INDEX_URL 走私有源
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：从 https://pypi.example.com/simple 安装 httpx（作为主索引）。

- 测试名称: 镜像：锁定与安装（命令参数）
  - 测试ID: 14
  - 测试目的: 验证 lock/sync 使用 --index-url/--extra-index-url
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：用清华镜像锁定并安装，阿里为额外索引。

- 测试名称: 代理与证书（add）
  - 测试ID: 15
  - 测试目的: 验证 add 在企业网络下通过代理/证书
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：在企业代理与自签证书环境下安装 httpx（http 代理 http://proxy.corp:8080，证书 /etc/ssl/certs/corp-ca.pem）。

- 测试名称: 额外索引（环境变量方式）
  - 测试ID: 16
  - 测试目的: 验证 PIP_EXTRA_INDEX_URL 对 add 的作用
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：使用 https://mirror.example.com/simple 作为额外索引安装 httpx。

- 测试名称: 离线复现（两机、固定缓存目录）
  - 测试ID: 17
  - 测试目的: 验证预热缓存 + 目标机离线严格复现闭环
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：【多机操作】先在在线机预热缓存到 /mnt/shared/uv-cache，再在目标机离线严格复现。

- 测试名称: 使用本地 PEP 503 索引
  - 测试ID: 18
  - 测试目的: 验证 file:// 索引用法
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：从本地索引 file:///opt/simple-index 安装（按锁同步）。

- 测试名称: 预下载 wheels（wheels-first）
  - 测试ID: 19
  - 测试目的: 验证 uv pip download 的使用
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：把 orjson 的 3.* 版本 wheel 下载到 wheelhouse 目录。

- 测试名称: 预下载 wheels（requirements 文件）
  - 测试ID: 20
  - 测试目的: 验证 -r 形式批量下载
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：按 requirements.txt 下载 wheels 到 wheelhouse 目录。

- 测试名称: 同步使用本地索引 + 轮子目录
  - 测试ID: 21
  - 测试目的: 验证 --index-url file:// 搭配 --find-links
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：从本地索引 /opt/simple-index 同步，并额外使用 ./wheelhouse 作为轮子目录。

- 测试名称: 缓存清理
  - 测试ID: 22
  - 测试目的: 验证 uv cache prune
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：清理本地 uv 缓存。

- 测试名称: 直链 URL 安装
  - 测试ID: 23
  - 测试目的: 验证 direct URL 格式
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：从 https://host/path/file.whl 安装包 mypkg。

- 测试名称: 直链 URL + 企业证书
  - 测试ID: 24
  - 测试目的: 验证直链 + SSL_CERT_FILE
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：在企业证书环境下从直链安装 mypkg（证书 /etc/ssl/certs/corp-ca.pem）。

- 测试名称: Git 指定 tag 安装
  - 测试ID: 25
  - 测试目的: 验证 Git 源形式（tag）
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：从 Git 安装 mypkg 的 v1.2.3 版本（使用 tag）。

- 测试名称: Git 指定分支安装
  - 测试ID: 26
  - 测试目的: 验证 Git 源分支形式
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：从 Git 的 main 分支安装 mypkg。

- 测试名称: 本地路径依赖（相对路径）
  - 测试ID: 27
  - 测试目的: 验证本地相对路径形式
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：把 ../libs/mylib 作为依赖加入当前项目。

- 测试名称: 本地路径依赖（当前目录子路径）
  - 测试ID: 28
  - 测试目的: 验证本地相对路径形式（子路径）
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：把 ./local_plugin 作为依赖加入当前项目。

- 测试名称: 诊断（依赖树与已装包）
  - 测试ID: 29
  - 测试目的: 验证 uv tree 与 uv pip list
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：查看 dev 分组的依赖树，并查看当前环境已安装包。

- 测试名称: 诊断（多分组依赖树）
  - 测试ID: 30
  - 测试目的: 验证 uv tree 多次 --group
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：同时查看 dev 与 test 分组的依赖树。

- 测试名称: 一次性脚本（PEP 723）
  - 测试ID: 31
  - 测试目的: 验证 uv run 解析内联依赖
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：运行带内联依赖头的 script.py。

- 测试名称: uv run 任意命令
  - 测试ID: 32
  - 测试目的: 验证 uv run 在项目环境内执行命令
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：在项目环境内开启 8000 端口的 http server。

- 测试名称: 显式创建虚拟环境
  - 测试ID: 33
  - 测试目的: 验证 uv venv 的使用（尽管 add/sync 会自动创建）
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：显式创建项目虚拟环境。

- 测试名称: 一次性工具（uvx）
  - 测试ID: 34
  - 测试目的: 验证 uvx 临时工具（不污染项目依赖）
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：用 uvx 运行 ruff 检查当前目录。

- 测试名称: 切换 Python 主版本（C 已允许）
  - 测试ID: 35
  - 测试目的: 验证 I 切换 + 冻结复现顺序（C 已兼容）
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：把项目切到 Python 3.12，并严格按锁复现环境（已确认 pyproject.toml 的 requires-python 允许 3.12）。

- 测试名称: 切换 Python 主版本（C 不允许）
  - 测试ID: 36
  - 测试目的: 验证不兼容时的回退路径（需先放宽 C 并刷新锁）
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：把项目切到 Python 3.12，并严格按锁复现环境（pyproject.toml 的 requires-python 当前不允许 3.12，需先手动修改配置文件放宽版本约束至 >=3.12）。

- 测试名称: 仅安装某个分组
  - 测试ID: 37
  - 测试目的: 验证分组安装
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：只安装 dev 分组依赖。

- 测试名称: 多分组安装
  - 测试ID: 38
  - 测试目的: 验证同时安装多个分组
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：同时安装 dev 与 test 两个分组。

- 测试名称: 仅刷新锁（不安装）
  - 测试ID: 39
  - 测试目的: 验证只改 L，不动 E
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：只生成/刷新锁，不改变当前环境。

- 测试名称: pip 生态兼容（导出 + 安装）
  - 测试ID: 40
  - 测试目的: 验证 uv pip freeze 与 uv pip install -r
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：导出当前环境为 requirements.lock.txt，并从该文件安装。

- 测试名称: 从 requirements.txt 迁移为 uv 项目（基础）
  - 测试ID: 41
  - 测试目的: 验证迁移主路径：映射依赖 → 生成锁 → 同步环境
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：将当前项目的 requirements.txt 迁移为 uv 项目并安装环境（需先手动将 requirements.txt 内容映射到 pyproject.toml 的 [project].dependencies）。

- 测试名称: 从 requirements.txt 迁移为 uv 项目（严格复现）
  - 测试ID: 42
  - 测试目的: 迁移后用冻结模式严格复现
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：迁移 requirements.txt 后严格按锁复现环境（需先手动将 requirements.txt 内容映射到 pyproject.toml 的 [project].dependencies）。

- 测试名称: 从 requirements.txt 迁移（私有主索引）
  - 测试ID: 43
  - 测试目的: 迁移时走私有主索引（lock/sync 命令参数）
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：迁移 requirements.txt 时使用主索引 https://pypi.example.com/simple（需先手动将 requirements.txt 内容映射到 pyproject.toml 的 [project].dependencies）。

- 测试名称: 新增子项目（库型）
  - 测试ID: 44
  - 测试目的: 工作区子项目首次锁定 + 安装
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：【子项目目录操作】在子项目目录初始化库型项目并安装。

- 测试名称: 子项目互依（路径形式）
  - 测试ID: 45
  - 测试目的: A 依赖 B（路径来源）后同步
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：【在 A 项目根目录操作】在 A 项目中添加对 ../B 的依赖并安装。

- 测试名称: 分组严格安装
  - 测试ID: 46
  - 测试目的: --group 与 --frozen 组合
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：仅严格安装 test 分组依赖。

- 测试名称: 文件索引 + 离线 + 冻结
  - 测试ID: 47
  - 测试目的: 本地 PEP 503 索引 + 离线严格复现
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：从 file:///opt/simple 严格离线复现环境。

- 测试名称: uvx 临时工具（不污染项目依赖）
  - 测试ID: 48
  - 测试目的: 验证 uvx 的一次性工具场景
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：用 uvx 运行 ruff 检查当前目录。

- 测试名称: 运行脚本（私有源）
  - 测试ID: 49
  - 测试目的: PEP 723 脚本解析依赖走私有源
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：从私有主索引 https://pypi.example.com/simple 运行 script.py。

- 测试名称: 切换 Python 主版本（C 不允许，含刷新锁）
  - 测试ID: 50
  - 测试目的: 先放宽 C，再刷新 L，严格复现
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：把项目切到 Python 3.12，并严格按锁复现环境（pyproject.toml 的 requires-python 当前不允许 3.12，需先手动修改配置文件放宽版本约束至 >=3.12）。

- 测试名称: 解释器安装（企业代理）
  - 测试ID: 51
  - 测试目的: uv python install 在代理下可用
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：通过企业代理安装 Python 3.12（http://user:pass@proxy.corp:8080）。

- 测试名称: uvx 临时工具 + 私有主索引
  - 测试ID: 52
  - 测试目的: 验证 uvx 结合私有源，不污染项目依赖
  - 提示词: 请严格根据上述"uv 规范"回答，并按"输出格式"作答。任务：从私有主索引 https://pypi.example.com/simple 临时运行 ruff --version。
"""


TEST_TABLE_UV_EXPECTED = r"""
1:
  uv add plotly

2:
  uv add plotly

3:
  uv add --group dev ruff

4:
  uv add "httpx[socks]"

5:
  uv add "uvloop; sys_platform != 'win32'"

6:
  uv remove httpx

7:
  uv add "httpx>=0.27,<0.28"

8:
  uv add "pydantic[email]==2.8.*; python_version >= '3.11'"

9:
  uv lock --upgrade
  uv sync

10:
  uv sync --frozen

11:
  uv python install 3.12
  uv sync --frozen
  uv run pytest

12:
  说明: 在目标机项目根目录执行
  uv lock
  uv sync --frozen

13:
  PIP_INDEX_URL=https://pypi.example.com/simple uv add httpx

14:
  uv lock --index-url https://pypi.tuna.tsinghua.edu.cn/simple --extra-index-url https://mirrors.aliyun.com/pypi/simple
  uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple --extra-index-url https://mirrors.aliyun.com/pypi/simple

15:
  HTTPS_PROXY=http://proxy.corp:8080 SSL_CERT_FILE=/etc/ssl/certs/corp-ca.pem uv add httpx

16:
  PIP_EXTRA_INDEX_URL=https://mirror.example.com/simple uv add httpx

17:
  在线机：UV_CACHE_DIR=/mnt/shared/uv-cache uv sync
  目标机：UV_CACHE_DIR=/mnt/shared/uv-cache uv sync --offline --frozen

18:
  uv sync --index-url file:///opt/simple-index

19:
  uv pip download -d wheelhouse "orjson==3.*"

20:
  uv pip download -d wheelhouse -r requirements.txt

21:
  uv sync --index-url file:///opt/simple-index --find-links ./wheelhouse

22:
  uv cache prune

23:
  uv add "mypkg @ https://host/path/file.whl"

24:
  SSL_CERT_FILE=/etc/ssl/certs/corp-ca.pem uv add "mypkg @ https://host/path/file.whl"

25:
  uv add "mypkg @ git+https://github.com/org/repo.git@v1.2.3"

26:
  uv add "mypkg @ git+https://github.com/org/repo.git@main"

27:
  uv add ../libs/mylib

28:
  uv add ./local_plugin

29:
  uv tree --group dev
  uv pip list

30:
  uv tree --group dev --group test

31:
  uv run script.py

32:
  uv run python -m http.server 8000

33:
  uv venv

34:
  uvx ruff check .

35:
  uv python install 3.12
  uv sync --frozen

36:
  说明: 需先修改 pyproject.toml 的 requires-python 至 >=3.12
  uv python install 3.12
  uv lock
  rm -rf .venv
  uv sync --frozen

37:
  uv sync --group dev

38:
  uv sync --group dev --group test

39:
  uv lock

40:
  uv pip freeze > requirements.lock.txt
  uv pip install -r requirements.lock.txt

41:
  说明: 需先映射 requirements.txt 到 pyproject.toml
  uv lock
  uv sync

42:
  说明: 需先映射 requirements.txt 到 pyproject.toml
  uv lock
  uv sync --frozen

43:
  说明: 需先映射 requirements.txt 到 pyproject.toml
  uv lock --index-url https://pypi.example.com/simple
  uv sync --index-url https://pypi.example.com/simple

44:
  说明: 在子项目目录执行
  uv lock
  uv sync

45:
  说明: 在 A 项目根目录执行
  uv add ../B
  uv sync

46:
  uv sync --group test --frozen

47:
  uv sync --index-url file:///opt/simple --offline --frozen

48:
  uvx ruff check .

49:
  PIP_INDEX_URL=https://pypi.example.com/simple uv run script.py

50:
  说明: 需先修改 pyproject.toml 的 requires-python 至 >=3.12
  uv python install 3.12
  uv lock
  rm -rf .venv
  uv sync --frozen

51:
  HTTPS_PROXY=http://user:pass@proxy.corp:8080 uv python install 3.12

52:
  PIP_INDEX_URL=https://pypi.example.com/simple uvx ruff --version
"""