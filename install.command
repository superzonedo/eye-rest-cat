#!/bin/bash
# 護眼貓 一鍵安裝 — 雙擊我一次,裝好套件並啟動。
cd "$(dirname "$0")"
echo "🐱 護眼貓 安裝精靈"
echo "================================"

# 找一個內含 tkinter 的 Python3
PY=""
for cand in \
    /Library/Frameworks/Python.framework/Versions/*/bin/python3 \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3 \
    "$(command -v python3)"; do
    [ -x "$cand" ] || continue
    if "$cand" -c "import tkinter" >/dev/null 2>&1; then
        PY="$cand"
        break
    fi
done

if [ -z "$PY" ]; then
    echo ""
    echo "⚠️  找不到內含 tkinter 的 Python。"
    echo "請到 python.org 下載安裝 Python(內建 tkinter),"
    echo "裝好後再雙擊一次這個『install.command』即可。"
    echo "(已幫你打開下載頁面)"
    open "https://www.python.org/downloads/macos/"
    echo ""
    read -n 1 -s -r -p "按任意鍵關閉視窗..."
    exit 1
fi

echo "✅ 使用 Python:$PY"
echo ""
echo "📦 安裝 rumps 套件中(第一次會下載一些東西,請稍候 1~2 分鐘)..."
"$PY" -m pip install rumps \
  || "$PY" -m pip install --user rumps \
  || "$PY" -m pip install --user --break-system-packages rumps

echo ""
echo "🚀 安裝完成,正在啟動護眼貓..."
pkill -f "eye_rest.py" 2>/dev/null
sleep 1
nohup "$PY" eye_rest.py >/tmp/eye_rest.log 2>&1 &
disown 2>/dev/null

echo ""
echo "✅ 完成!請看 Mac 螢幕右上角選單列的 🐱 圖示。"
echo "💡 如果看不到圖示(瀏海機種),按住 ⌘ Command 鍵,"
echo "   把選單列上任一個小圖示往下拖掉,空出位置就會出現。"
echo ""
echo "以後啟動:雙擊『start.command』即可。"
sleep 4
