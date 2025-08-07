@echo off
echo ========================================
echo Jekyll博客本地启动脚本
echo ========================================
echo.

REM 检查Ruby是否安装
ruby --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Ruby未安装或未添加到PATH
    echo 请先安装Ruby: https://rubyinstaller.org/downloads/
    echo 建议下载Ruby+Devkit版本
    pause
    exit /b 1
)

echo [信息] Ruby已安装
ruby --version

REM 检查Bundler是否安装
bundler --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [信息] 正在安装Bundler...
    gem install bundler
)

echo [信息] Bundler已安装
bundler --version

REM 安装依赖
echo.
echo [信息] 正在安装项目依赖...
bundle install

if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    echo 尝试运行: bundle install --user-install
    pause
    exit /b 1
)

REM 清理Jekyll缓存
echo.
echo [信息] 正在清理Jekyll缓存...
if exist _site rmdir /s /q _site
if exist .jekyll-cache rmdir /s /q .jekyll-cache

REM 启动Jekyll服务器
echo.
echo [信息] 正在启动Jekyll服务器...
echo [信息] 服务器启动后，请访问: http://localhost:4000
echo [信息] 按Ctrl+C停止服务器
echo.

bundle exec jekyll serve --livereload --host=127.0.0.1 --port=4000

pause