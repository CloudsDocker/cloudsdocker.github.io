@echo off
echo 正在重启Jekyll服务器...
echo.

REM 停止现有的Jekyll进程
taskkill /f /im ruby.exe 2>nul
timeout /t 2 /nobreak >nul

REM 清理Jekyll缓存
if exist _site rmdir /s /q _site
if exist .jekyll-cache rmdir /s /q .jekyll-cache

echo 缓存已清理，正在启动Jekyll服务器...
echo.

REM 启动Jekyll服务器
bundle exec jekyll serve --livereload --host=127.0.0.1 --port=4000

pause