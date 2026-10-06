#!/bin/bash
# 護眼貓 一鍵更新 — 雙擊我更新到最新版。
cd "$(dirname "$0")"
echo "🐱 護眼貓 更新精靈"
echo "================================"

# 先關掉正在跑的護眼貓
pkill -f "eye_rest.py" 2>/dev/null
sleep 1

if [ -d .git ]; then
    echo "偵測到 git 版本,正在從 GitHub 拉取最新版..."
    if git pull --ff-only; then
        echo "✅ 已更新到最新版!"
    else
        echo ""
        echo "⚠️  自動更新遇到衝突(可能你改過檔案,例如換過 meow.mp3)。"
        echo "    若你沒有要保留本機修改,可執行下面這行後再更新一次:"
        echo "    git reset --hard origin/main"
    fi
    echo ""
    echo "🚀 正在重新啟動護眼貓..."
    # 找一個同時有 tkinter 與 rumps 的 Python3
    PY=""
    for cand in \
        /Library/Frameworks/Python.framework/Versions/*/bin/python3 \
        /opt/homebrew/bin/python3 \
        /usr/local/bin/python3 \
        "$(command -v python3)"; do
        [ -x "$cand" ] || continue
        # 跳過 Apple 內建的 Python(附的 Tk 8.5 太舊,休息畫面會空白;沒裝開發工具時還會跳安裝視窗)
        case "$cand" in /usr/bin/*|/Library/Developer/*|/Applications/Xcode*) continue ;; esac
        if "$cand" -c "import tkinter, rumps, sys; sys.exit(tkinter.TkVersion < 8.6)" >/dev/null 2>&1; then
            PY="$cand"
            break
        fi
    done
    if [ -n "$PY" ]; then
        nohup "$PY" eye_rest.py >/tmp/eye_rest.log 2>&1 &
        disown 2>/dev/null
        echo "✅ 完成!護眼貓已是最新版,請看選單列 🐱"
    else
        echo "⚠️  找不到合適的 Python,請先雙擊『install.command』。"
    fi
else
    echo "這是 ZIP 下載版(非 git),沒辦法自動更新。"
    echo ""
    echo "請到 GitHub 重新下載最新的 ZIP:"
    echo "  綠色 Code 按鈕 → Download ZIP"
    echo "解壓縮後,把檔案蓋回原本的資料夾(⚠️ 同一個位置)即可。"
    echo "(已幫你打開下載頁面)"
    open "https://github.com/superzonedo/eye-rest-cat"
fi
echo ""
sleep 4
