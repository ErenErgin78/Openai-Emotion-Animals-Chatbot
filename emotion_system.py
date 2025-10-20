"""
Duygu Analizi Sistemi
====================

Bu modül duygu analizi, sohbet ve istatistik işlemlerini yönetir.
Ana chatbot sınıfı ve duygu işleme fonksiyonlarını içerir.
"""

import os
import json
import random
import re
import html
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path
from openai import OpenAI

# Güvenlik sabitleri
MAX_EMOTION_MESSAGE_LENGTH = 1000
DANGEROUS_EMOTION_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'data:text/html',
    r'vbscript:',
    r'on\w+\s*=',
    r'<iframe[^>]*>',
    r'<object[^>]*>',
    r'<embed[^>]*>',
]

# Duygu → emoji veri kaynağını yükle (uygulama başında bir kez)
MOOD_EMOJIS: Dict[str, list[str]] = {}
# Kalıcı depolama dosyaları
DATA_DIR = Path(__file__).parent / "data"
CHAT_HISTORY_FILE = DATA_DIR / "chat_history.txt"
MOOD_COUNTER_FILE = DATA_DIR / "mood_counter.txt"

try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data_path = DATA_DIR / "mood_emojis.json"
    if data_path.exists():
        MOOD_EMOJIS = json.loads(data_path.read_text(encoding="utf-8"))
    # Dosyaları oluştur
    if not CHAT_HISTORY_FILE.exists():
        CHAT_HISTORY_FILE.write_text("", encoding="utf-8")
    if not MOOD_COUNTER_FILE.exists():
        MOOD_COUNTER_FILE.write_text("{}", encoding="utf-8")
except Exception:
    MOOD_EMOJIS = {}


class EmotionChatbot:
    def __init__(self, client: OpenAI = None) -> None:
        self.client = client
        self.use_gemini = False
        if client is None:
            self.use_gemini = True
            # Gemini API'yi yapılandır - sadece API key ile
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.messages: list[Dict[str, Any]] = []
        self.stats: Dict[str, Any] = {
            "requests": 0,
            "last_request_at": None,
        }
        self.allowed_moods = [
            "Mutlu", "Üzgün", "Öfkeli", "Şaşkın", "Utangaç",
            "Endişeli", "Yorgun", "Gururlu", "Çaresiz", "Flörtöz"
        ]
        self.emotion_counts: Dict[str, int] = {m: 0 for m in self.allowed_moods}
        # Kalıcı sayaçları yükle
        persisted = self._load_mood_counts()
        if persisted:
            # Sadece bilinen anahtarları al
            for k, v in persisted.items():
                if k in self.emotion_counts and isinstance(v, int):
                    self.emotion_counts[k] = v

    def _sanitize_emotion_input(self, text: str) -> str:
        """Duygu sistemi için güvenli input sanitization"""
        if not text:
            return ""
        
        # HTML escape
        text = html.escape(text, quote=True)
        
        # Tehlikeli pattern'leri kontrol et
        for pattern in DANGEROUS_EMOTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                print(f"[SECURITY] Duygu sisteminde tehlikeli pattern: {pattern}")
                return "[Güvenlik nedeniyle mesaj filtrelendi]"
        
        # Fazla boşlukları temizle
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _validate_emotion_message_length(self, text: str) -> bool:
        """Duygu mesajı uzunluk kontrolü"""
        return len(text) <= MAX_EMOTION_MESSAGE_LENGTH

    def _convert_messages_to_prompt(self, messages: list[Dict[str, Any]]) -> str:
        """OpenAI mesaj formatını Gemini prompt formatına çevirir"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if content:
                if role == "system":
                    prompt_parts.append(f"Sistem: {content}")
                elif role == "user":
                    prompt_parts.append(f"Kullanıcı: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Asistan: {content}")
                elif role == "function":
                    function_name = msg.get("name", "")
                    prompt_parts.append(f"Fonksiyon ({function_name}): {content}")
        return "\n".join(prompt_parts)

    def _load_mood_counts(self) -> Dict[str, int]:
        """Kalıcı duygu sayaçlarını yükler"""
        try:
            raw = MOOD_COUNTER_FILE.read_text(encoding="utf-8").strip() or "{}"
            data = json.loads(raw)
            if isinstance(data, dict):
                return {str(k): int(v) for k, v in data.items()}
        except Exception:
            pass
        return {}

    def _save_mood_counts(self) -> None:
        """Duygu sayaçlarını kalıcı olarak kaydeder"""
        try:
            MOOD_COUNTER_FILE.write_text(
                json.dumps(self.emotion_counts, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _append_chat_history(self, user_message: str, response_text: str) -> None:
        """Konuşma geçmişini dosyaya ekler"""
        try:
            line = json.dumps({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user": user_message,
                "response": response_text
            }, ensure_ascii=False)
            with CHAT_HISTORY_FILE.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def get_functions(self) -> list[Dict[str, Any]]:
        """Emotion sistemi için function-calling kullanılmıyor (istatistik ayrı sistemde)."""
        return []

    # İstatistik fonksiyonları bu sistemden kaldırıldı; StatisticSystem kullanılacak.

    def chat(self, user_message: str) -> Dict[str, Any]:
        """Ana sohbet fonksiyonu - duygu analizi ve yanıt üretir"""
        # Güvenlik kontrolleri
        if not user_message:
            return {"response": "Mesaj boş olamaz"}
        
        # Mesaj uzunluk kontrolü
        if not self._validate_emotion_message_length(user_message):
            return {"response": f"Mesaj çok uzun. Maksimum {MAX_EMOTION_MESSAGE_LENGTH} karakter olabilir."}
        
        # Input sanitization
        user_message = self._sanitize_emotion_input(user_message)
        if user_message == "[Güvenlik nedeniyle mesaj filtrelendi]":
            return {"response": "Güvenlik nedeniyle mesaj filtrelendi"}
        
        self.stats["requests"] += 1
        self.stats["last_request_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ConversationSummaryBufferMemory sistemi kullanılacak - bu kısım kaldırıldı
        # Sadece sistem promptu ve kullanıcı mesajı - memory chain tarafından yönetilecek
        # Önceki konuşma geçmişi ana sistem tarafından ConversationSummaryBufferMemory ile yönetiliyor
        messages_payload: list[Dict[str, Any]] = [{"role": "system", "content": self._get_emotion_system_prompt().strip()}]
        messages_payload.append({"role": "user", "content": user_message})

        # Debug için OpenAI'ye giden tam metni hazırla
        def _messages_to_debug(ms: list[Dict[str, Any]]) -> str:
            parts: list[str] = []
            for m in ms:
                role = m.get("role", "")
                if "content" in m and m["content"] is not None:
                    parts.append(f"{role}: {m['content']}")
                elif "function_call" in m and m["function_call"] is not None:
                    parts.append(f"{role}: [function_call] {m['function_call']}")
                else:
                    parts.append(f"{role}: ")
            return "\n".join(parts)

        request_debug = _messages_to_debug(messages_payload)

        if self.use_gemini:
            # Gemini API kullan - sadece API key ile
            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-2.5-flash')
            # Gemini için mesajları düz metne çevir
            prompt_text = self._convert_messages_to_prompt(messages_payload)
            response = model.generate_content(prompt_text)
            # Gemini response'unu OpenAI formatına çevir
            completion = type('obj', (object,), {
                'choices': [type('obj', (object,), {
                    'message': type('obj', (object,), {
                        'content': response.text,
                        'function_call': None
                    })()
                })()]
            })()
        else:
            # OpenAI API kullan
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages_payload,
                functions=self.get_functions(),
                function_call="auto",
                temperature=0.2,
            )

        msg = completion.choices[0].message

        # Emotion sistemi function-calling kullanmaz; istatistikler ayrı sistemdedir.

        # Aksi halde modelden JSON veya fonksiyon benzeri metin bekliyoruz
        content = msg.content or ""

        # İstatistik düz metin yakalama kaldırıldı; STATS akışına devredildi.

        def extract_json_object(text: str) -> Dict[str, Any] | None:
            # code fence temizle
            t = text.replace("```json", "").replace("```", "").strip()
            # İlk dengeli JSON objesini çıkar (kaçışlı stringleri hesaba kat)
            start = t.find('{')
            if start == -1:
                return None
            depth = 0
            in_string = False
            escape = False
            end_index = -1
            for i in range(start, len(t)):
                ch = t[i]
                if in_string:
                    if escape:
                        escape = False
                    elif ch == '\\':
                        escape = True
                    elif ch == '"':
                        in_string = False
                else:
                    if ch == '"':
                        in_string = True
                    elif ch == '{':
                        depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0:
                            end_index = i
                            break
            if end_index == -1:
                return None
            candidate = t[start:end_index + 1]
            try:
                return json.loads(candidate)
            except Exception:
                return None

        data = extract_json_object(content)
        if not data:
            # Ham chat'i kaydet
            self._append_chat_history(user_message, content)
            # Geçmişe ekle
            self.messages.append({"role": "user", "content": user_message})
            self.messages.append({"role": "assistant", "content": content})
            return {"response": content, "request_debug": request_debug}

        required_keys = {"kullanici_ruh_hali", "ilk_ruh_hali", "ilk_cevap", "ikinci_ruh_hali", "ikinci_cevap"}
        missing = [k for k in required_keys if k not in data]
        if missing:
            # Ham chat'i kaydet
            self._append_chat_history(user_message, content)
            return {"response": content}

        # Duygu sayaçlarını güncelle
        def inc(mood: str) -> None:
            key = (mood or "").strip()
            if key in self.emotion_counts:
                self.emotion_counts[key] += 1

        user_mood_raw = str(data.get("kullanici_ruh_hali", ""))
        first_mood_raw = str(data.get("ilk_ruh_hali", ""))
        second_mood_raw = str(data.get("ikinci_ruh_hali", ""))

        inc(user_mood_raw)
        inc(first_mood_raw)
        inc(second_mood_raw)
        # Sayaçları kalıcı kaydet
        self._save_mood_counts()

        # Emoji seçim: mood_emojis.json'dan duyguya göre rastgele
        def normalize_mood(name: str) -> str:
            n = name.strip().lower()
            mapping = {
                "utangaç": "Utanmış",
                "utanmış": "Utanmış",
                "gülümseyen": "Gülümseyen",
                "mutlu": "Mutlu",
                "üzgün": "Üzgün",
                "öfkeli": "Öfkeli",
                "şaşkın": "Şaşkın",
                "endişeli": "Endişeli",
                "flörtöz": "Flörtöz",
                "sorgulayıcı": "Sorgulayıcı",
                "yorgun": "Yorgun",
            }
            return mapping.get(n, name)

        def pick_emoji(mood: str) -> Optional[str]:
            key = normalize_mood(mood)
            options = MOOD_EMOJIS.get(key)
            if options:
                try:
                    return random.choice(options)
                except Exception:
                    return None
            return None

        first_emoji = pick_emoji(first_mood_raw)
        second_emoji = pick_emoji(second_mood_raw)

        response_text = json.dumps(data, ensure_ascii=False)
        # Ham chat'i kaydet
        self._append_chat_history(user_message, response_text)
        # Geçmişe ekle
        self.messages.append({"role": "user", "content": user_message})
        self.messages.append({"role": "assistant", "content": response_text})

        return {
            "response": response_text,
            "first_emoji": first_emoji,
            "second_emoji": second_emoji,
            "request_debug": request_debug,
        }

    def _get_emotion_system_prompt(self) -> str:
        """Duygu analizi için sistem prompt'unu döndürür"""
        return """
Sen bir duygu sınıflandırma ve yanıt üretme modelisin.
Görevin şunlardır:

1. Kullanıcının mesajındaki duyguyu tahmin et.
2. O duyguya uygun bir ilk cevap yaz.
3. Ardından ilk duygu ile uyumlu bir ikinci duygu seç; gerekirse aynı duyguyu tekrar seçebilirsin.
4. Seçilen ikinci duyguya uygun bir ikinci cevap yaz (ilk yanıtla tutarlı olmalıdır).
5. Çıktıyı Türkçe ver ve her iki yanıt da sadece 1 cümle olmalıdır.
6. Ek olarak, kullanıcının verdiği mesajdan kullanıcının duygu durumunu tek bir etiket ile belirle.
6. Çıktıyı her zaman aşağıdaki JSON formatında ver:

{
  "kullanici_ruh_hali": "...",
  "ilk_ruh_hali": "...",
  "ilk_cevap": "...",
  "ikinci_ruh_hali": "...",
  "ikinci_cevap": "..."
}

Seçilebilecek ruh halleri:
Mutlu, Üzgün, Öfkeli, Şaşkın, Utanmış, Endişeli, Gülümseyen, Flörtöz, Sorgulayıcı, Sorgulayıcı, Yorgun

EK KURALLAR (İstatistik Sorguları):
- Sadece kullanıcı AÇIKÇA istatistik/özet isterse sınıflandırma JSON'u üretmek yerine şu fonksiyonu çağır: `get_emotion_stats`.
  - Açıkça istatistik/özet isteme anahtar kelimeleri: "en çok", "istatistik", "özet", "toplam", "kaç kez", "kaç kere", "en sık".
  - Normal duygu/sohbet mesajlarında ASLA fonksiyon çağırma.
  - `period` argümanı: İstatistik sorgusunda "bugün"/"günlük" geçiyorsa "today"; aksi halde "all".
- Fonksiyonun dönüşünden sonra sadece 1 cümlelik, Türkçe, kısa bir özet yaz ve JSON döndürme. Bu kural YALNIZCA istatistik sorguları için geçerlidir.
"""
