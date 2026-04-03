@echo off
rem 用法: run_logo.bat 图片 logo.png 下载栏.png [-o 输出.png] [-p 20]
set PYTHONHOME=C:\Users\lijun\AppData\Local\Programs\Python\Python314
C:\Python314\python.exe C:\test\add_logo.py --invoke-dir "%CD%" %*
