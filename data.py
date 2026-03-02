"""数据模块 - 完整拼音与英语单词表"""

# 拼音基础数据：声母与韵母的读音映射
PINYIN_DATA = [
    # 声母
    {"char": "波", "pinyin": "b", "type": "声母", "speak_zh": "波", "speak_py": "b o"},
    {"char": "坡", "pinyin": "p", "type": "声母", "speak_zh": "坡", "speak_py": "p o"},
    {"char": "摸", "pinyin": "m", "type": "声母", "speak_zh": "摸", "speak_py": "m o"},
    {"char": "佛", "pinyin": "f", "type": "声母", "speak_zh": "佛", "speak_py": "f o"},
    {"char": "得", "pinyin": "d", "type": "声母", "speak_zh": "得", "speak_py": "d e"},
    {"char": "特", "pinyin": "t", "type": "声母", "speak_zh": "特", "speak_py": "t e"},
    {"char": "讷", "pinyin": "n", "type": "声母", "speak_zh": "讷", "speak_py": "n e"},
    {"char": "勒", "pinyin": "l", "type": "声母", "speak_zh": "勒", "speak_py": "l e"},
    {"char": "哥", "pinyin": "g", "type": "声母", "speak_zh": "哥", "speak_py": "g e"},
    {"char": "科", "pinyin": "k", "type": "声母", "speak_zh": "科", "speak_py": "k e"},
    {"char": "喝", "pinyin": "h", "type": "声母", "speak_zh": "喝", "speak_py": "h e"},
    {"char": "鸡", "pinyin": "j", "type": "声母", "speak_zh": "鸡", "speak_py": "j i"},
    {"char": "七", "pinyin": "q", "type": "声母", "speak_zh": "七", "speak_py": "q i"},
    {"char": "西", "pinyin": "x", "type": "声母", "speak_zh": "西", "speak_py": "x i"},
    {"char": "知", "pinyin": "zh", "type": "声母", "speak_zh": "知", "speak_py": "zh i"},
    {"char": "吃", "pinyin": "ch", "type": "声母", "speak_zh": "吃", "speak_py": "ch i"},
    {"char": "狮", "pinyin": "sh", "type": "声母", "speak_zh": "狮", "speak_py": "sh i"},
    {"char": "日", "pinyin": "r", "type": "声母", "speak_zh": "日", "speak_py": "r i"},
    {"char": "滋", "pinyin": "z", "type": "声母", "speak_zh": "滋", "speak_py": "z i"},
    {"char": "刺", "pinyin": "c", "type": "声母", "speak_zh": "刺", "speak_py": "c i"},
    {"char": "丝", "pinyin": "s", "type": "声母", "speak_zh": "丝", "speak_py": "s i"},
    {"char": "衣", "pinyin": "y", "type": "声母", "speak_zh": "衣", "speak_py": "y i"},
    {"char": "乌", "pinyin": "w", "type": "声母", "speak_zh": "乌", "speak_py": "w u"},
    
    # 韵母 (单韵母)
    {"char": "啊", "pinyin": "a", "type": "韵母", "speak_zh": "啊", "speak_py": "a"},
    {"char": "喔", "pinyin": "o", "type": "韵母", "speak_zh": "喔", "speak_py": "o"},
    {"char": "鹅", "pinyin": "e", "type": "韵母", "speak_zh": "鹅", "speak_py": "e"},
    {"char": "衣", "pinyin": "i", "type": "韵母", "speak_zh": "衣", "speak_py": "i"},
    {"char": "乌", "pinyin": "u", "type": "韵母", "speak_zh": "乌", "speak_py": "u"},
    {"char": "鱼", "pinyin": "ü", "type": "韵母", "speak_zh": "鱼", "speak_py": "v"},
    
    # 复韵母
    {"char": "哎", "pinyin": "ai", "type": "韵母", "speak_zh": "哎", "speak_py": "ai"},
    {"char": "欸", "pinyin": "ei", "type": "韵母", "speak_zh": "欸", "speak_py": "ei"},
    {"char": "危", "pinyin": "ui", "type": "韵母", "speak_zh": "危", "speak_py": "ui"},
    {"char": "熬", "pinyin": "ao", "type": "韵母", "speak_zh": "熬", "speak_py": "ao"},
    {"char": "欧", "pinyin": "ou", "type": "韵母", "speak_zh": "欧", "speak_py": "ou"},
    {"char": "优", "pinyin": "iu", "type": "韵母", "speak_zh": "优", "speak_py": "iu"},
    {"char": "耶", "pinyin": "ie", "type": "韵母", "speak_zh": "耶", "speak_py": "ie"},
    {"char": "约", "pinyin": "üe", "type": "韵母", "speak_zh": "约", "speak_py": "ve"},
    {"char": "耳", "pinyin": "er", "type": "韵母", "speak_zh": "耳", "speak_py": "er"},
    
    # 整体认读音节
    {"char": "织", "pinyin": "zhi", "type": "整体认读", "speak_zh": "织", "speak_py": "zh i"},
    {"char": "吃", "pinyin": "chi", "type": "整体认读", "speak_zh": "吃", "speak_py": "ch i"},
    {"char": "狮", "pinyin": "shi", "type": "整体认读", "speak_zh": "狮", "speak_py": "sh i"},
    {"char": "日", "pinyin": "ri",  "type": "整体认读", "speak_zh": "日", "speak_py": "r i"},
    {"char": "字", "pinyin": "zi",  "type": "整体认读", "speak_zh": "字", "speak_py": "z i"},
    {"char": "词", "pinyin": "ci",  "type": "整体认读", "speak_zh": "词", "speak_py": "c i"},
    {"char": "丝", "pinyin": "si",  "type": "整体认读", "speak_zh": "丝", "speak_py": "s i"},
    {"char": "衣", "pinyin": "yi",  "type": "整体认读", "speak_zh": "衣", "speak_py": "y i"},
    {"char": "屋", "pinyin": "wu",  "type": "整体认读", "speak_zh": "屋", "speak_py": "w u"},
    {"char": "鱼", "pinyin": "yu",  "type": "整体认读", "speak_zh": "鱼", "speak_py": "y u"},
]

ENGLISH_DATA = [
    {"word": "Apple",  "chinese": "苹果", "emoji": "🍎", "category": "水果"},
    {"word": "Banana", "chinese": "香蕉", "emoji": "🍌", "category": "水果"},
    {"word": "Orange", "chinese": "橙子", "emoji": "🍊", "category": "水果"},
    {"word": "Grape",  "chinese": "葡萄", "emoji": "🍇", "category": "水果"},
    {"word": "Peach",  "chinese": "桃子", "emoji": "🍑", "category": "水果"},
    {"word": "Cat",    "chinese": "猫",   "emoji": "🐱", "category": "动物"},
    {"word": "Dog",    "chinese": "狗",   "emoji": "🐶", "category": "动物"},
    {"word": "Rabbit", "chinese": "兔子", "emoji": "🐰", "category": "动物"},
    {"word": "Tiger",  "chinese": "老虎", "emoji": "🐯", "category": "动物"},
    {"word": "Lion",   "chinese": "狮子", "emoji": "🦁", "category": "动物"},
    {"word": "Red",    "chinese": "红色", "emoji": "🔴", "category": "颜色"},
    {"word": "Blue",   "chinese": "蓝色", "emoji": "🔵", "category": "颜色"},
    {"word": "Green",  "chinese": "绿色", "emoji": "🟢", "category": "颜色"},
    {"word": "Sunny",  "chinese": "晴天", "emoji": "☀️", "category": "天气"},
    {"word": "Rainy",  "chinese": "下雨", "emoji": "🌧️", "category": "天气"},
    {"word": "Star",   "chinese": "星星", "emoji": "⭐", "category": "自然"},
]

TONE_NAMES = ["", "一声（阴平）ā", "二声（阳平）á", "三声（上声）ǎ", "四声（去声）à", "轻声"]

ALPHABET = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
SHENGMU = [d["pinyin"] for d in PINYIN_DATA if d["type"] == "声母"]
YUNMU = [d["pinyin"] for d in PINYIN_DATA if d["type"] == "韵母"]
ZHENGTI = [d["pinyin"] for d in PINYIN_DATA if d["type"] == "整体认读"]
