# Jekyll博客本地启动脚本 (PowerShell版本)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Jekyll博客本地启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Ruby是否安装
try {
    $rubyVersion = ruby --version 2>$null
    Write-Host "[信息] Ruby已安装: $rubyVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] Ruby未安装或未添加到PATH" -ForegroundColor Red
    Write-Host "请先安装Ruby: https://rubyinstaller.org/downloads/" -ForegroundColor Yellow
    Write-Host "建议下载Ruby+Devkit版本" -ForegroundColor Yellow
    Read-Host "按Enter键退出"
    exit 1
}

# 检查Bundler是否安装
try {
    $bundlerVersion = bundler --version 2>$null
    Write-Host "[信息] Bundler已安装: $bundlerVersion" -ForegroundColor Green
} catch {
    Write-Host "[信息] 正在安装Bundler..." -ForegroundColor Yellow
    gem install bundler
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] Bundler安装失败" -ForegroundColor Red
        Read-Host "按Enter键退出"
        exit 1
    }
}

# 安装依赖
Write-Host ""
Write-Host "[信息] 正在安装项目依赖..." -ForegroundColor Yellow
bundle install

if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 依赖安装失败" -ForegroundColor Red
    Write-Host "尝试运行: bundle install --user-install" -ForegroundColor Yellow
    Read-Host "按Enter键退出"
    exit 1
}

# 启动Jekyll服务器
Write-Host ""
Write-Host "[信息] 正在启动Jekyll服务器..." -ForegroundColor Green
Write-Host "[信息] 服务器启动后，请访问: http://localhost:4000" -ForegroundColor Cyan
Write-Host "[信息] 按Ctrl+C停止服务器" -ForegroundColor Yellow
Write-Host ""

bundle exec jekyll serve --livereload

Read-Host "按Enter键退出"