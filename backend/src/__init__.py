from os.path import abspath, dirname

current_path = abspath(__file__)
if "src" not in current_path:
  raise ValueError("请保证 src 目录在项目根目录下")

APP_ROOT = dirname(abspath(__file__)).split("/src")[0]
