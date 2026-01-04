@echo off
chcp 65001 >nul
echo ========================================
echo 中国海油网站监测工具 - 一键打包脚本
echo ========================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] 检查Python环境...
python --version

echo.
echo [2/5] 安装Python依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [3/5] 安装Playwright浏览器...
python -m playwright install chromium
if errorlevel 1 (
    echo [警告] Playwright浏览器安装失败，但可以继续打包
)

echo.
echo [4/5] 安装PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo [错误] PyInstaller安装失败
    pause
    exit /b 1
)

echo.
echo [5/5] 开始打包...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pyinstaller --onefile ^
    --name "网站监测工具" ^
    --add-data "templates;templates" ^
    --hidden-import=flask ^
    --hidden-import=playwright ^
    --hidden-import=requests ^
    --hidden-import=parse_websites_elements ^
    --hidden-import=playwright.sync_api ^
    --hidden-import=playwright.async_api ^
    --console ^
    website_monitor_app.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 可执行文件位置: dist\网站监测工具.exe
echo.
echo 使用说明：
echo 1. 将 dist\网站监测工具.exe 复制到目标电脑
echo 2. 双击运行，程序会自动打开浏览器
echo 3. 在浏览器中点击"开始监测"按钮
echo.
echo 按任意键打开dist目录...
pause >nul
explorer dist

