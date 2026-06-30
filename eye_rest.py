#!/usr/bin/env python3
"""護眼貓 — Mac 選單列三層休息計時器(貓咪風格)。

依研究設計的三層休息週期:
  · 看遠方   每 20 分 → 20 秒   (20-20-20,放鬆睫狀肌)
  · 起身走動 每 50 分 → 3 分    (證據最強的一層)
  · 離開螢幕 每 120 分 → 5 分   (高頻短休息原則)

選單列顯示「距離下次看遠方」的倒數;時間到時跳出全螢幕遮罩。
休息進行中會暫停所有計時,結束後才繼續。
"""
import os
import sys
import json
import subprocess

import rumps

CONFIG_PATH = os.path.expanduser("~/.eye_rest_config.json")
APP_PATH = os.path.abspath(__file__)
OVERLAY = os.path.join(os.path.dirname(APP_PATH), "break_overlay.py")
MEOW_PATH = os.path.join(os.path.dirname(APP_PATH), "meow.wav")
MEOW_MP3 = os.path.join(os.path.dirname(APP_PATH), "meow.mp3")
PY = sys.executable

# 開機自動啟動用的 LaunchAgent
LAUNCH_LABEL = "com.eyerest.cat"
PLIST_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{LAUNCH_LABEL}.plist")

# 測試模式:設環境變數 EYE_REST_TEST=1 會用很短的間隔,方便馬上看到效果
TEST = os.environ.get("EYE_REST_TEST") == "1"

DEFAULTS = {
    "eye_interval": 20 * 60,
    "move_interval": 50 * 60,
    "away_interval": 120 * 60,
    "eye_dur": 20,
    "move_dur": 180,
    "away_dur": 300,
    "work_start": 9,    # 只在 09:00–22:00 提醒
    "work_end": 22,
    "work_hours_only": True,
    "allow_skip": True,
    "sound": True,
}

if TEST:
    DEFAULTS.update({
        "eye_interval": 20, "move_interval": 45, "away_interval": 90,
        "eye_dur": 8, "move_dur": 10, "away_dur": 12,
        "work_hours_only": False,
    })

# 三層的中繼資料:(key, 中文名, icon 字元)
LAYERS = [
    ("eye", "看遠方喵", "👀"),
    ("move", "伸懶腰喵", "🐾"),
    ("away", "打個盹喵", "😴"),
]


def load_config():
    cfg = dict(DEFAULTS)
    if os.path.exists(CONFIG_PATH) and not TEST:
        try:
            with open(CONFIG_PATH) as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg


def save_config(cfg):
    if TEST:
        return
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def fmt(sec):
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


# --- 開機自動啟動(LaunchAgent)------------------------------------------
def autostart_enabled():
    return os.path.exists(PLIST_PATH)


def enable_autostart():
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LAUNCH_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{PY}</string>
        <string>{APP_PATH}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{os.path.dirname(APP_PATH)}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>ProcessType</key>
    <string>Interactive</string>
</dict>
</plist>
"""
    os.makedirs(os.path.dirname(PLIST_PATH), exist_ok=True)
    with open(PLIST_PATH, "w") as f:
        f.write(plist)
    # 載入(忽略已載入的錯誤)
    subprocess.run(["launchctl", "load", "-w", PLIST_PATH],
                   capture_output=True)


def disable_autostart():
    subprocess.run(["launchctl", "unload", "-w", PLIST_PATH],
                   capture_output=True)
    try:
        os.remove(PLIST_PATH)
    except OSError:
        pass


# --- 合成貓叫聲(stdlib,免下載)----------------------------------------
def sound_file():
    # 優先用使用者放的 meow.mp3,沒有才用內建合成的 meow.wav
    return MEOW_MP3 if os.path.exists(MEOW_MP3) else MEOW_PATH


def ensure_meow(path=MEOW_PATH):
    # 已有自訂 mp3 或已合成過就不用再產生
    if os.path.exists(MEOW_MP3) or os.path.exists(path):
        return
    import wave
    import math
    import struct
    sr = 22050
    dur = 0.55
    n = int(sr * dur)
    frames = bytearray()
    phase = 0.0
    for i in range(n):
        t = i / n
        # 「喵~」音調:先快速升高(me~),再緩緩降下(~ow)
        if t < 0.25:
            f = 520 + (880 - 520) * (t / 0.25)
        else:
            f = 880 + (470 - 880) * ((t - 0.25) / 0.75)
        # 一點顫音讓它更像貓
        f *= 1 + 0.03 * math.sin(2 * math.pi * 6 * (i / sr))
        phase += 2 * math.pi * f / sr
        # 疊加泛音讓聲音更飽滿
        s = math.sin(phase) + 0.5 * math.sin(2 * phase) + 0.25 * math.sin(3 * phase)
        # 音量包絡:快起、尾巴漸弱
        if t < 0.05:
            env = t / 0.05
        elif t > 0.65:
            env = max(0.0, (1 - t) / 0.35)
        else:
            env = 1.0
        val = (s / 1.75) * env
        val = max(-1.0, min(1.0, val))
        frames += struct.pack("<h", int(val * 32767 * 0.6))
    try:
        w = wave.open(path, "w")
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(bytes(frames))
        w.close()
    except Exception:
        pass


def play_meow():
    try:
        subprocess.Popen(["afplay", sound_file()])
    except Exception:
        pass


class EyeRest(rumps.App):
    def __init__(self):
        super().__init__("🐱", quit_button=None)
        self.cfg = load_config()
        self.paused = False
        self.in_break = False
        self.proc = None
        self.fired = None  # 觸發休息的層 key
        self.prev_app = None
        self.reset_all_timers()
        ensure_meow()  # 第一次啟動時合成貓叫聲音檔

        # 選單
        self.status_item = rumps.MenuItem("距離下次陪你看遠方喵 --:--")
        self.layer_items = {
            "eye": rumps.MenuItem("👀  看遠方喵 · 每 20 分"),
            "move": rumps.MenuItem("🐾  伸懶腰喵 · 每 50 分"),
            "away": rumps.MenuItem("😴  打個盹喵 · 每 120 分"),
        }
        self.pause_item = rumps.MenuItem("讓貓打盹(暫停)", callback=self.toggle_pause)
        self.skip_item = rumps.MenuItem("跳過下一個喵", callback=self.skip_next)

        interval_menu = self._build_interval_menu()
        work_item = rumps.MenuItem("只在特定時段看家", callback=self.toggle_work_hours)
        work_item.state = 1 if self.cfg["work_hours_only"] else 0
        self.work_item = work_item
        work_time_menu = self._build_work_time_menu()
        skip_allow = rumps.MenuItem("允許偷偷略過", callback=self.toggle_allow_skip)
        skip_allow.state = 1 if self.cfg["allow_skip"] else 0
        self.allow_skip_item = skip_allow

        autostart = rumps.MenuItem("開機自動啟動", callback=self.toggle_autostart)
        autostart.state = 1 if autostart_enabled() else 0
        self.autostart_item = autostart

        sound_item = rumps.MenuItem("結束時喵一聲", callback=self.toggle_sound)
        sound_item.state = 1 if self.cfg["sound"] else 0
        self.sound_item = sound_item

        self.menu = [
            self.status_item,
            None,
            self.layer_items["eye"],
            self.layer_items["move"],
            self.layer_items["away"],
            None,
            self.pause_item,
            self.skip_item,
            None,
            ("設定間隔", interval_menu),
            work_item,
            ("看家時段", work_time_menu),
            skip_allow,
            sound_item,
            autostart,
            None,
            rumps.MenuItem("叫貓咪現在出來(測試)", callback=lambda _: self.start_break("eye")),
            None,
            rumps.MenuItem("放貓咪回家(結束)", callback=self.quit_app),
        ]

        self.timer = rumps.Timer(self.tick, 1)
        self.timer.start()

    # --- 計時邏輯 ---------------------------------------------------------
    def reset_all_timers(self):
        self.remaining = {
            "eye": self.cfg["eye_interval"],
            "move": self.cfg["move_interval"],
            "away": self.cfg["away_interval"],
        }

    def in_work_hours(self):
        if not self.cfg["work_hours_only"]:
            return True
        import datetime
        h = datetime.datetime.now().hour
        return self.cfg["work_start"] <= h < self.cfg["work_end"]

    def tick(self, _):
        # 休息進行中:等子程序結束
        if self.in_break:
            if self.proc is not None and self.proc.poll() is not None:
                self.end_break()
            else:
                self.title = "🐱 睡"
                return

        if self.paused or not self.in_work_hours():
            self.title = "🐱 停" if self.paused else "🐱 眠"
            self.refresh_menu()
            return

        for key in ("eye", "move", "away"):
            self.remaining[key] -= 1

        # 觸發優先序:長休息優先
        if self.remaining["away"] <= 0:
            self.start_break("away")
        elif self.remaining["move"] <= 0:
            self.start_break("move")
        elif self.remaining["eye"] <= 0:
            self.start_break("eye")

        self.title = f"🐱 {fmt(self.remaining['eye'])}"  # 貓 + 倒數
        self.refresh_menu()

    def refresh_menu(self):
        names = {"eye": "看遠方喵", "move": "伸懶腰喵", "away": "打個盹喵"}
        self.status_item.title = f"距離下次陪你{names['eye']} {fmt(self.remaining['eye'])}"
        mins = {"eye": self.cfg["eye_interval"], "move": self.cfg["move_interval"],
                "away": self.cfg["away_interval"]}
        icons = {"eye": "👀", "move": "🐾", "away": "😴"}
        for key in ("eye", "move", "away"):
            self.layer_items[key].title = (
                f"{icons[key]}  {names[key]} · 每 {mins[key] // 60} 分   →  {fmt(self.remaining[key])}"
            )

    # --- 休息 -------------------------------------------------------------
    def start_break(self, kind):
        if self.in_break:
            return
        # 先記住「現在正在用的 app」,休息結束後要切回去
        self.prev_app = self._frontmost_app()
        self.in_break = True
        self.fired = kind
        dur = {"eye": self.cfg["eye_dur"], "move": self.cfg["move_dur"],
               "away": self.cfg["away_dur"]}[kind]
        allow = "1" if self.cfg["allow_skip"] else "0"
        try:
            self.proc = subprocess.Popen([PY, OVERLAY, kind, str(dur), allow])
        except Exception as e:
            rumps.notification("護眼貓", "貓咪跑不出來了", str(e))
            self.in_break = False
            self.fired = None

    def end_break(self):
        # 自然倒數結束 returncode 為 0;按略過/Esc 為 2
        natural_end = (self.proc is not None and self.proc.returncode == 0)
        self.proc = None
        self.in_break = False
        kind = self.fired
        self.fired = None
        # 把焦點切回休息前正在用的 app,而不是掉到桌面
        self._restore_app(getattr(self, "prev_app", None))
        self.prev_app = None
        # 休息自然結束時喵一聲提醒回來(略過時不吵)
        if natural_end and self.cfg["sound"]:
            play_meow()
        # 看遠方一定重置;走動/離開也順帶重置較短的層,避免休息背靠背
        self.remaining["eye"] = self.cfg["eye_interval"]
        if kind in ("move", "away"):
            self.remaining["move"] = self.cfg["move_interval"]
        if kind == "away":
            self.remaining["away"] = self.cfg["away_interval"]

    @staticmethod
    def _frontmost_app():
        try:
            from AppKit import NSWorkspace
            return NSWorkspace.sharedWorkspace().frontmostApplication()
        except Exception:
            return None

    @staticmethod
    def _restore_app(app):
        if app is None:
            return
        try:
            # NSApplicationActivateAllWindows(1) | IgnoringOtherApps(2) = 3
            app.activateWithOptions_(3)
        except Exception:
            pass

    # --- 選單動作 ---------------------------------------------------------
    def toggle_pause(self, item):
        self.paused = not self.paused
        item.title = "叫貓咪回來看家(繼續)" if self.paused else "讓貓打盹(暫停)"

    def skip_next(self, _):
        # 把最接近觸發的那一層重置
        nxt = min(self.remaining, key=self.remaining.get)
        interval = self.cfg[f"{nxt}_interval"]
        self.remaining[nxt] = interval

    def toggle_work_hours(self, item):
        self.cfg["work_hours_only"] = not self.cfg["work_hours_only"]
        item.state = 1 if self.cfg["work_hours_only"] else 0
        save_config(self.cfg)

    def toggle_allow_skip(self, item):
        self.cfg["allow_skip"] = not self.cfg["allow_skip"]
        item.state = 1 if self.cfg["allow_skip"] else 0
        save_config(self.cfg)

    def toggle_autostart(self, item):
        if autostart_enabled():
            disable_autostart()
        else:
            enable_autostart()
        item.state = 1 if autostart_enabled() else 0

    def toggle_sound(self, item):
        self.cfg["sound"] = not self.cfg["sound"]
        item.state = 1 if self.cfg["sound"] else 0
        save_config(self.cfg)
        if self.cfg["sound"]:
            play_meow()  # 打開時試聽一下

    def _build_interval_menu(self):
        sub = rumps.MenuItem("設定間隔")
        options = {
            "eye": [10, 15, 20, 25, 30],
            "move": [30, 40, 50, 60],
            "away": [60, 90, 120, 150, 180],
        }
        labels = {"eye": "看遠方喵", "move": "伸懶腰喵", "away": "打個盹喵"}
        for key in ("eye", "move", "away"):
            grp = rumps.MenuItem(labels[key])
            for mins in options[key]:
                mi = rumps.MenuItem(
                    f"每 {mins} 分",
                    callback=self._make_interval_setter(key, mins),
                )
                if self.cfg[f"{key}_interval"] == mins * 60:
                    mi.state = 1
                grp.add(mi)
            sub.add(grp)
        return sub

    def _make_interval_setter(self, key, mins):
        def setter(item):
            self.cfg[f"{key}_interval"] = mins * 60
            self.remaining[key] = mins * 60
            save_config(self.cfg)
            # 更新勾選狀態
            for sib in item.parent.values():
                sib.state = 0
            item.state = 1
        return setter

    def _build_work_time_menu(self):
        sub = rumps.MenuItem("看家時段")
        # 開始時間:0–12 點
        self.work_start_grp = rumps.MenuItem(
            f"開始時間(目前 {self.cfg['work_start']:02d}:00)")
        for h in range(0, 13):
            mi = rumps.MenuItem(f"{h:02d}:00",
                                callback=self._make_hour_setter("work_start", h))
            if self.cfg["work_start"] == h:
                mi.state = 1
            self.work_start_grp.add(mi)
        # 結束時間:13–24 點(24 = 午夜)
        self.work_end_grp = rumps.MenuItem(
            f"結束時間(目前 {self.cfg['work_end']:02d}:00)")
        for h in range(13, 25):
            label = f"{h:02d}:00" if h < 24 else "24:00(午夜)"
            mi = rumps.MenuItem(label,
                                callback=self._make_hour_setter("work_end", h))
            if self.cfg["work_end"] == h:
                mi.state = 1
            self.work_end_grp.add(mi)
        sub.add(self.work_start_grp)
        sub.add(self.work_end_grp)
        return sub

    def _make_hour_setter(self, key, hour):
        def setter(item):
            self.cfg[key] = hour
            # 設了時間就自動開啟時段限制,否則設了沒效果
            self.cfg["work_hours_only"] = True
            self.work_item.state = 1
            save_config(self.cfg)
            for sib in item.parent.values():
                sib.state = 0
            item.state = 1
            grp = self.work_start_grp if key == "work_start" else self.work_end_grp
            head = "開始時間" if key == "work_start" else "結束時間"
            grp.title = f"{head}(目前 {hour:02d}:00)"
        return setter

    def quit_app(self, _):
        if self.proc is not None:
            try:
                self.proc.terminate()
            except Exception:
                pass
        rumps.quit_application()


if __name__ == "__main__":
    EyeRest().run()
