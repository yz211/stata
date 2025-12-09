# update_app.ps1
# 自动更新部署脚本

Write-Host "正在准备更新..." -ForegroundColor Cyan

# 1. 添加所有更改
git add .

# 2. 获取提交信息
$commitMsg = Read-Host "请输入更新说明 (直接回车默认为: '程序优化更新')"
if ([string]::IsNullOrWhiteSpace($commitMsg)) { $commitMsg = "程序优化更新" }

# 3. 提交更改
git commit -m "$commitMsg"

# 4. 推送到 GitHub
Write-Host "正在推送到 GitHub..." -ForegroundColor Cyan
git push

if ($?) {
    Write-Host "`n✅ 推送成功！" -ForegroundColor Green
    Write-Host "Streamlit Cloud 检测到 GitHub 变动后，会自动重新部署您的应用。"
    Write-Host "请等待约 1-3 分钟，刷新您的网站即可看到最新版本。"
} else {
    Write-Host "`n❌ 推送失败，请检查网络或 Git 配置。" -ForegroundColor Red
}
