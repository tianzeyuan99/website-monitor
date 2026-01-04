# GitHub Actions 设置步骤

## 📋 前提条件

1. 拥有 GitHub 账号
2. 已安装 Git（可选，也可以直接在网页上操作）

## 🚀 快速设置（3步完成）

### 方法1：使用 GitHub 网页界面（最简单）⭐推荐

#### 步骤1：创建仓库

1. 登录 GitHub：https://github.com
2. 点击右上角 `+` → `New repository`
3. 填写信息：
   - Repository name: `网站监测工具`（或任意名称）
   - Description: `中国海油网站404链接监测工具`
   - 选择 `Public` 或 `Private`
   - **不要**勾选 "Initialize this repository with a README"
4. 点击 `Create repository`

#### 步骤2：上传文件

1. 在仓库页面，点击 `uploading an existing file`
2. 将 `网站监测工具_打包文件` 文件夹中的所有文件拖拽上传：
   - `parse_websites_elements.py`
   - `website_monitor_app.py`
   - `templates/index.html`
   - `requirements.txt`
   - `.github/workflows/build-windows.yml`（重要！）
   - 其他文件（可选）
3. 在页面底部填写：
   - Commit message: `Initial commit`
4. 点击 `Commit changes`

#### 步骤3：触发打包

1. 点击仓库顶部的 `Actions` 标签
2. 在左侧选择 `Build Windows Executable`
3. 点击右侧 `Run workflow` 按钮
4. 选择分支（默认 `main`），点击绿色 `Run workflow` 按钮
5. 等待打包完成（约 5-10 分钟）

#### 步骤4：下载 exe

1. 打包完成后，在 `Actions` 页面点击完成的工作流
2. 滚动到页面底部，找到 `Artifacts` 部分
3. 点击 `网站监测工具-exe` 下载 zip 文件
4. 解压后得到 `网站监测工具.exe`

---

### 方法2：使用 Git 命令行

#### 步骤1：初始化仓库

```bash
cd 网站监测工具_打包文件
git init
git add .
git commit -m "Initial commit"
```

#### 步骤2：创建 GitHub 仓库并推送

1. 在 GitHub 上创建新仓库（参考方法1的步骤1）
2. 复制仓库地址（如：`https://github.com/你的用户名/网站监测工具.git`）

```bash
git remote add origin https://github.com/你的用户名/网站监测工具.git
git branch -M main
git push -u origin main
```

#### 步骤3：触发打包（同方法1的步骤3）

---

## ⚙️ 自动触发设置

默认配置会在以下情况自动打包：
- 推送代码到 `main` 或 `master` 分支
- 修改了 `.py` 文件、`requirements.txt` 或 `templates/` 目录

如果不想自动触发，可以：
1. 编辑 `.github/workflows/build-windows.yml`
2. 删除或注释掉 `push:` 部分，只保留 `workflow_dispatch:`

---

## 🔧 常见问题

### Q: 找不到 Actions 标签？
A: 确保 `.github/workflows/build-windows.yml` 文件已上传

### Q: 打包失败？
A: 
1. 点击失败的工作流查看错误信息
2. 检查 `requirements.txt` 是否正确
3. 确保所有 Python 文件语法正确

### Q: 下载的 exe 无法运行？
A: 
1. 确保在 Windows 系统上运行
2. 检查是否有杀毒软件拦截
3. 尝试右键 → 属性 → 解除锁定

### Q: 如何更新代码后重新打包？
A: 
1. 上传修改后的文件到 GitHub
2. 在 Actions 页面手动触发工作流
3. 或等待自动触发（如果配置了自动触发）

---

## 💡 提示

- **首次打包**可能需要 10-15 分钟（下载依赖）
- **后续打包**通常 5-8 分钟
- **Artifacts 保留 90 天**，记得及时下载
- 可以设置 **GitHub Actions 通知**，打包完成后收到邮件

---

## 📝 文件结构要求

确保上传的文件结构如下：

```
网站监测工具/
├── .github/
│   └── workflows/
│       └── build-windows.yml    ← 重要！
├── parse_websites_elements.py
├── website_monitor_app.py
├── requirements.txt
└── templates/
    └── index.html
```

---

## 🎯 完成！

设置完成后，每次需要打包时：
1. 更新代码（如果需要）
2. 在 Actions 页面点击 `Run workflow`
3. 等待完成并下载 exe

**无需 Windows 电脑，全自动打包！** 🎉

