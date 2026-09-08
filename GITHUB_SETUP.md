# GitHub 加速配置指南

## 问题描述
国内网络访问 GitHub 经常超时，导致 git push/pull 失败。

## 解决方案

### 方案1：使用 GitHub 镜像（推荐）

`powershell
# 使用 ghfast 镜像
git remote set-url origin https://ghfast.top/https://github.com/wt521lcl/agent.git

# 其他可用镜像
# https://ghproxy.com/https://github.com/wt521lcl/agent.git
# https://mirror.ghproxy.com/https://github.com/wt521lcl/agent.git
# https://gh-proxy.com/https://github.com/wt521lcl/agent.git
`

### 方案2：配置 HTTP 代理

`powershell
# 如果你有本地代理（如 Clash、V2Ray 等）
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 取消代理
git config --global --unset http.proxy
git config --global --unset https.proxy
`

### 方案3：使用 SSH 方式（最稳定）

`powershell
# 1. 生成 SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. 复制公钥
cat ~/.ssh/id_ed25519.pub | clip

# 3. 添加到 GitHub: https://github.com/settings/keys

# 4. 修改远程地址为 SSH
git remote set-url origin git@github.com:wt521lcl/agent.git
`

### 方案4：修改 Hosts 文件

`powershell
# 1. 获取 GitHub IP
nslookup github.com 8.8.8.8

# 2. 编辑 hosts 文件（以管理员身份运行 notepad）
notepad C:\Windows\System32\drivers\etc\hosts

# 3. 添加类似以下内容（IP 需要实时查询）
140.82.114.4 github.com
140.82.114.4 www.github.com
`

## 自动化脚本

创建 setup-github.ps1 脚本：

`powershell
param(
    [string] = "mirror"
)

 = "https://github.com/wt521lcl/agent.git"

switch () {
    "mirror" {
        git remote set-url origin "https://ghfast.top/"
        Write-Host "✓ 已配置 ghfast 镜像" -ForegroundColor Green
    }
    "proxy" {
        git config --global http.proxy http://127.0.0.1:7890
        git config --global https.proxy http://127.0.0.1:7890
        Write-Host "✓ 已配置代理" -ForegroundColor Green
    }
    "ssh" {
        git remote set-url origin "git@github.com:wt521lcl/agent.git"
        Write-Host "✓ 已配置 SSH" -ForegroundColor Green
    }
}

Write-Host "
当前远程地址:"
git remote -v
`

使用方式：
`powershell
.\setup-github.ps1 -Method mirror
.\setup-github.ps1 -Method proxy
.\setup-github.ps1 -Method ssh
`

## 推荐配置

对于国内用户，推荐使用 **镜像 + Token** 方式：

`powershell
# 1. 配置镜像
git remote set-url origin https://ghfast.top/https://github.com/wt521lcl/agent.git

# 2. 配置凭证存储
git config --global credential.helper store

# 3. 推送时输入 GitHub 用户名和 Token
git push origin master
`

## 注意事项

1. 镜像站可能会失效，需要更换
2. Token 会明文存储在 .git-credentials，注意安全
3. SSH 方式最稳定，但需要配置密钥
