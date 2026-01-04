# 使用 GitHub Actions 自动打包 Windows exe

## 📋 前提条件

1. 拥有 GitHub 账号
2. 代码已上传到 GitHub 仓库

## 🚀 使用步骤

### 1. 创建 GitHub 仓库

```bash
# 在本地初始化仓库（如果还没有）
cd 网站监测工具_打包文件
git init
git add .
git commit -m "Initial commit"
```

### 2. 推送到 GitHub

```bash
# 在 GitHub 上创建新仓库，然后：
git remote add origin https://github.com/你的用户名/仓库名.git
git branch -M main
git push -u origin main
```

### 3. 触发打包

**方法A：自动触发**
- 推送代码到 `main` 或 `master` 分支时自动打包

**方法B：手动触发**
1. 进入 GitHub 仓库页面
2. 点击 "Actions" 标签
3. 选择 "Build Windows Executable" 工作流
4. 点击 "Run workflow" 按钮
5. 选择分支，点击 "Run workflow"

### 4. 下载 exe 文件

1. 等待打包完成（约 5-10 分钟）
2. 在 Actions 页面点击完成的工作流
3. 在 "Artifacts" 部分下载 `网站监测工具-exe.zip`
4. 解压后得到 `网站监测工具.exe`

## 📁 文件说明

- `.github/workflows/build-windows.yml` - GitHub Actions 工作流配置
- 工作流会在 Windows 环境中自动：
  1. 安装 Python 3.10
  2. 安装所有依赖
  3. 安装 Playwright 浏览器
  4. 使用 PyInstaller 打包
  5. 生成可下载的 exe 文件

## ⚠️ 注意事项

- 首次运行可能需要 10-15 分钟（下载依赖）
- 后续运行通常 5-8 分钟
- 生成的 exe 文件在 Artifacts 中，保留 90 天

## 💡 优势

✅ 无需 Windows 电脑  
✅ 自动化打包  
✅ 可重复使用  
✅ 免费（GitHub 提供免费额度）

