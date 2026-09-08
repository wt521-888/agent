# GitHub 加速配置脚本
param(
    [string] = "mirror",
    [string] = "http://127.0.0.1:7890"
)

 = "wt521lcl/agent.git"

function Set-Mirror {
    Write-Host "配置 GitHub 镜像..." -ForegroundColor Cyan
     = @(
        "https://ghfast.top/https://github.com/",
        "https://ghproxy.com/https://github.com/"
    )
    foreach ( in ) {
        Write-Host "尝试: " -ForegroundColor Gray
        git remote set-url origin 
         = git ls-remote origin --heads 2>&1
        if ( -eq 0) {
            Write-Host "OK 镜像可用: " -ForegroundColor Green
            return
        }
    }
    Write-Host "FAIL 所有镜像不可用" -ForegroundColor Red
}

function Set-Proxy {
    Write-Host "配置 Git 代理..." -ForegroundColor Cyan
    git config --global http.proxy 
    git config --global https.proxy 
    Write-Host "OK 代理已配置: " -ForegroundColor Green
}

function Set-SSH {
    Write-Host "配置 SSH 方式..." -ForegroundColor Cyan
     = "C:\Users\MECHREVO\.ssh\id_ed25519.pub"
    if (!(Test-Path )) {
        ssh-keygen -t ed25519 -C "github@MECHREVO" -f "C:\Users\MECHREVO\.ssh\id_ed25519" -N '""'
    }
    Get-Content  | Set-Clipboard
    Write-Host "OK SSH 公钥已复制到剪贴板" -ForegroundColor Green
    Write-Host "请添加到: https://github.com/settings/keys" -ForegroundColor Yellow
    git remote set-url origin "git@github.com:"
}

Write-Host "=== GitHub 加速配置 ===" -ForegroundColor Cyan

switch () {
    "mirror" { Set-Mirror }
    "proxy"  { Set-Proxy }
    "ssh"    { Set-SSH }
}

Write-Host ""
Write-Host "当前远程地址:" -ForegroundColor Cyan
git remote -v
