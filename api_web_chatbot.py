"""
Ana Chatbot Sistemi
==================

Bu dosya tüm sistemleri koordine eden ana yönlendirme sistemidir.
- LLM ile akış yönlendirmesi
- RAG, Animal, Emotion sistemlerini çağırma
- Web arayüzü yönetimi
"""

import os
import re
import html
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Sistem modüllerini import et
from emotion_system import EmotionChatbot
from animal_system import route_animals, _animal_emoji
from rag_service import rag_service

load_dotenv()

app = FastAPI(title="Akıllı Chatbot Sistemi", version="2.0.0")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Global chatbot instance
chatbot_instance: EmotionChatbot | None = None

# RAG modelini asenkron olarak önceden yükle
print("[STARTUP] RAG modeli asenkron olarak yükleniyor...")
rag_service.preload_model_async()

# Güvenlik sabitleri
MAX_MESSAGE_LENGTH = 2000  # Maksimum mesaj uzunluğu
MAX_TOKENS_PER_REQUEST = 1000  # Maksimum token sayısı
DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # Script injection
    r'javascript:',  # JavaScript URL
    r'data:text/html',  # Data URL
    r'vbscript:',  # VBScript
    r'on\w+\s*=',  # Event handlers
    r'<iframe[^>]*>',  # Iframe injection
    r'<object[^>]*>',  # Object injection
    r'<embed[^>]*>',  # Embed injection
    r'<link[^>]*>',  # Link injection
    r'<meta[^>]*>',  # Meta injection
]

# RAG kaynakları
RAG_SOURCES = {
    "Learning_Python.pdf": {"id": "pdf-python", "emoji": "🐍", "alias": "python"},
    "gerekceli_anayasa.pdf": {"id": "pdf-anayasa", "emoji": "⚖️", "alias": "anayasa"},
    "clean_architecture.pdf": {"id": "pdf-clean", "emoji": "🏗️", "alias": "clean"},
}

# Static files (CSS/JS)
STATIC_DIR = Path(__file__).parent / "static"
try:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _sanitize_input(text: str) -> str:
    """Güvenli input sanitization - injection saldırılarını önler"""
    if not text:
        return ""
    
    # HTML escape
    text = html.escape(text, quote=True)
    
    # Tehlikeli pattern'leri kontrol et
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            print(f"[SECURITY] Tehlikeli pattern tespit edildi: {pattern}")
            return "[Güvenlik nedeniyle mesaj filtrelendi]"
    
    # Fazla boşlukları temizle
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def _validate_message_length(text: str) -> bool:
    """Mesaj uzunluğunu kontrol eder"""
    return len(text) <= MAX_MESSAGE_LENGTH


def _estimate_tokens(text: str) -> int:
    """Yaklaşık token sayısını hesaplar (Türkçe için)"""
    # Türkçe için yaklaşık hesaplama: 1 token ≈ 4 karakter
    return len(text) // 4


def _get_flow_decision(user_message: str) -> str:
    """LLM ile akış yönlendirmesi yapar (ANIMAL/RAG/EMOTION)"""
    try:
        # Token kontrolü
        estimated_tokens = _estimate_tokens(user_message)
        if estimated_tokens > MAX_TOKENS_PER_REQUEST:
            print(f"[SECURITY] Çok fazla token: {estimated_tokens}")
            return "EMOTION"  # Güvenli fallback
        
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Kullanıcının mesajını analiz et ve şu akışlardan birini seç:

ÖNEMLİ KURALLAR:
1. Eğer kullanıcı BİLGİ istiyorsa (nedir, nasıl, açıkla, tanım, principle, concept, theory) → RAG
2. Eğer kullanıcı HAYVAN istiyorsa (köpek, kedi, tilki, ördek fotoğraf/bilgi) → ANIMAL  
3. Eğer kullanıcı SOHBET/DUYGU istiyorsa (merhaba, nasılsın, üzgünüm, mutluyum) → EMOTION

Akışlar:
- ANIMAL: Köpek, kedi, tilki, ördek fotoğraf/bilgi isteği
- RAG: Python, Anayasa, Clean Architecture, teknik terimler, bilgi soruları, "nedir", "nasıl", "açıkla", "tanım", "principle", "concept"
- EMOTION: Duygu analizi, sohbet, normal konuşma

Sadece şu yanıtlardan birini ver: ANIMAL, RAG, EMOTION"""},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1,
            max_tokens=15
        )
        flow_decision = completion.choices[0].message.content or ""
        return flow_decision.strip()
    except Exception as e:
        print(f"[FLOW] LLM yönlendirme hatası: {e}")
        return "EMOTION"  # Varsayılan


def _process_rag_flow(user_message: str) -> Dict[str, Any] | None:
    """RAG akışını işler - PDF'lerden bilgi çeker"""
    t = user_message.lower()
    # Heuristic: explicit source keywords
    if "anayasa" in t:
        source = "gerekceli_anayasa.pdf"
    elif ("clean architecture" in t or "clean architecture".replace(" ", "_") in t or 
          ("clean" in t and "architecture" in t) or "acyclic" in t or "dependency" in t or 
          "principle" in t or "principles" in t or "dependencies" in t):
        source = "clean_architecture.pdf"
    elif "python" in t:
        source = "Learning_Python.pdf"
    else:
        # If generic question, try general retrieval (no source filter)
        keywords = ["pdf", "belge", "doküman", "özetle", "açıkla", "nedir", "nasıl", "anlat", "tanım"]
        if not any(k in t for k in keywords):
            return None
        chunks = rag_service.retrieve_top(user_message, top_k=4)
        if not chunks:
            return None
        context = "\n\n".join([c.get("text", "") for c in chunks])
        sources = list({(c.get("metadata", {}) or {}).get("source", "?") for c in chunks})
        prompt = f"BAĞLAM:\n{context}\n\nSORU: {user_message}\nYANIT:"

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sen bir bilgi asistanısın. Kullanıcının sorularını verilen bağlam bilgilerini kullanarak yanıtla. Türkçe, kısa ve net yanıtlar ver. Bağlam bilgisini kullan ama gereksiz detay verme. Eğer bağlamda yeterli bilgi yoksa bunu belirt. Yanıtını doğrudan metin olarak ver (JSON formatında değil). Maksimum 5 cümle ile yanıtla. Özellikle Clean Architecture, Python, Anayasa konularında uzmanlaşmışsın."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        answer = completion.choices[0].message.content or ""
        # Pick first known source for UI hint
        lit = None
        for s in sources:
            if s in RAG_SOURCES:
                lit = s
                break
        ui = RAG_SOURCES.get(lit or "", None)
        return {
            "rag": True,
            "response": answer,
            "rag_source": ui.get("id") if ui else None,
            "rag_emoji": ui.get("emoji") if ui else None,
        }

    # Source-filtered retrieval
    chunks = rag_service.retrieve_by_source(user_message, source_filename=source, top_k=4)
    if not chunks:
        return None
    context = "\n\n".join([c.get("text", "") for c in chunks])
    prompt = f"BAĞLAM:\n{context}\n\nSORU: {user_message}\nYANIT:"
    
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Sen bir bilgi asistanısın. Kullanıcının sorularını verilen bağlam bilgilerini kullanarak yanıtla. Türkçe, kısa ve net yanıtlar ver. Bağlam bilgisini kullan ama gereksiz detay verme. Eğer bağlamda yeterli bilgi yoksa bunu belirt. Yanıtını doğrudan metin olarak ver (JSON formatında değil). Maksimum 5 cümle ile yanıtla. Özellikle Clean Architecture, Python, Anayasa konularında uzmanlaşmışsın."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    answer = completion.choices[0].message.content or ""
    ui = RAG_SOURCES.get(source)
    return {
        "rag": True,
        "response": answer,
        "rag_source": ui.get("id"),
        "rag_emoji": ui.get("emoji"),
    }


def _process_animal_flow(user_message: str) -> Dict[str, Any] | None:
    """Hayvan akışını işler - fotoğraf/bilgi getirir"""
    animal_result = route_animals(user_message, client)
    if animal_result:
        animal = str(animal_result.get("animal", ""))
        out: Dict[str, Any] = {
            "animal": animal,
            "type": animal_result.get("type"),
            "animal_emoji": _animal_emoji(animal),
        }
        if animal_result.get("type") == "image":
            out["image_url"] = animal_result.get("image_url")
            out["response"] = f"{_animal_emoji(animal)} {animal.capitalize()} fotoğrafı hazır."
        else:
            out["response"] = animal_result.get("text", "")
        return out
    return None


def _process_emotion_flow(user_message: str) -> Dict[str, Any]:
    """Duygu akışını işler - duygu analizi ve sohbet"""
    global chatbot_instance
    if chatbot_instance is None:
        chatbot_instance = EmotionChatbot(client)
    
    result = chatbot_instance.chat(user_message)
    stats = {
        "requests": chatbot_instance.stats["requests"],
        "last_request_at": chatbot_instance.stats["last_request_at"],
    }
    # result: { response: str, first_emoji?: str, second_emoji?: str, request_debug?: str }
    out = {"response": result.get("response", ""), "stats": stats}
    if "first_emoji" in result:
        out["first_emoji"] = result["first_emoji"]
    if "second_emoji" in result:
        out["second_emoji"] = result["second_emoji"]
    if "request_debug" in result:
        out["request_debug"] = result["request_debug"]
    return out


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    """Ana sayfa HTML'ini döndürür"""
    template_path = Path(__file__).parent / "templates" / "index.html"
    try:
        html = template_path.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HTML yüklenemedi: {e}")
    return HTMLResponse(content=html)


@app.post("/chat")
def chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Ana chat endpoint'i - akış yönlendirmesi yapar"""
    user_message = str(payload.get("message", "")).strip()
    
    # Güvenlik kontrolleri
    if not user_message:
        return {"error": "Mesaj boş olamaz"}
    
    # Mesaj uzunluk kontrolü
    if not _validate_message_length(user_message):
        return {"error": f"Mesaj çok uzun. Maksimum {MAX_MESSAGE_LENGTH} karakter olabilir."}
    
    # Input sanitization
    user_message = _sanitize_input(user_message)
    if user_message == "[Güvenlik nedeniyle mesaj filtrelendi]":
        return {"error": "Güvenlik nedeniyle mesaj filtrelendi"}
    
    # Token kontrolü
    estimated_tokens = _estimate_tokens(user_message)
    if estimated_tokens > MAX_TOKENS_PER_REQUEST:
        return {"error": f"Çok fazla token. Maksimum {MAX_TOKENS_PER_REQUEST} token olabilir."}

    try:
        # AŞAMA 1: LLM ile akış yönlendirmesi
        print("[FLOW] AŞAMA 1: LLM akış yönlendirmesi başlıyor...")
        flow_decision = _get_flow_decision(user_message)
        print(f"[FLOW] LLM akış kararı: {flow_decision}")

        # AŞAMA 2: Seçilen akışa göre işleme
        if flow_decision == "RAG":
            print("[FLOW] AŞAMA 2: RAG akışı çalışıyor...")
            result = _process_rag_flow(user_message)
            if result:
                return result
        elif flow_decision == "ANIMAL":
            print("[FLOW] AŞAMA 2: Hayvan akışı çalışıyor...")
            result = _process_animal_flow(user_message)
            if result:
                return result
        elif flow_decision == "EMOTION":
            print("[FLOW] AŞAMA 2: Duygu akışı çalışıyor...")
            result = _process_emotion_flow(user_message)
            if result:
                return result
        
        # Fallback: Varsayılan duygu akışı
        print("[FLOW] Fallback: Duygu akışı çalışıyor...")
        result = _process_emotion_flow(user_message)
        return result

    except HTTPException as e:
        return {"error": e.detail}
    except Exception as e:
        return {"error": str(e)}


# Çalıştırma:
# uvicorn api_web_chatbot:app --host 0.0.0.0 --port 8000 --reload
