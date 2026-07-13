#!/usr/bin/env python3
"""全螢幕休息遮罩(貓咪風格)。由 eye_rest.py 以子程序方式叫出。

用法:
    python3 break_overlay.py <kind> <seconds> <allow_skip>
    kind       = eye | move | away
    seconds    = 倒數秒數
    allow_skip = 1 顯示略過按鈕, 0 不顯示

離開碼:
    0 = 正常結束(休息完成)
    2 = 使用者按了略過
"""
import sys
import tkinter as tk
import tkinter.font as tkfont

# 每種休息的外觀與文案 ------------------------------------------------------
STYLES = {
    "eye": {
        "bg": "#0C447C", "fg": "#FFFFFF", "sub": "#B5D4F4", "dim": "#85B7EB",
        "title": "陪我看看 6 公尺外的遠方喵～",
        "subtitle": "讓眼睛的睫狀肌放鬆一下吧",
        "tail": "秒後貓咪就放你走喵",
        "symbol": "(=^･ω･^=)",  # 看遠方的貓
    },
    "move": {
        "bg": "#0F6E56", "fg": "#FFFFFF", "sub": "#9FE1CB", "dim": "#5DCAA5",
        "title": "一起伸個懶腰喵～",
        "subtitle": "站起來、走幾步、喝口水",
        "tail": "秒後再坐回去喵",
        "symbol": "ฅ(=ＴωＴ=)ฅ",  # 伸懶腰打哈欠的貓
    },
    "away": {
        "bg": "#854F0B", "fg": "#FFFFFF", "sub": "#FAC775", "dim": "#EF9F27",
        "title": "離開螢幕打個盹喵～",
        "subtitle": "去窗邊看遠方,讓眼睛和身體都重置",
        "tail": "秒後睡飽再回來喵",
        "symbol": "(=˘ω˘=) zzz",  # 打盹的貓
    },
}


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "eye"
    seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    allow_skip = (len(sys.argv) > 3 and sys.argv[3] == "1")
    s = STYLES.get(kind, STYLES["eye"])

    root = tk.Tk()
    # 切成「配件模式」:不在 Dock 顯示圖示、也不出現在 Cmd-Tab 切換清單
    try:
        from AppKit import NSApplication
        NSApplication.sharedApplication().setActivationPolicy_(1)  # 1 = Accessory
    except Exception:
        pass
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.97)
    root.configure(bg=s["bg"])
    root.lift()
    root.focus_force()

    big = tkfont.Font(family="Helvetica Neue", size=140, weight="normal")
    cat = tkfont.Font(family="Menlo", size=64, weight="normal")  # 等寬字讓貓臉工整
    h1 = tkfont.Font(family="Helvetica Neue", size=38, weight="normal")
    h2 = tkfont.Font(family="Helvetica Neue", size=20, weight="normal")
    small = tkfont.Font(family="Helvetica Neue", size=15, weight="normal")

    wrap = tk.Frame(root, bg=s["bg"])
    wrap.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(wrap, text=s["symbol"], font=cat, fg=s["fg"], bg=s["bg"]).pack(pady=(0, 28))
    tk.Label(wrap, text=s["title"], font=h1, fg=s["fg"], bg=s["bg"]).pack()
    tk.Label(wrap, text=s["subtitle"], font=h2, fg=s["sub"], bg=s["bg"]).pack(pady=(10, 36))

    count_lbl = tk.Label(wrap, text=str(seconds), font=big, fg=s["fg"], bg=s["bg"])
    count_lbl.pack()
    tk.Label(wrap, text=s["tail"], font=small, fg=s["dim"], bg=s["bg"]).pack(pady=(4, 0))

    # 角落標題
    tk.Label(root, text="🐱 護眼貓", font=small, fg=s["sub"], bg=s["bg"]).place(x=24, y=20)

    def finish(code):
        root.destroy()
        sys.exit(code)

    if allow_skip:
        skip = tk.Button(
            root, text="略過這次喵", font=small, fg=s["sub"], bg=s["bg"],
            activebackground=s["bg"], activeforeground=s["fg"],
            highlightthickness=0, bd=0, relief="flat", cursor="pointinghand",
            command=lambda: finish(2),
        )
        skip.place(relx=0.94, rely=0.94, anchor="se")

    # Esc 永遠可以強制關閉(避免卡住),視同略過
    root.bind("<Escape>", lambda e: finish(2))

    state = {"remaining": seconds}

    def tick():
        state["remaining"] -= 1
        if state["remaining"] <= 0:
            finish(0)
            return
        count_lbl.config(text=str(state["remaining"]))
        root.after(1000, tick)

    root.after(1000, tick)
    root.mainloop()


if __name__ == "__main__":
    main()
