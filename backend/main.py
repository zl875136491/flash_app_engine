"""FlashApp Engine 后端入口。

启动示例：
  cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
或：
  ./run.sh
"""

from src.core import create_app

app = create_app()
