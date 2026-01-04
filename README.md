# 中国海油网站404链接监测工具 - 打包文件

## 📦 快速打包（Windows）

### 方法1：一键打包（推荐）

1. **双击运行** `一键打包.bat`
2. **等待完成**（5-10分钟）
3. **获取exe**：在 `dist` 目录找到 `网站监测工具.exe`

### 方法2：手动打包

```cmd
pip install -r requirements.txt
python -m playwright install chromium
pip install pyinstaller

pyinstaller --onefile --name "网站监测工具" --add-data "templates;templates" --hidden-import=flask --hidden-import=playwright --hidden-import=requests --hidden-import=parse_websites_elements --hidden-import=playwright.sync_api --hidden-import=playwright.async_api --console website_monitor_app.py
```

## 📁 文件说明

- `parse_websites_elements.py` - 核心监测脚本
- `website_monitor_app.py` - Flask Web应用
- `templates/index.html` - 前端界面
- `requirements.txt` - Python依赖
- `一键打包.bat` - 打包脚本

## 🚀 使用说明

打包完成后，将 `dist/网站监测工具.exe` 复制给用户：

1. 双击运行exe
2. 浏览器自动打开界面
3. 点击"开始监测"
4. 查看404链接结果

## ⚠️ 注意事项

- 需要Python 3.8+环境
- 首次运行需要下载Playwright浏览器（约100MB）
- 确保网络连接正常

