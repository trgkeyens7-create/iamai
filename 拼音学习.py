"""
小小学习星 v2 - 儿童拼音英语学习软件
功能：拼音/英语学习卡片、语音朗读、书写练习、小测验、进度统计、家长管理
"""

import tkinter as tk
from tkinter import ttk, font, messagebox
import random, json, os, threading, sys
from data import PINYIN_DATA, ENGLISH_DATA, TONE_NAMES, ALPHABET, SHENGMU, YUNMU, ZHENGTI
from tts_engine import get_tts

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROGRESS_FILE = os.path.join(BASE_DIR, "progress.json")
PARENT_PASSWORD = "1234"

COLORS = {
    "bg": "#F8FAFC", "primary": "#6366F1", "secondary": "#10B981", # Indigo & Emerald
    "accent": "#F59E0B", "purple": "#8B5CF6", "green": "#22C55E",
    "orange": "#F97316", "dark": "#1E293B", "card": "#FFFFFF",
    "shadow": "#E2E8F0", "star": "#FBBF24", "correct": "#10B981",
    "wrong": "#EF4444", "navy": "#334155", "pink": "#EC4899",
}


def make_btn(parent, text, bg, fg, cmd, font_obj=None, px=18, py=10):
    return tk.Button(parent, text=text, font=font_obj, bg=bg, fg=fg,
                     relief="flat", padx=px, pady=py, cursor="hand2",
                     activebackground=COLORS["dark"], activeforeground="white", 
                     borderwidth=0, highlightthickness=0, command=cmd)


def popup(root, msg, color=None, ms=1800):
    w = tk.Toplevel(root)
    w.overrideredirect(True)
    color = color or COLORS["correct"]
    w.configure(bg=color)
    rx, ry = root.winfo_rootx(), root.winfo_rooty()
    rw, rh = root.winfo_width(), root.winfo_height()
    w.geometry(f"320x65+{rx + rw//2 - 160}+{ry + rh//2 - 32}")
    tk.Label(w, text=msg, font=("Microsoft YaHei UI", 14, "bold"),
             bg=color, fg="white").pack(expand=True, pady=10)
    w.after(ms, w.destroy)


class LearningApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🌟 小小学习星 v2")
        self.geometry("940x680")
        self.minsize(860, 620)
        self.configure(bg=COLORS["bg"])
        cx = (self.winfo_screenwidth() - 940) // 2
        cy = (self.winfo_screenheight() - 680) // 2
        self.geometry(f"940x680+{cx}+{cy}")

        self.score = tk.IntVar(value=0)
        self.stars = tk.IntVar(value=0)
        self.tts_on = tk.BooleanVar(value=True)
        self.progress = self._load_progress()
        self.current_frame = None
        self.tts = get_tts()

        self._setup_fonts()
        self._build_header()
        self._build_nav()
        self.main_area = tk.Frame(self, bg=COLORS["bg"])
        self.main_area.pack(fill="both", expand=True, padx=8, pady=6)
        self.show_home()

    def _setup_fonts(self):
        self.f_title  = font.Font(family="Microsoft YaHei UI", size=24, weight="bold")
        self.f_big    = font.Font(family="Microsoft YaHei UI", size=18, weight="bold")
        self.f_med    = font.Font(family="Microsoft YaHei UI", size=14)
        self.f_sm     = font.Font(family="Microsoft YaHei UI", size=12)
        self.f_xs     = font.Font(family="Microsoft YaHei UI", size=10)
        self.f_emoji  = font.Font(size=40)
        self.f_char   = font.Font(family="Microsoft YaHei UI", size=72, weight="bold")
        self.f_pinyin = font.Font(family="Comic Sans MS", size=115, weight="bold")

    def _build_header(self):
        hdr = tk.Frame(self, bg=COLORS["primary"], height=60)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="🌟 小小学习星", font=self.f_big,
                 bg=COLORS["primary"], fg="white").pack(side="left", padx=18, pady=10)
        right = tk.Frame(hdr, bg=COLORS["primary"])
        right.pack(side="right", padx=12)
        tk.Checkbutton(right, text="🔊 语音", variable=self.tts_on,
                       font=self.f_sm, bg=COLORS["primary"], fg="white",
                       activebackground=COLORS["primary"], selectcolor=COLORS["secondary"],
                       ).pack(side="left", padx=8)
        for icon, var in [("⭐", self.stars), ("🏆", self.score)]:
            tk.Label(right, text=icon, font=self.f_med, bg=COLORS["primary"],
                     fg=COLORS["star"]).pack(side="left")
            tk.Label(right, textvariable=var, font=self.f_med,
                     bg=COLORS["primary"], fg="white").pack(side="left", padx=(2, 8))

    def _build_nav(self):
        nav = tk.Frame(self, bg=COLORS["secondary"], height=46)
        nav.pack(fill="x"); nav.pack_propagate(False)
        pages = [
            ("🏠 首页", self.show_home),
            ("🔤 拼音", self.show_pinyin),
            ("🇬🇧 英语", self.show_english),
            ("✏️ 书写练习", self.show_writing),
            ("🎯 测验", self.show_quiz),
            ("📊 进度", self.show_progress),
            ("👨‍👩‍👧 家长", self.show_parent),
        ]
        for text, cmd in pages:
            b = tk.Button(nav, text=text, font=self.f_sm, bg=COLORS["secondary"],
                          fg="white", relief="flat", padx=10, pady=8, cursor="hand2",
                          activebackground=COLORS["primary"], activeforeground="white",
                          command=cmd)
            b.pack(side="left", padx=1, pady=3)

    def _switch(self, FrameClass, *args, **kw):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = FrameClass(self.main_area, self, *args, **kw)
        self.current_frame.pack(fill="both", expand=True)

    def show_home(self):     self._switch(HomeFrame)
    def show_pinyin(self):   self._switch(PinyinFrame)
    def show_english(self):  self._switch(EnglishFrame)
    def show_writing(self):  self._switch(WritingFrame)
    def show_quiz(self):     self._switch(QuizFrame)
    def show_progress(self): self._switch(ProgressFrame)
    def show_parent(self):   self._switch(ParentFrame)

    def speak(self, text, lang="zh", pinyin_spelling=None):
        if self.tts_on.get():
            if lang == "zh" and pinyin_spelling:
                threading.Thread(target=lambda: self.tts.speak_pinyin(text, pinyin_spelling), daemon=True).start()
            else:
                threading.Thread(target=lambda: self.tts.speak(text, lang), daemon=True).start()

    def show_voice_help(self):
        msg = ("检测到你的系统可能缺少中文语音包，或者处于离线状态。\n\n"
               "如何安装本地中文语音：\n"
               "1. 打开 Windows『设置』\n"
               "2. 选择『时间和语言』->『语音』\n"
               "3. 在『管理语音』下点击『添加语音』\n"
               "4. 搜索并安装『中文(简体)』语音包\n"
               "5. 重启本软件即可听到流畅中文！\n\n"
               "当前已为你开启『拼音拼读模式』作为临时方案。")
        messagebox.showinfo("语音帮助", msg)

    def add_score(self, pts, st=0):
        self.score.set(self.score.get() + pts)
        self.stars.set(self.stars.get() + st)
        self._save_progress()

    def _load_progress(self):
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"learned_pinyin": [], "learned_english": [], "total_score": 0,
                "total_stars": 0, "quiz_history": [], "parent_pw": PARENT_PASSWORD,
                "daily_goal": 10}

    def _save_progress(self):
        self.progress["total_score"] = self.score.get()
        self.progress["total_stars"] = self.stars.get()
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)


# ───── 首页 ─────
class HomeFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self._build()

    def _build(self):
        tk.Label(self, text="🌈 欢迎来到小小学习星！", font=self.app.f_title,
                 bg=COLORS["bg"], fg=COLORS["dark"]).pack(pady=(14, 3))
        tk.Label(self, text="快来学拼音和英语吧，每天进步一点点！",
                 font=self.app.f_med, bg=COLORS["bg"], fg="#636e72").pack()
        grid = tk.Frame(self, bg=COLORS["bg"]); grid.pack(expand=True)
        cards = [
            ("🔤", "拼音学习", "声母·韵母·四声调", COLORS["primary"],   self.app.show_pinyin),
            ("🇬🇧", "英语学习", "单词·图片·朗读",   COLORS["secondary"], self.app.show_english),
            ("✏️", "书写练习", "字母·拼音手写",     COLORS["purple"],    self.app.show_writing),
            ("🎯", "小测验",   "挑战自己·赢星星",   COLORS["orange"],    self.app.show_quiz),
        ]
        for i, (em, title, desc, color, cmd) in enumerate(cards):
            c = self._card(grid, em, title, desc, color, cmd)
            c.grid(row=i//2, column=i%2, padx=14, pady=10)
        grid.columnconfigure(0, weight=1); grid.columnconfigure(1, weight=1)
        msgs = ["今天学习了吗？加油！💪", "每天进步一点点 🚀", "你最棒！🌟", "学习使我快乐！📚"]
        tk.Label(self, text=random.choice(msgs), font=self.app.f_sm,
                 bg=COLORS["bg"], fg=COLORS["purple"]).pack(pady=8)

    def _card(self, parent, em, title, desc, color, cmd):
        f = tk.Frame(parent, bg=COLORS["card"], width=290, height=148, cursor="hand2")
        f.pack_propagate(False)
        tk.Frame(f, bg=color, height=6).pack(fill="x")
        inner = tk.Frame(f, bg=COLORS["card"]); inner.pack(expand=True)
        tk.Label(inner, text=em, font=self.app.f_emoji, bg=COLORS["card"]).pack()
        tk.Label(inner, text=title, font=self.app.f_big, bg=COLORS["card"], fg=color).pack()
        tk.Label(inner, text=desc, font=self.app.f_xs, bg=COLORS["card"], fg="#636e72").pack()
        def enter(e):
            f["bg"] = "#F0F4FF"; inner["bg"] = "#F0F4FF"
            for w in inner.winfo_children(): w["bg"] = "#F0F4FF"
        def leave(e):
            f["bg"] = COLORS["card"]; inner["bg"] = COLORS["card"]
            for w in inner.winfo_children(): w["bg"] = COLORS["card"]
        for w in [f, inner] + list(inner.winfo_children()):
            w.bind("<Enter>", enter); w.bind("<Leave>", leave)
            w.bind("<Button-1>", lambda e, c=cmd: c())
        return f


# ───── 拼音学习 ─────
class PinyinFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.all_data = PINYIN_DATA
        self.category = tk.StringVar(value="声母")
        self.data = [d for d in self.all_data if d["type"] == self.category.get()]
        self.idx = 0
        self.flipped = False
        
        # UI Attributes initialized in _build
        self.cat_btns = {}
        self._build()

    def _update_category(self, cat):
        self.category.set(cat)
        self.data = [d for d in self.all_data if d["type"] == cat]
        self.idx = 0
        self.flipped = False
        self._highlight_cat()
        self._build_sidebar()
        self._update_card()

    def _build(self):
        # 顶部导航
        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", pady=10)
        
        cats = ["声母", "韵母", "整体认读"]
        btn_frame = tk.Frame(top, bg=COLORS["bg"])
        btn_frame.pack()
        
        for c in cats:
            btn = tk.Button(btn_frame, text=c, font=self.app.f_sm,
                           command=lambda x=c: self._update_category(x),
                           relief="flat", padx=15, pady=5)
            btn.pack(side="left", padx=5)
            self.cat_btns[c] = btn
        
        self._highlight_cat()

        # 主内容区域
        main = tk.Frame(self, bg=COLORS["bg"])
        main.pack(expand=True, fill="both", padx=40)
        
        # 左侧：列表
        self.side = tk.Frame(main, bg="white", width=180, relief="flat")
        self.side.pack(side="left", fill="y", pady=(0, 20))
        self.side.pack_propagate(False)
        self._build_sidebar()

        # 右侧：卡片区域
        self.content = tk.Frame(main, bg=COLORS["bg"])
        self.content.pack(side="right", expand=True, fill="both")
        
        # 居中放置大卡片
        self.card_area = tk.Frame(self.content, bg="white", highlightthickness=1,
                                 highlightbackground=COLORS["shadow"], cursor="hand2")
        self.card_area.place(relx=0.5, rely=0.45, anchor="center", width=320, height=420)
        self.card_area.bind("<Button-1>", lambda e: self._flip())
        
        self.label_main = tk.Label(self.card_area, text="", font=self.app.f_pinyin,
                                  bg="white", fg=COLORS["primary"])
        self.label_main.pack(expand=True, pady=(20, 0))
        
        self.label_info = tk.Label(self.card_area, text="", font=self.app.f_med,
                                  bg="white", fg="#94A3B8")
        self.label_info.pack(pady=(0, 30))

        # 底部控制按钮
        ctrl = tk.Frame(self.content, bg=COLORS["bg"])
        ctrl.place(relx=0.5, rely=0.88, anchor="center")
        
        make_btn(ctrl, "⬅ 上一个", COLORS["shadow"], COLORS["dark"], self._prev).pack(side="left", padx=10)
        make_btn(ctrl, "下一个 ➡", COLORS["primary"], "white", self._next).pack(side="left", padx=10)
        
        self._update_card()

    def _highlight_cat(self):
        for c, btn in self.cat_btns.items():
            if c == self.category.get():
                btn.config(bg=COLORS["primary"], fg="white")
            else:
                btn.config(bg=COLORS["shadow"], fg=COLORS["dark"])

    def _build_sidebar(self):
        for w in self.side.winfo_children(): w.destroy()
        
        tk.Label(self.side, text=f"{self.category.get()}列表", font=self.app.f_sm,
                 bg="white", fg="#95a5a6").pack(pady=10)
                 
        for i, item in enumerate(self.data):
            color = COLORS["primary"] if i == self.idx else COLORS["dark"]
            f_style = (self.app.f_sm.actual("family"), self.app.f_sm.actual("size"), 
                      "bold" if i == self.idx else "normal")
            btn = tk.Button(self.side, text=f" {item['pinyin']}  {item['char']}", 
                           font=f_style, fg=color, bg="white", relief="flat", anchor="w",
                           command=lambda x=i: self._jump(x))
            btn.pack(fill="x", padx=15, pady=2)

    def _update_card(self):
        if not self.data:
            self.label_main.config(text="无数据", fg=COLORS["dark"])
            self.label_info.config(text="请选择其他分类", fg="#95a5a6")
            return
        item = self.data[self.idx]
        
        if not self.flipped:
            # 正面：看拼音字母
            self.label_main.config(text=item["pinyin"], fg=COLORS["primary"])
            self.label_info.config(text="👆 点击翻转学习读音", fg="#bdc3c7")
        else:
            # 背面：看汉字并播放声音
            self.label_main.config(text=item["char"], fg=COLORS["dark"])
            self.label_info.config(text=f"拼音: {item['pinyin']}", fg=COLORS["primary"])
            self._speak()
        
    def _speak(self):
        if not self.data: return
        item = self.data[self.idx]
        self.app.speak(item["char"], lang="zh", pinyin_spelling=item.get("speak_py"))

    def _flip(self):
        if not self.data: return
        self.flipped = not self.flipped
        self._update_card()
        if self.flipped:
            # 记录进度：翻转过就算学过一次
            item = self.data[self.idx]
            prog = self.app.progress.setdefault("learned_pinyin", [])
            if item["pinyin"] not in prog:
                prog.append(item["pinyin"])
                self.app.add_score(10, 1) # 每学一个新卡片给10分和1星
                popup(self, "🌟 新发现！+10分 +1星", COLORS["correct"])

    def _next(self):
        if not self.data: return
        self.idx = (self.idx + 1) % len(self.data)
        self.flipped = False
        self._build_sidebar()
        self._update_card()

    def _prev(self):
        if not self.data: return
        self.idx = (self.idx - 1) % len(self.data)
        self.flipped = False
        self._build_sidebar()
        self._update_card()

    def _jump(self, i):
        self.idx = i
        self.flipped = False
        self._build_sidebar()
        self._update_card()


# ───── 英语学习 ─────
class EnglishFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app; self.idx = 0; self.flipped = False
        self.filtered = ENGLISH_DATA[:]; self._build()

    def _build(self):
        tk.Label(self, text="🇬🇧 英语学习", font=self.app.f_title,
                 bg=COLORS["bg"], fg=COLORS["secondary"]).pack(pady=(8, 2))
        cf = tk.Frame(self, bg=COLORS["bg"]); cf.pack()
        tk.Label(cf, text="分类：", font=self.app.f_sm, bg=COLORS["bg"]).pack(side="left", padx=4)
        self.cat_var = tk.StringVar(value="全部")
        for cat in ["全部", "水果", "动物", "颜色", "数字", "自然"]:
            tk.Radiobutton(cf, text=cat, variable=self.cat_var, value=cat,
                           font=self.app.f_sm, bg=COLORS["bg"],
                           activebackground=COLORS["bg"], selectcolor=COLORS["secondary"],
                           command=self._filter).pack(side="left", padx=5)
        self.card_area = tk.Frame(self, bg=COLORS["bg"]); self.card_area.pack(expand=True)
        btns = tk.Frame(self, bg=COLORS["bg"]); btns.pack(pady=10)
        for txt, color, fg, cmd in [
            ("⬅ 上一个", COLORS["shadow"], COLORS["dark"], self._prev),
            ("🔊 朗读",   COLORS["purple"], "white", self._speak),
            ("🔄 翻转",   COLORS["secondary"], "white", self._flip),
            ("✅ 已掌握", COLORS["correct"], "white", self._learned),
            ("下一个 ➡", COLORS["primary"], "white", self._next),
        ]:
            make_btn(btns, txt, color, fg, cmd, self.app.f_sm).pack(side="left", padx=6)
        self._show_card()

    def _filter(self):
        c = self.cat_var.get()
        self.filtered = ENGLISH_DATA[:] if c == "全部" else [d for d in ENGLISH_DATA if d["category"] == c]
        self.idx = 0; self._show_card()

    def _show_card(self):
        for w in self.card_area.winfo_children(): w.destroy()
        self.flipped = False
        if not self.filtered:
            tk.Label(self.card_area, text="该分类暂无数据",
                     font=self.app.f_med, bg=COLORS["bg"]).pack(pady=40); return
        item = self.filtered[self.idx]
        card = tk.Frame(self.card_area, bg=COLORS["card"], width=360, height=290)
        card.pack(pady=6); card.pack_propagate(False)
        tk.Frame(card, bg=COLORS["secondary"], height=8).pack(fill="x")
        inner = tk.Frame(card, bg=COLORS["card"]); inner.pack(expand=True, fill="both")
        tk.Label(inner, text=item["emoji"], font=font.Font(size=62),
                 bg=COLORS["card"]).pack(pady=(8, 0))
        tk.Label(inner, text=item["word"],
                 font=font.Font(family="Arial", size=30, weight="bold"),
                 bg=COLORS["card"], fg=COLORS["secondary"]).pack()
        tk.Label(inner, text="👆 翻转查看中文 | 🔊 点朗读听发音",
                 font=self.app.f_xs, bg=COLORS["card"], fg="#b2bec3").pack(pady=(2, 8))
        tk.Label(self.card_area, text=f"{self.idx+1}/{len(self.filtered)}  分类：{item['category']}",
                 font=self.app.f_xs, bg=COLORS["bg"], fg="#636e72").pack()

    def _flip(self):
        if not self.filtered: return
        item = self.filtered[self.idx]
        if not self.flipped:
            for w in self.card_area.winfo_children(): w.destroy()
            card = tk.Frame(self.card_area, bg="#E8F5E9", width=360, height=290)
            card.pack(pady=6); card.pack_propagate(False)
            tk.Frame(card, bg=COLORS["correct"], height=8).pack(fill="x")
            inner = tk.Frame(card, bg="#E8F5E9"); inner.pack(expand=True, fill="both")
            tk.Label(inner, text=item["emoji"], font=font.Font(size=48),
                     bg="#E8F5E9").pack(pady=(8, 0))
            tk.Label(inner, text=item["word"],
                     font=font.Font(family="Arial", size=24, weight="bold"),
                     bg="#E8F5E9", fg=COLORS["secondary"]).pack()
            tk.Label(inner, text=f"中文：{item['chinese']}",
                     font=font.Font(family="Microsoft YaHei", size=22, weight="bold"),
                     bg="#E8F5E9", fg=COLORS["dark"]).pack(pady=4)
            tk.Label(self.card_area, text=f"🔊 大声读：{item['word'].upper()}",
                     font=self.app.f_sm, bg=COLORS["bg"], fg=COLORS["purple"]).pack()
            self.flipped = True; self.app.add_score(1); self._speak()
        else:
            self._show_card()

    def _speak(self):
        if not self.filtered: return
        self.app.speak(self.filtered[self.idx]["word"], lang="en")

    def _learned(self):
        if not self.filtered: return
        item = self.filtered[self.idx]
        lst = self.app.progress.setdefault("learned_english", [])
        if item["word"] not in lst:
            lst.append(item["word"]); self.app.add_score(5, 1)
            popup(self, "🌟 太棒了！+5分 +1星", COLORS["correct"])
        self._next()

    def _prev(self):
        if self.idx > 0: self.idx -= 1; self._show_card()

    def _next(self):
        if self.filtered and self.idx < len(self.filtered)-1:
            self.idx += 1; self._show_card()
        else: popup(self, "🎉 本类全部学完！", COLORS["star"])


# ───── 书写练习 ─────
class WritingFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app; self.mode = tk.StringVar(value="alphabet")
        self.current_items = ALPHABET[:]; self.idx = 0
        self.last_x = self.last_y = 0; self._build()

    def _build(self):
        tk.Label(self, text="✏️ 书写练习", font=self.app.f_title,
                 bg=COLORS["bg"], fg=COLORS["purple"]).pack(pady=(8, 2))
        tk.Label(self, text="在右侧画布上练习书写，感受字形！",
                 font=self.app.f_sm, bg=COLORS["bg"], fg="#636e72").pack()
        mf = tk.Frame(self, bg=COLORS["bg"]); mf.pack(pady=6)
        for txt, val, color in [("🔤 声母", "shengmu", COLORS["primary"]),
                                  ("🔤 韵母", "yunmu",   COLORS["secondary"]),
                                  ("✨ 整体", "zhengti", COLORS["star"]),
                                  ("🇬🇧 字母", "alphabet", COLORS["purple"])]:
            tk.Radiobutton(mf, text=txt, variable=self.mode, value=val,
                           font=self.app.f_sm, bg=COLORS["bg"],
                           activebackground=COLORS["bg"], selectcolor=color,
                           command=self._switch_mode).pack(side="left", padx=12)
        main = tk.Frame(self, bg=COLORS["bg"]); main.pack(expand=True, fill="both", padx=20)
        main.columnconfigure(0, weight=1); main.columnconfigure(1, weight=2)
        # 左：参考字符
        left = tk.Frame(main, bg=COLORS["card"], width=230)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=4)
        left.pack_propagate(False)
        tk.Frame(left, bg=COLORS["purple"], height=6).pack(fill="x")
        tk.Label(left, text="参考字符", font=self.app.f_sm,
                 bg=COLORS["card"], fg="#636e72").pack(pady=(10, 0))
        self.ref_label = tk.Label(left, text="A",
                                   font=font.Font(family="Arial", size=90, weight="bold"),
                                   bg=COLORS["card"], fg=COLORS["purple"])
        self.ref_label.pack(expand=True)
        self.name_label = tk.Label(left, text="字母 A", font=self.app.f_med,
                                    bg=COLORS["card"], fg=COLORS["dark"])
        self.name_label.pack(pady=(0, 6))
        make_btn(left, "🔊 朗读", COLORS["purple"], "white",
                 self._speak, self.app.f_sm).pack(pady=(0, 10))
        # 右：画布
        right = tk.Frame(main, bg=COLORS["card"])
        right.grid(row=0, column=1, sticky="nsew", pady=4)
        tk.Frame(right, bg=COLORS["secondary"], height=6).pack(fill="x")
        tk.Label(right, text="在下面的画布上练习书写 ↓",
                 font=self.app.f_sm, bg=COLORS["card"], fg="#636e72").pack(pady=4)
        self.canvas = tk.Canvas(right, bg="white", cursor="pencil",
                                highlightthickness=1, highlightbackground=COLORS["shadow"])
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.canvas.bind("<ButtonPress-1>", lambda e: self._set_pos(e))
        self.canvas.bind("<B1-Motion>", self._draw)
        # 底部按钮
        bf = tk.Frame(self, bg=COLORS["bg"]); bf.pack(pady=8)
        for txt, color, fg, cmd in [
            ("⬅ 上一个", COLORS["shadow"], COLORS["dark"], self._prev),
            ("🗑️ 清除", COLORS["orange"], "white", self._clear),
            ("🔊 朗读",  COLORS["purple"], "white", self._speak),
            ("下一个 ➡", COLORS["primary"], "white", self._next),
        ]:
            make_btn(bf, txt, color, fg, cmd, self.app.f_sm).pack(side="left", padx=8)
        self._update_display()

    def _switch_mode(self):
        m = self.mode.get()
        self.current_items = {"alphabet": ALPHABET, "shengmu": SHENGMU, "yunmu": YUNMU, "zhengti": ZHENGTI}[m]
        self.idx = 0; self._update_display()

    def _update_display(self):
        if not self.current_items: return
        item = self.current_items[self.idx]
        self.ref_label["text"] = item.upper() if self.mode.get() == "alphabet" else item
        m = self.mode.get()
        names = {"alphabet": "字母", "shengmu": "声母", "yunmu": "韵母", "zhengti": "整体认读"}
        self.name_label["text"] = f"{names[m]} {item.upper() if m=='alphabet' else item}"; self._clear()

    def _set_pos(self, e): self.last_x, self.last_y = e.x, e.y

    def _draw(self, e):
        self.canvas.create_line(self.last_x, self.last_y, e.x, e.y,
                                width=5, fill=COLORS["primary"], capstyle="round", smooth=True)
        self.last_x, self.last_y = e.x, e.y

    def _clear(self): self.canvas.delete("all")

    def _speak(self):
        if not self.current_items: return
        item = self.current_items[self.idx]
        mode = self.mode.get()
        if mode == "alphabet":
            self.app.speak(item, lang="en")
        else:
            # 查找拼音对应的数据
            match = next((d for d in PINYIN_DATA if d["pinyin"] == item), None)
            if match:
                self.app.speak(match["char"], lang="zh", pinyin_spelling=match.get("speak_py"))
            else:
                self.app.speak(item, lang="en") # 兜底读字母

    def _prev(self):
        if self.idx > 0: self.idx -= 1; self._update_display()

    def _next(self):
        if self.idx < len(self.current_items)-1:
            self.idx += 1; self._update_display(); self.app.add_score(2)


# ───── 小测验 ─────
class QuizFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app; self.q_idx = self.correct = 0
        self.questions = []; self.answered = False; self._build_select()

    def _build_select(self):
        for w in self.winfo_children(): w.destroy()
        tk.Label(self, text="🎯 小测验", font=self.app.f_title,
                 bg=COLORS["bg"], fg=COLORS["purple"]).pack(pady=(18, 8))
        tk.Label(self, text="选择测验模式：", font=self.app.f_med, bg=COLORS["bg"]).pack(pady=4)
        bf = tk.Frame(self, bg=COLORS["bg"]); bf.pack(pady=18)
        for txt, mode, color in [("🔤 拼音认读", "py", COLORS["primary"]),
                                   ("🇬🇧 英语认词", "en", COLORS["secondary"]),
                                   ("🎲 混合挑战", "mix", COLORS["purple"])]:
            card = tk.Frame(bf, bg=COLORS["card"], width=190, height=130, cursor="hand2")
            card.pack(side="left", padx=14); card.pack_propagate(False)
            tk.Frame(card, bg=color, height=6).pack(fill="x")
            inner = tk.Frame(card, bg=COLORS["card"]); inner.pack(expand=True)
            tk.Label(inner, text=txt.split()[0], font=font.Font(size=34),
                     bg=COLORS["card"]).pack()
            tk.Label(inner, text=" ".join(txt.split()[1:]),
                     font=self.app.f_sm, bg=COLORS["card"], fg=color).pack()
            make_btn(inner, "开始！", color, "white",
                     lambda m=mode: self._start(m), self.app.f_sm, 18, 4).pack(pady=4)

    def _start(self, mode):
        pool = []
        if mode in ("py", "mix"): pool += random.sample(PINYIN_DATA, min(10, len(PINYIN_DATA)))
        if mode in ("en", "mix"): pool += random.sample(ENGLISH_DATA, min(10, len(ENGLISH_DATA)))
        random.shuffle(pool); self.questions = pool[:12]
        self.q_idx = self.correct = 0; self.answered = False; self._show_q()

    def _show_q(self):
        for w in self.winfo_children(): w.destroy()
        if self.q_idx >= len(self.questions): self._show_result(); return
        item = self.questions[self.q_idx]
        top = tk.Frame(self, bg=COLORS["bg"]); top.pack(fill="x", padx=18, pady=(8, 4))
        tk.Label(top, text=f"第 {self.q_idx+1}/{len(self.questions)} 题",
                 font=self.app.f_med, bg=COLORS["bg"], fg=COLORS["purple"]).pack(side="left")
        tk.Label(top, text=f"✅ {self.correct}",
                 font=self.app.f_sm, bg=COLORS["bg"], fg=COLORS["correct"]).pack(side="right")
        if "pinyin" in item: self._pinyin_q(item)
        else: self._english_q(item)

    def _pinyin_q(self, item):
        qf = tk.Frame(self, bg=COLORS["card"], width=500, height=130)
        qf.pack(pady=8); qf.pack_propagate(False)
        tk.Frame(qf, bg=COLORS["primary"], height=6).pack(fill="x")
        inner = tk.Frame(qf, bg=COLORS["card"]); inner.pack(expand=True)
        tk.Label(inner, text="这个汉字的拼音是？",
                 font=self.app.f_sm, bg=COLORS["card"], fg="#636e72").pack(pady=(6, 0))
        cl = tk.Label(inner, text=item["char"],
                      font=font.Font(family="Microsoft YaHei", size=50, weight="bold"),
                      bg=COLORS["card"], fg=COLORS["dark"], cursor="hand2")
        cl.pack()
        cl.bind("<Button-1>", lambda e: self.app.speak(item["char"], "zh"))
        tk.Label(inner, text="🔊 点击汉字听发音", font=self.app.f_xs,
                 bg=COLORS["card"], fg="#b2bec3").pack()
        wrong = [d for d in PINYIN_DATA if d["pinyin"] != item["pinyin"]]
        random.shuffle(wrong)
        opts = [item["pinyin"]] + [d["pinyin"] for d in wrong[:3]]
        random.shuffle(opts); self._show_opts(opts, item["pinyin"])

    def _english_q(self, item):
        qf = tk.Frame(self, bg=COLORS["card"], width=500, height=130)
        qf.pack(pady=8); qf.pack_propagate(False)
        tk.Frame(qf, bg=COLORS["secondary"], height=6).pack(fill="x")
        inner = tk.Frame(qf, bg=COLORS["card"]); inner.pack(expand=True)
        tk.Label(inner, text="这个图片对应的英语单词是？",
                 font=self.app.f_sm, bg=COLORS["card"], fg="#636e72").pack(pady=(6, 0))
        el = tk.Label(inner, text=f"{item['emoji']} {item['chinese']}",
                      font=font.Font(size=30), bg=COLORS["card"], cursor="hand2")
        el.pack()
        el.bind("<Button-1>", lambda e: self.app.speak(item["word"], "en"))
        tk.Label(inner, text="🔊 点击图片听发音", font=self.app.f_xs,
                 bg=COLORS["card"], fg="#b2bec3").pack()
        wrong = [d for d in ENGLISH_DATA if d["word"] != item["word"]]
        random.shuffle(wrong)
        opts = [item["word"]] + [d["word"] for d in wrong[:3]]
        random.shuffle(opts); self._show_opts(opts, item["word"])

    def _show_opts(self, opts, correct):
        of = tk.Frame(self, bg=COLORS["bg"]); of.pack(pady=8)
        self._btns = []
        for i, opt in enumerate(opts):
            btn = tk.Button(of, text=opt,
                            font=font.Font(family="Microsoft YaHei", size=14, weight="bold"),
                            width=13, pady=10, relief="flat",
                            bg=COLORS["secondary"], fg="white", cursor="hand2",
                            command=lambda o=opt: self._check(o, correct))
            btn.grid(row=i//2, column=i%2, padx=10, pady=6)
            self._btns.append((btn, opt))
        self.answered = False

    def _check(self, chosen, correct):
        if self.answered: return
        self.answered = True
        for btn, opt in self._btns:
            btn["bg"] = COLORS["correct"] if opt == correct else (COLORS["wrong"] if opt == chosen else COLORS["secondary"])
        if chosen == correct:
            self.correct += 1; self.app.add_score(10, 1)
            msg = random.choice(["🎉 太棒了！", "✨ 真聪明！", "🌟 答对啦！"])
        else:
            msg = f"❌ 正确答案：{correct}"
        tk.Label(self, text=msg, font=self.app.f_med, bg=COLORS["bg"],
                 fg=COLORS["correct"] if chosen == correct else COLORS["wrong"]).pack(pady=4)
        self.after(1300, self._next_q)

    def _next_q(self): self.q_idx += 1; self._show_q()

    def _show_result(self):
        for w in self.winfo_children(): w.destroy()
        total = len(self.questions); pct = int(self.correct/total*100) if total else 0
        em, txt, color = ("🏆", "优秀！", COLORS["star"]) if pct >= 90 else \
                         ("🌟", "良好！", COLORS["correct"]) if pct >= 70 else \
                         ("👍", "继续！", COLORS["secondary"]) if pct >= 50 else \
                         ("💪", "加油！", COLORS["primary"])
        tk.Label(self, text=em, font=font.Font(size=60), bg=COLORS["bg"]).pack(pady=(28, 4))
        tk.Label(self, text=txt, font=self.app.f_title, bg=COLORS["bg"], fg=color).pack()
        tk.Label(self, text=f"答对 {self.correct}/{total} 题 ({pct}%)",
                 font=self.app.f_big, bg=COLORS["bg"], fg=COLORS["dark"]).pack(pady=6)
        tk.Label(self, text=f"🏆 +{self.correct*10}分  ⭐ +{self.correct}星",
                 font=self.app.f_med, bg=COLORS["bg"], fg=COLORS["purple"]).pack()
        hst = self.app.progress.setdefault("quiz_history", [])
        hst.append({"score": self.correct, "total": total, "pct": pct})
        if len(hst) > 20: hst.pop(0)
        self.app._save_progress()
        bf = tk.Frame(self, bg=COLORS["bg"]); bf.pack(pady=18)
        make_btn(bf, "🔄 再来一次", COLORS["secondary"], "white",
                 self._build_select, self.app.f_med).pack(side="left", padx=10)
        make_btn(bf, "🏠 回首页", COLORS["primary"], "white",
                 self.app.show_home, self.app.f_med).pack(side="left", padx=10)


# ───── 进度统计 ─────
class ProgressFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app; self._build()

    def _build(self):
        tk.Label(self, text="📊 我的进度", font=self.app.f_title,
                 bg=COLORS["bg"], fg=COLORS["orange"]).pack(pady=(12, 4))
        lp = len(self.app.progress.get("learned_pinyin", []))
        le = len(self.app.progress.get("learned_english", []))
        sc = self.app.score.get(); st = self.app.stars.get()
        cf = tk.Frame(self, bg=COLORS["bg"]); cf.pack()
        for i, (em, lbl, val, color) in enumerate([
            ("📚", "拼音已学", f"{lp}/{len(PINYIN_DATA)}", COLORS["primary"]),
            ("🇬🇧", "英语已学", f"{le}/{len(ENGLISH_DATA)}", COLORS["secondary"]),
            ("🏆", "总得分", str(sc), COLORS["purple"]),
            ("⭐", "星星数", str(st), COLORS["star"]),
        ]):
            card = tk.Frame(cf, bg=COLORS["card"], width=155, height=108)
            card.grid(row=0, column=i, padx=10, pady=8); card.pack_propagate(False)
            tk.Frame(card, bg=color, height=6).pack(fill="x")
            inner = tk.Frame(card, bg=COLORS["card"]); inner.pack(expand=True)
            tk.Label(inner, text=em, font=font.Font(size=24), bg=COLORS["card"]).pack()
            tk.Label(inner, text=val, font=self.app.f_big, bg=COLORS["card"], fg=color).pack()
            tk.Label(inner, text=lbl, font=self.app.f_xs, bg=COLORS["card"], fg="#636e72").pack()
        tk.Label(self, text="📈 掌握进度", font=self.app.f_med,
                 bg=COLORS["bg"], fg=COLORS["dark"]).pack(pady=(12, 4))
        df = tk.Frame(self, bg=COLORS["bg"]); df.pack(fill="x", padx=60)
        for lbl, learned, total, color in [
            ("拼音", lp, len(PINYIN_DATA), COLORS["primary"]),
            ("英语", le, len(ENGLISH_DATA), COLORS["secondary"]),
        ]:
            row = tk.Frame(df, bg=COLORS["bg"]); row.pack(fill="x", pady=5)
            tk.Label(row, text=lbl, width=6, anchor="w",
                     font=self.app.f_sm, bg=COLORS["bg"]).pack(side="left")
            bar = ttk.Progressbar(row, length=340, mode="determinate", maximum=total, value=learned)
            bar.pack(side="left", padx=8)
            pct = int(learned/total*100) if total else 0
            tk.Label(row, text=f"{pct}%", font=self.app.f_sm, bg=COLORS["bg"], fg=color).pack(side="left")
        hist = self.app.progress.get("quiz_history", [])
        if hist:
            tk.Label(self, text="📝 最近测验", font=self.app.f_med,
                     bg=COLORS["bg"], fg=COLORS["dark"]).pack(pady=(10, 2))
            for h in hist[-5:][::-1]:
                tk.Label(self, text=f"答对 {h['score']}/{h['total']} 题  ({h['pct']}%)",
                         font=self.app.f_sm, bg=COLORS["bg"], fg="#636e72").pack()
        tip = "🔤 多练习拼音，点开拼音模块！" if lp < len(PINYIN_DATA)//2 else \
              "🇬🇧 去英语模块探索更多单词！" if le < len(ENGLISH_DATA)//2 else \
              "🌟 你学得很棒！去小测验检验！"
        tk.Label(self, text=tip, font=self.app.f_med,
                 bg=COLORS["bg"], fg=COLORS["purple"]).pack(pady=8)
        make_btn(self, "🗑️ 重置进度", COLORS["shadow"], COLORS["dark"],
                 self._reset, self.app.f_sm).pack(pady=6)

    def _reset(self):
        if messagebox.askyesno("确认", "确定要重置所有学习进度吗？"):
            self.app.progress.update({"learned_pinyin": [], "learned_english": [],
                                      "total_score": 0, "total_stars": 0, "quiz_history": []})
            self.app.score.set(0); self.app.stars.set(0); self.app._save_progress()
            self._build()


# ───── 家长管理 ─────
class ParentFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app; self._build_lock()

    def _build_lock(self):
        for w in self.winfo_children(): w.destroy()
        tk.Label(self, text="👨‍👩‍👧 家长管理", font=self.app.f_title,
                 bg=COLORS["bg"], fg=COLORS["navy"]).pack(pady=(40, 10))
        tk.Label(self, text="请输入家长密码：", font=self.app.f_med, bg=COLORS["bg"]).pack(pady=8)
        self.pw_var = tk.StringVar()
        e = tk.Entry(self, textvariable=self.pw_var, show="*", font=self.app.f_big,
                     width=10, justify="center", relief="flat", bd=2,
                     highlightthickness=2, highlightbackground=COLORS["shadow"],
                     highlightcolor=COLORS["primary"])
        e.pack(pady=6); e.focus(); e.bind("<Return>", lambda ev: self._check_pw())
        make_btn(self, "🔓 进入管理", COLORS["navy"], "white",
                 self._check_pw, self.app.f_med).pack(pady=10)
        tk.Label(self, text="默认密码：1234", font=self.app.f_xs,
                 bg=COLORS["bg"], fg="#b2bec3").pack()

    def _check_pw(self):
        if self.pw_var.get() == self.app.progress.get("parent_pw", PARENT_PASSWORD):
            self._build_panel()
        else:
            messagebox.showerror("错误", "密码不正确！")

    def _build_panel(self):
        for w in self.winfo_children(): w.destroy()
        tk.Label(self, text="👨‍👩‍👧 家长管理面板", font=self.app.f_title,
                 bg=COLORS["bg"], fg=COLORS["navy"]).pack(pady=(12, 4))
        lp = len(self.app.progress.get("learned_pinyin", []))
        le = len(self.app.progress.get("learned_english", []))
        hist = self.app.progress.get("quiz_history", [])
        avg = int(sum(h["pct"] for h in hist)/len(hist)) if hist else 0
        sf = tk.Frame(self, bg=COLORS["bg"]); sf.pack(fill="x", padx=40, pady=8)
        for i, (txt, color) in enumerate([
            (f"拼音已学 {lp}/{len(PINYIN_DATA)}", COLORS["primary"]),
            (f"英语已学 {le}/{len(ENGLISH_DATA)}", COLORS["secondary"]),
            (f"测验次数 {len(hist)} 次",            COLORS["purple"]),
            (f"平均得分率 {avg}%",                  COLORS["star"]),
        ]):
            tk.Label(sf, text=txt, font=self.app.f_sm, bg=COLORS["card"], fg=color,
                     padx=14, pady=8, width=22).grid(row=i//2, column=i%2, padx=8, pady=6)
        tk.Label(self, text="⚙️ 设置", font=self.app.f_med,
                 bg=COLORS["bg"], fg=COLORS["dark"]).pack(pady=(10, 4))
        sf2 = tk.Frame(self, bg=COLORS["bg"]); sf2.pack(fill="x", padx=80)
        # 修改密码
        pw_row = tk.Frame(sf2, bg=COLORS["bg"]); pw_row.pack(fill="x", pady=6)
        tk.Label(pw_row, text="修改密码：", font=self.app.f_sm,
                 bg=COLORS["bg"], width=12, anchor="w").pack(side="left")
        self.new_pw = tk.Entry(pw_row, show="*", font=self.app.f_sm, width=12,
                                relief="flat", bd=2, highlightthickness=1)
        self.new_pw.pack(side="left", padx=8)
        make_btn(pw_row, "保存", COLORS["navy"], "white",
                 self._change_pw, self.app.f_sm, 10, 4).pack(side="left")
        # 语音开关
        tts_row = tk.Frame(sf2, bg=COLORS["bg"]); tts_row.pack(fill="x", pady=6)
        tk.Label(tts_row, text="语音朗读：", font=self.app.f_sm,
                 bg=COLORS["bg"], width=12, anchor="w").pack(side="left")
        tk.Checkbutton(tts_row, text="开启语音朗读", variable=self.app.tts_on,
                       font=self.app.f_sm, bg=COLORS["bg"],
                       activebackground=COLORS["bg"],
                       selectcolor=COLORS["secondary"]).pack(side="left")
        # 每日目标
        gr = tk.Frame(sf2, bg=COLORS["bg"]); gr.pack(fill="x", pady=6)
        tk.Label(gr, text="每日目标：", font=self.app.f_sm,
                 bg=COLORS["bg"], width=12, anchor="w").pack(side="left")
        self.goal_var = tk.IntVar(value=self.app.progress.get("daily_goal", 10))
        tk.Spinbox(gr, from_=5, to=50, increment=5, textvariable=self.goal_var,
                   font=self.app.f_sm, width=5).pack(side="left", padx=8)
        tk.Label(gr, text="张卡片", font=self.app.f_sm, bg=COLORS["bg"]).pack(side="left")
        make_btn(gr, "保存", COLORS["navy"], "white",
                 self._save_goal, self.app.f_sm, 10, 4).pack(side="left", padx=8)
        if hist:
            tk.Label(self, text="📝 最近5次测验", font=self.app.f_med,
                     bg=COLORS["bg"], fg=COLORS["dark"]).pack(pady=(10, 2))
            for h in hist[-5:][::-1]:
                tk.Label(self, text=f"答对 {h['score']}/{h['total']} 题  正确率 {h['pct']}%",
                         font=self.app.f_sm, bg=COLORS["bg"], fg="#636e72").pack()
        make_btn(self, "🔒 退出管理", COLORS["shadow"], COLORS["dark"],
                 self._build_lock, self.app.f_sm).pack(pady=12)
        
        make_btn(self, "❓ 为什么没有中文声音？", COLORS["purple"], "white",
                 self.app.show_voice_help, self.app.f_sm).pack(pady=4)

    def _change_pw(self):
        new = self.new_pw.get().strip()
        if len(new) < 4: messagebox.showwarning("提示", "密码至少4位！"); return
        self.app.progress["parent_pw"] = new; self.app._save_progress()
        messagebox.showinfo("成功", "密码已修改！"); self.new_pw.delete(0, "end")

    def _save_goal(self):
        self.app.progress["daily_goal"] = self.goal_var.get(); self.app._save_progress()
        popup(self, f"✅ 每日目标 {self.goal_var.get()} 张！", COLORS["correct"])


if __name__ == "__main__":
    app = LearningApp()
    app.mainloop()
