#!/bin/bash
# 雙擊這個檔案就能啟動護眼貓。
cd "$(dirname "$0")"
# 若已在執行就先關掉舊的,避免重複
pkill -f "eye_rest.py" 2>/dev/null
sleep 1

# 自動找一個同時有 tkinter 與 rumps 的 Python3(在任何 Mac 上都能用)
PY=""
for cand in \
    /Library/Frameworks/Python.framework/Versions/*/bin/python3 \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3 \
    "$(command -v python3)"; do
    [ -x "$cand" ] || continue
    if "$cand" -c "import tkinter, rumps" >/dev/null 2>&1; then
        PY="$cand"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "⚠️  還沒安裝好,正在打開『install.command』幫你安裝..."
    open install.command 2>/dev/null
    sleep 2
    exit 1
fi

# nohup + disown:就算這個終端機視窗關掉,護眼貓還是會繼續活著
nohup "$PY" eye_rest.py >/tmp/eye_rest.log 2>&1 &
disown 2>/dev/null
echo "護眼貓已啟動,請看 Mac 右上角選單列的 🐱 圖示。"
echo "要關閉:點 🐱 → 放貓咪回家(結束)。"
sleep 2
