#!/bin/bash
# 一键上传到GitHub并触发打包的脚本

echo "=========================================="
echo "网站监测工具 - GitHub 上传脚本"
echo "=========================================="
echo ""

# 检查是否已初始化git
if [ ! -d ".git" ]; then
    echo "初始化Git仓库..."
    git init
    git add .
    git commit -m "Initial commit: 网站监测工具"
    echo "✓ Git仓库已初始化"
else
    echo "检测到已有Git仓库，更新文件..."
    git add .
    git commit -m "Update: $(date +%Y%m%d_%H%M%S)"
    echo "✓ 文件已更新"
fi

echo ""
echo "=========================================="
echo "下一步操作："
echo "=========================================="
echo ""
echo "1. 在GitHub上创建新仓库："
echo "   - 访问: https://github.com/new"
echo "   - 填写仓库名称（如：website-monitor）"
echo "   - 选择 Public 或 Private"
echo "   - 不要勾选 'Initialize with README'"
echo "   - 点击 'Create repository'"
echo ""
echo "2. 复制仓库地址后，运行以下命令："
echo ""
echo "   git remote add origin https://github.com/你的用户名/仓库名.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. 在GitHub网页上："
echo "   - 进入仓库 → Actions 标签"
echo "   - 选择 'Build Windows Executable'"
echo "   - 点击 'Run workflow'"
echo "   - 等待打包完成并下载exe"
echo ""
echo "=========================================="
echo "或者，如果你已经配置了远程仓库，直接运行："
echo "  git push"
echo "=========================================="

