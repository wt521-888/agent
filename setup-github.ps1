# GitHub 加速配置脚本
# 使用方式: .\setup-github.ps1 -Method mirror

param(
    [Parameter(Position=0)]
    [ValidateSet("mirror", "proxy", "ssh", "hosts")]
    [string] = "mirror",
    
    [string] = "http://127.0.0.1:7890"
)

 = "wt521lcl/agent.git"
 = @(
    "https://ghfast.top/https://github.com/",
    "https://ghproxy.com/https://github.com/",
    "https://mirror.ghproxy.com/https://github.com/"
)

function Set-Mirror {
    Write-Host "配置 GitHub 镜像..." -ForegroundColor Cyan
    
    foreach ( in ) {
        Write-Host "尝试: " -ForegroundColor Gray
        git remote set-url origin 
        
        # 测试连接
         = git ls-remote origin --heads 2>&1
        if ( -eq 0) {
            Write-Host "✓ 镜像可用: " -ForegroundColor Green
            return True
        }
    }
    
    Write-Host "✗ 所有镜像不可用" -ForegroundColor Red
    return False
}

function Set-Proxy {
    Write-Host "配置 Git 代理..." -ForegroundColor Cyan
    
    git config --global http.proxy 
    git config --global https.proxy 
    
    Write-Host "✓ 代理已配置: " -ForegroundColor Green
    Write-Host "提示: 确保代理软件已启动" -ForegroundColor Yellow
}

function Set-SSH {
    Write-Host "配置 SSH 方式..." -ForegroundColor Cyan
    
    # 检查 SSH key
    if (!(Test-Path "C:\Users\MECHREVO\.ssh\id_ed25519.pub")) {
        Write-Host "生成 SSH key..." -ForegroundColor Yellow
        ssh-keygen -t ed25519 -C "github@MECHREVO" -f "C:\Users\MECHREVO\.ssh\id_ed25519" -N '""'
    }
    
    # 复制公钥
     = Get-Content "C:\Users\MECHREVO\.ssh\id_ed25519.pub"
     | Set-Clipboard
    
    Write-Host "✓ SSH 公钥已复制到剪贴板" -ForegroundColor Green
    Write-Host "请添加到: https://github.com/settings/keys" -ForegroundColor Yellow
    
    # 修改远程地址
    git remote set-url origin "git@github.com:"
    Write-Host "✓ 远程地址已改为 SSH" -ForegroundColor Green
}

function Set-Hosts {
    Write-Host "配置 Hosts 文件..." -ForegroundColor Cyan
    
    # 获取 GitHub IP
     = (nslookup github.com 8.8.8.8 2> | Select-String "Address:" | Select-Object -Last 1).ToString().Split(":")[-1].Trim()
    
    if () {
        Write-Host "GitHub IP: " -ForegroundColor Gray
        
        # 添加到 hosts
         = "C:\Windows\System32\drivers\etc\hosts"
         = " github.com"
        
         = Get-Content 
        if ( -notcontains ) {
            Add-Content -Path  -Value "
" -Force
            Write-Host "✓ 已添加到 hosts 文件" -ForegroundColor Green
        } else {
            Write-Host "✓ hosts 文件已存在该记录" -ForegroundColor Green
        }
    } else {
        Write-Host "✗ 无法获取 GitHub IP" -ForegroundColor Red
    }
}

# 主逻辑
Write-Host "=== GitHub 加速配置 ===" -ForegroundColor Cyan
Write-Host ""

switch () {
    "mirror" { Set-Mirror }
    "proxy"  { Set-Proxy }
    "ssh"    { Set-SSH }
    "hosts"  { Set-Hosts }
}

Write-Host ""
Write-Host "当前配置:" -ForegroundColor Cyan
git remote -v
