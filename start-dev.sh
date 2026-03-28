#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$HOME/code/formflow修改版"
FRONTEND_DIR="$PROJECT_DIR/my-app"
BACKEND_DIR="$PROJECT_DIR/backend"
DISTRO="${WSL_DISTRO_NAME:-Ubuntu}"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "项目目录不存在: $PROJECT_DIR"
  exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
  echo "前端目录不存在: $FRONTEND_DIR"
  exit 1
fi

if [ ! -d "$BACKEND_DIR" ]; then
  echo "后端目录不存在: $BACKEND_DIR"
  exit 1
fi

echo "正在启动前后端..."
echo "项目目录: $PROJECT_DIR"
echo "WSL 发行版: $DISTRO"

# 新开前端窗口
cmd.exe /c start "" wt.exe -w new new-tab --title "FormFlow Frontend" ^
  wsl.exe -d "$DISTRO" bash -lc "cd '$FRONTEND_DIR' && npm run dev; exec bash"

# 新开后端窗口
cmd.exe /c start "" wt.exe -w new new-tab --title "FormFlow Backend" ^
  wsl.exe -d "$DISTRO" bash -lc "cd '$BACKEND_DIR' && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload; exec bash"
