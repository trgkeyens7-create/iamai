"""
TTS 语音引擎 v7 - 完美中英切换版
通过显式设置 SAPI 语音对象，解决中英文读音混淆问题
"""

import threading
import queue
import win32com.client
import pythoncom


class TTSEngine:
    """离线 SAPI 语音引擎，强制中英语音包切换"""

    def __init__(self):
        self._q = queue.Queue()
        self._zh_voice = None
        self._en_voice = None
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        pythoncom.CoInitialize()
        try:
            sapi = win32com.client.Dispatch("SAPI.SpVoice")
            
            # 寻找并存储中英文语音包
            voices = sapi.GetVoices()
            for i in range(voices.Count):
                try:
                    v = voices.Item(i)
                    desc = v.GetDescription().lower()
                    # 优先找中文
                    if not self._zh_voice and ("chinese" in desc or "zh-cn" in desc or "huihui" in desc):
                        self._zh_voice = v
                    # 优先找英文 (Zira 或 David)
                    if not self._en_voice and ("english" in desc or "en-us" in desc or "zira" in desc or "david" in desc):
                        self._en_voice = v
                except:
                    continue
            
            # 如果没找到特定的，用默认补位
            if not self._en_voice and voices.Count > 0:
                self._en_voice = voices.Item(0)
            
            print(f"[TTS] 中文语音: {self._zh_voice.GetDescription() if self._zh_voice else '未找到'}")
            print(f"[TTS] 英文语音: {self._en_voice.GetDescription() if self._en_voice else '未找到'}")

            while True:
                item = self._q.get()
                if item is None:
                    break
                text, lang = item
                try:
                    # 核心修复：每次朗读前强制切换 Voice 对象
                    if lang == "zh" and self._zh_voice:
                        sapi.Voice = self._zh_voice
                        sapi.Rate = -1 # 中文稍慢一点，自然一些
                    elif self._en_voice:
                        sapi.Voice = self._en_voice
                        sapi.Rate = 0
                    
                    sapi.Speak(text)
                except Exception as e:
                    print(f"[TTS] 朗读失败: {e}")
                finally:
                    self._q.task_done()
        except Exception as e:
            print(f"[TTS] 引擎启动失败: {e}")
        finally:
            pythoncom.CoUninitialize()

    def speak(self, text: str, lang: str = "zh"):
        """朗读文本"""
        # 即时响应：清空队列
        while not self._q.empty():
            try:
                self._q.get_nowait()
                self._q.task_done()
            except Exception:
                break
        self._q.put((str(text), lang))

    def speak_pinyin(self, char: str, pinyin_letters: str):
        """拼音专读：有中文包读汉字声母/韵母，否则拼读字母"""
        if self._zh_voice:
            self.speak(char, "zh")
        else:
            # 比如 "b o"
            self.speak(pinyin_letters, "en")

    def stop(self):
        self._q.put(None)


_engine_instance = None

def get_tts() -> TTSEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = TTSEngine()
    return _engine_instance
