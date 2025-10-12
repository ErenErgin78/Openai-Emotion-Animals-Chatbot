"""
Hayvan API Sistemi
=================

Bu modül hayvan fotoğraf ve bilgi API'lerini yönetir.
Köpek, kedi, tilki, ördek için fotoğraf ve bilgi isteklerini işler.
"""

import httpx
import re
import html
from typing import Dict, Any

# Güvenlik sabitleri
MAX_ANIMAL_MESSAGE_LENGTH = 500
DANGEROUS_ANIMAL_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'data:text/html',
    r'vbscript:',
    r'on\w+\s*=',
    r'<iframe[^>]*>',
    r'<object[^>]*>',
    r'<embed[^>]*>',
]

ANIMAL_FUNCTIONS_SPEC = [
    {
        "name": "dog_photo",
        "description": "Rastgele bir köpek fotoğrafı döndür",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "dog_facts",
        "description": "Rastgele bir köpek bilgisi döndür",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "cat_facts",
        "description": "Rastgele bir kedi bilgisi döndür",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "cat_photo",
        "description": "Rastgele bir kedi fotoğrafı döndür",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "fox_photo",
        "description": "Rastgele bir tilki fotoğrafı döndür",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "duck_photo",
        "description": "Rastgele bir ördek fotoğrafı döndür",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
]

ANIMAL_SYSTEM_PROMPT = (
    "Kullanıcının niyetini tespit et ve sadece açık HAYVAN isteği varsa uygun hayvan fonksiyonunu çağır. "
    "Seçenekler: dog_photo, dog_facts, cat_facts, cat_photo, fox_photo, duck_photo. "
    "Mesajda 'köpek/dog', 'kedi/cat', 'tilki/fox', 'ördek/duck' anahtar kelimeleri YOKSA kesinlikle fonksiyon çağırma. "
    "PDF, ders, kitap, teori, Python, Anayasa, Clean Architecture gibi bilgi taleplerinde fonksiyon çağırma. "
    "Net hayvan isteği yoksa FONKSİYON ÇAĞIRMA ve normal akışa bırak."
)


def _sanitize_animal_input(text: str) -> str:
    """Hayvan sistemi için güvenli input sanitization"""
    if not text:
        return ""
    
    # HTML escape
    text = html.escape(text, quote=True)
    
    # Tehlikeli pattern'leri kontrol et
    for pattern in DANGEROUS_ANIMAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            print(f"[SECURITY] Hayvan sisteminde tehlikeli pattern: {pattern}")
            return "[Güvenlik nedeniyle mesaj filtrelendi]"
    
    # Fazla boşlukları temizle
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def _validate_animal_message_length(text: str) -> bool:
    """Hayvan mesajı uzunluk kontrolü"""
    return len(text) <= MAX_ANIMAL_MESSAGE_LENGTH

def _http_get_json(url: str) -> dict:
    """HTTP GET isteği yapar ve JSON döndürür"""
    with httpx.Client(timeout=15.0, follow_redirects=True) as s:
        r = s.get(url)
        r.raise_for_status()
        return r.json()


def _animal_emoji(animal: str) -> str:
    """Hayvan türüne göre emoji döndürür"""
    mapping = {
        "dog": "🐶",
        "cat": "🐱",
        "fox": "🦊",
        "duck": "🦆",
    }
    return mapping.get(animal, "🙂")


def _is_image_url(url: str) -> bool:
    """URL'nin resim dosyası olup olmadığını kontrol eder"""
    if not url:
        return False
    url_l = url.lower()
    for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        if url_l.endswith(ext):
            return True
    return False


def dog_photo() -> dict:
    """Köpek fotoğrafı getirir"""
    # random.dog zaman zaman video döndürdüğü için birkaç deneme yap
    image_url = ""
    for _ in range(6):
        data = _http_get_json("https://random.dog/woof.json")
        candidate = str(data.get("url", "")).strip()
        if _is_image_url(candidate):
            image_url = candidate
            break
    # Son çare: image değilse yine candidate'i döndürme; yardım mesajı ver
    if not image_url:
        # Alternatif statik bir köpek resmi verilebilir; burada metin döndürelim
        return {"type": "text", "animal": "dog", "text": "Şu an uygun köpek fotoğrafı bulunamadı, tekrar dener misin?"}
    return {"type": "image", "animal": "dog", "image_url": image_url}


def dog_facts() -> dict:
    """Köpek bilgisi getirir"""
    data = _http_get_json("https://dogapi.dog/api/v2/facts?limit=1")
    fact = ""
    try:
        arr = data.get("data") or []
        if arr and isinstance(arr, list):
            attributes = (arr[0] or {}).get("attributes", {})
            fact = str(attributes.get("body", "")).strip()
    except Exception:
        fact = ""
    return {"type": "text", "animal": "dog", "text": fact}


def cat_facts() -> dict:
    """Kedi bilgisi getirir"""
    data = _http_get_json("https://meowfacts.herokuapp.com/")
    fact = ""
    try:
        arr = data.get("data") or []
        if arr and isinstance(arr, list):
            fact = str(arr[0]).strip()
    except Exception:
        fact = ""
    return {"type": "text", "animal": "cat", "text": fact}


def cat_photo() -> dict:
    """Kedi fotoğrafı getirir"""
    data = _http_get_json("https://api.thecatapi.com/v1/images/search")
    url = ""
    try:
        if isinstance(data, list) and data:
            url = str((data[0] or {}).get("url", "")).strip()
    except Exception:
        url = ""
    return {"type": "image", "animal": "cat", "image_url": url}


def fox_photo() -> dict:
    """Tilki fotoğrafı getirir"""
    data = _http_get_json("https://randomfox.ca/floof/")
    return {"type": "image", "animal": "fox", "image_url": str(data.get("image", "")).strip()}


def duck_photo() -> dict:
    """Ördek fotoğrafı getirir"""
    data = _http_get_json("https://random-d.uk/api/v2/random")
    return {"type": "image", "animal": "duck", "image_url": str(data.get("url", "")).strip()}


def _animal_keyword_router(text: str) -> dict | None:
    """Anahtar kelime tabanlı hayvan yönlendirmesi (fallback)"""
    t = text.lower()
    if ("köpek" in t or "dog" in t) and ("foto" in t or "resim" in t or "image" in t or "photo" in t):
        return dog_photo()
    if ("köpek" in t or "dog" in t) and ("fact" in t or "bilgi" in t):
        return dog_facts()
    if ("kedi" in t or "cat" in t) and ("fact" in t or "bilgi" in t):
        return cat_facts()
    if ("kedi" in t or "cat" in t) and ("foto" in t or "resim" in t or "image" in t or "photo" in t):
        return cat_photo()
    if ("tilki" in t or "fox" in t) and ("foto" in t or "resim" in t or "image" in t or "photo" in t):
        return fox_photo()
    if ("ördek" in t or "duck" in t) and ("foto" in t or "resim" in t or "image" in t or "photo" in t):
        return duck_photo()
    return None


def route_animals(user_message: str, client) -> dict | None:
    """Ana hayvan yönlendirme fonksiyonu - function calling + fallback"""
    # Güvenlik kontrolleri
    if not user_message:
        return None
    
    # Mesaj uzunluk kontrolü
    if not _validate_animal_message_length(user_message):
        return {"type": "text", "animal": "error", "text": f"Mesaj çok uzun. Maksimum {MAX_ANIMAL_MESSAGE_LENGTH} karakter olabilir."}
    
    # Input sanitization
    user_message = _sanitize_animal_input(user_message)
    if user_message == "[Güvenlik nedeniyle mesaj filtrelendi]":
        return {"type": "text", "animal": "error", "text": "Güvenlik nedeniyle mesaj filtrelendi"}
    
    # Ön filtre: mesajda hayvan anahtar kelimesi yoksa hiç deneme
    tl = user_message.lower()
    if not ("köpek" in tl or "dog" in tl or "kedi" in tl or "cat" in tl or "tilki" in tl or "fox" in tl or "ördek" in tl or "duck" in tl):
        return None
    # OpenAI modeli ile fonksiyon çağırma dene; olmazsa anahtar kelimeye düş
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": ANIMAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            functions=ANIMAL_FUNCTIONS_SPEC,
            function_call="auto",
            temperature=0.0,
        )
        msg = completion.choices[0].message
        fn_name = getattr(getattr(msg, "function_call", None), "name", None)
        if not fn_name:
            return None
        mapping = {
            "dog_photo": dog_photo,
            "dog_facts": dog_facts,
            "cat_facts": cat_facts,
            "cat_photo": cat_photo,
            "fox_photo": fox_photo,
            "duck_photo": duck_photo,
        }
        func = mapping.get(fn_name)
        return func() if func else None
    except Exception:
        return _animal_keyword_router(user_message)
