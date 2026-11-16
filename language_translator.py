import ctypes
import os
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from deep_translator import GoogleTranslator, MyMemoryTranslator
from gtts import gTTS

LANGUAGES = {
    "English": ("en", "en-US"),
    "Telugu": ("te", "te-IN"),
    "Hindi": ("hi", "hi-IN"),
    "Tamil": ("ta", "ta-IN"),
    "Kannada": ("kn", "kn-IN"),
    "Malayalam": ("ml", "ml-IN"),
    "Marathi": ("mr", "mr-IN"),
    "Bengali": ("bn", "bn-IN"),
    "Gujarati": ("gu", "gu-IN"),
    "Spanish": ("es", "es-ES"),
    "French": ("fr", "fr-FR"),
    "German": ("de", "de-DE"),
    "Japanese": ("ja", "ja-JP"),
    "Korean": ("ko", "ko-KR"),
    "Arabic": ("ar", "ar-SA"),
    "Russian": ("ru", "ru-RU"),
}


class LanguageTranslationApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CodeAlpha - AI Language Translation Tool")
        self.root.geometry("680x580")
        self.root.configure(bg="#11111b")
        self.root.resizable(False, False)

        self.is_speaking = False
        self._build_ui()

    def _build_ui(self):
        # Header
        tk.Label(
            self.root,
            text="🌐 AI Language Translator",
            font=("Segoe UI", 18, "bold"),
            bg="#11111b",
            fg="#89b4fa",
        ).pack(pady=(16, 10))

        # Language Selector Bar
        lang_frame = tk.Frame(self.root, bg="#11111b")
        lang_frame.pack(pady=5)

        lang_list = list(LANGUAGES.keys())

        self.src_combo = ttk.Combobox(
            lang_frame, values=lang_list, width=18, state="readonly", font=("Segoe UI", 11)
        )
        self.src_combo.set("English")
        self.src_combo.grid(row=0, column=0, padx=8)

        swap_btn = tk.Button(
            lang_frame,
            text="⇄",
            font=("Segoe UI", 13, "bold"),
            bg="#313244",
            fg="#cdd6f4",
            activebackground="#45475a",
            activeforeground="white",
            bd=0,
            padx=12,
            pady=2,
            cursor="hand2",
            command=self.swap_languages,
        )
        swap_btn.grid(row=0, column=1, padx=8)

        self.dest_combo = ttk.Combobox(
            lang_frame, values=lang_list, width=18, state="readonly", font=("Segoe UI", 11)
        )
        self.dest_combo.set("Telugu")
        self.dest_combo.grid(row=0, column=2, padx=8)

        # --- TOP BOX: INPUT TEXT ---
        tk.Label(
            self.root,
            text="Enter Text to Translate:",
            font=("Segoe UI", 10, "bold"),
            bg="#11111b",
            fg="#cdd6f4",
        ).pack(anchor="w", padx=35, pady=(12, 4))

        self.input_text = tk.Text(
            self.root,
            height=5,
            width=68,
            font=("Segoe UI", 11),
            bg="#ffffff",
            fg="#11111b",
            relief="flat",
            padx=10,
            pady=8,
            wrap="word",
        )
        self.input_text.pack(padx=35)
        self.input_text.insert("1.0", "Hello! How are you doing today?")

        # --- ACTION BUTTONS ---
        btn_frame = tk.Frame(self.root, bg="#11111b")
        btn_frame.pack(pady=14)

        self.translate_btn = tk.Button(
            btn_frame,
            text="⚡ Translate",
            font=("Segoe UI", 10, "bold"),
            bg="#a6e3a1",
            fg="#11111b",
            width=14,
            pady=7,
            bd=0,
            cursor="hand2",
            command=self.trigger_translation,
        )
        self.translate_btn.grid(row=0, column=0, padx=6)

        self.speak_btn = tk.Button(
            btn_frame,
            text="🔊 Speak Output",
            font=("Segoe UI", 10, "bold"),
            bg="#f9e2af",
            fg="#11111b",
            width=15,
            pady=7,
            bd=0,
            cursor="hand2",
            command=self.trigger_speech,
        )
        self.speak_btn.grid(row=0, column=1, padx=6)

        self.copy_btn = tk.Button(
            btn_frame,
            text="📋 Copy Output",
            font=("Segoe UI", 10, "bold"),
            bg="#89b4fa",
            fg="#11111b",
            width=14,
            pady=7,
            bd=0,
            cursor="hand2",
            command=self.copy_output,
        )
        self.copy_btn.grid(row=0, column=2, padx=6)

        self.clear_btn = tk.Button(
            btn_frame,
            text="✖ Clear",
            font=("Segoe UI", 10, "bold"),
            bg="#f38ba8",
            fg="#11111b",
            width=10,
            pady=7,
            bd=0,
            cursor="hand2",
            command=self.clear_all,
        )
        self.clear_btn.grid(row=0, column=3, padx=6)

        # --- BOTTOM BOX: TRANSLATED OUTPUT ---
        tk.Label(
            self.root,
            text="Translated Output:",
            font=("Segoe UI", 10, "bold"),
            bg="#11111b",
            fg="#a6e3a1",
        ).pack(anchor="w", padx=35, pady=(2, 4))

        self.output_text = tk.Text(
            self.root,
            height=5,
            width=68,
            font=("Segoe UI", 11),
            bg="#ffffff",
            fg="#11111b",
            relief="flat",
            padx=10,
            pady=8,
            wrap="word",
            state="disabled",
        )
        self.output_text.pack(padx=35)

        # Status Bar
        self.status_var = tk.StringVar(value="● Ready")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg="#181825",
            fg="#a6adc8",
            anchor="w",
            padx=15,
            pady=5,
        ).pack(fill="x", side="bottom")

    def swap_languages(self):
        src = self.src_combo.get()
        dest = self.dest_combo.get()
        self.src_combo.set(dest)
        self.dest_combo.set(src)

        in_txt = self.input_text.get("1.0", tk.END).strip()
        out_txt = self._get_output_text()
        if out_txt:
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", out_txt)
            self._set_output_text(in_txt)

    def _get_output_text(self) -> str:
        self.output_text.config(state="normal")
        text = self.output_text.get("1.0", tk.END).strip()
        self.output_text.config(state="disabled")
        return text

    def _set_output_text(self, text: str):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        self.output_text.config(state="disabled")

    def trigger_translation(self):
        raw_text = self.input_text.get("1.0", tk.END).strip()
        if not raw_text:
            messagebox.showwarning("Empty Input", "Please enter text to translate.")
            return

        src_lang = self.src_combo.get()
        dest_lang = self.dest_combo.get()

        self.translate_btn.config(state="disabled", text="Translating...")
        self.status_var.set(f"⏳ Translating {src_lang} → {dest_lang}...")
        threading.Thread(
            target=self._translate_worker, args=(raw_text, src_lang, dest_lang), daemon=True
        ).start()

    def _translate_worker(self, text: str, src_lang: str, dest_lang: str):
        iso_src, mm_src = LANGUAGES[src_lang]
        iso_dest, mm_dest = LANGUAGES[dest_lang]

        try:
            res = GoogleTranslator(source=iso_src, target=iso_dest).translate(text)
            if res:
                self.root.after(0, self._on_translate_success, res, "Google Translate")
                return
        except Exception:
            pass

        try:
            res = MyMemoryTranslator(source=mm_src, target=mm_dest).translate(text)
            if res:
                self.root.after(0, self._on_translate_success, res, "MyMemory Engine")
                return
        except Exception:
            pass

        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {"client": "gtx", "sl": iso_src, "tl": iso_dest, "dt": "t", "q": text}
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, params=params, headers=headers, timeout=8)
            resp.raise_for_status()
            res = "".join([chunk[0] for chunk in resp.json()[0] if chunk[0]])
            if res:
                self.root.after(0, self._on_translate_success, res, "Google Cloud API")
                return
        except Exception as err:
            self.root.after(0, self._on_translate_error, str(err))

    def _on_translate_success(self, translated: str, provider: str):
        self._set_output_text(translated)
        self.translate_btn.config(state="normal", text="⚡ Translate")
        self.status_var.set(f"✅ Translated via {provider}")

    def _on_translate_error(self, err_msg: str):
        self.translate_btn.config(state="normal", text="⚡ Translate")
        self.status_var.set("❌ Translation failed")
        messagebox.showerror("Translation Error", f"Could not translate:\n{err_msg}")

    def trigger_speech(self):
        text = self._get_output_text()
        if not text:
            messagebox.showinfo("No Output", "Translate some text first.")
            return
        if self.is_speaking:
            return

        dest_lang = self.dest_combo.get()
        iso_code = LANGUAGES[dest_lang][0]

        self.is_speaking = True
        self.speak_btn.config(state="disabled", text="🔊 Speaking...")
        self.status_var.set(f"🎙️ Playing {dest_lang} voice...")
        threading.Thread(target=self._speech_worker, args=(text, iso_code, dest_lang), daemon=True).start()

    def _speech_worker(self, text: str, lang_code: str, lang_name: str):
        try:
            tts = gTTS(text=text, lang=lang_code, slow=False)
            tmp_file = os.path.join(tempfile.gettempdir(), "codealpha_tts.mp3")
            tts.save(tmp_file)

            mci = ctypes.windll.winmm.mciSendStringW
            alias = "codealpha_voice"
            mci(f"close {alias}", None, 0, None)
            mci(f'open "{tmp_file}" type mpegvideo alias {alias}', None, 0, None)
            mci(f"play {alias} wait", None, 0, None)
            mci(f"close {alias}", None, 0, None)

            self.root.after(0, self._on_speech_done, f"✅ Finished speaking {lang_name}")
        except Exception as err:
            self.root.after(0, self._on_speech_done, f"❌ Speech error: {err}")

    def _on_speech_done(self, status_msg: str):
        self.is_speaking = False
        self.speak_btn.config(state="normal", text="🔊 Speak Output")
        self.status_var.set(status_msg)

    def copy_output(self):
        text = self._get_output_text()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_var.set("📋 Copied to clipboard!")
        else:
            messagebox.showinfo("Empty", "Nothing to copy yet.")

    def clear_all(self):
        self.input_text.delete("1.0", tk.END)
        self._set_output_text("")
        self.status_var.set("● Cleared")


if __name__ == "__main__":
    root = tk.Tk()
    app = LanguageTranslationApp(root)
    root.mainloop()