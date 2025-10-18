"""
CHAIN SYSTEM - Ana Chatbot Sistemi
==================================

Bu dosya LangChain chain yapısı ile tüm sistemleri koordine eder.
- Chain-based akış yönlendirmesi
- RAG, Animal, Emotion sistemlerini chain olarak çağırma
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

# LangChain imports
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain.schema import BaseOutputParser

# Sistem modüllerini import et
from emotion_system import EmotionChatbot
from animal_system import route_animals, _animal_emoji
from rag_service import rag_service

load_dotenv()

app = FastAPI(title="CHAIN SYSTEM - Akıllı Chatbot Sistemi", version="3.0.0")

# LangChain LLM instance
llm = OpenAI(temperature=0.1, max_tokens=1000, request_timeout=15)

# Global chatbot instance
chatbot_instance: EmotionChatbot | None = None

# RAG modelini asenkron olarak önceden yükle
print("[CHAIN SYSTEM] RAG modeli asenkron olarak yükleniyor...")
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


class FlowDecisionParser(BaseOutputParser):
    """Akış kararı parser'ı - LLM çıktısını temizler"""
    
    def parse(self, text: str) -> str:
        """LLM çıktısını temizleyip akış kararını döndürür"""
        text = text.strip().upper()
        valid_flows = ["ANIMAL", "RAG", "EMOTION"]
        
        for flow in valid_flows:
            if flow in text:
                return flow
        
        return "EMOTION"  # Varsayılan fallback


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


# =============================================================================
# CHAIN SYSTEM - LangChain Chain Yapıları
# =============================================================================

def create_flow_decision_chain():
    """Akış kararı chain'i oluşturur"""
    flow_prompt = PromptTemplate(
        input_variables=["user_message"],
        template="""Kullanıcının mesajını analiz et ve şu akışlardan birini seç:

ÖNEMLİ KURALLAR:
1. Eğer kullanıcı BİLGİ istiyorsa (nedir, nasıl, açıkla, tanım, principle, concept, theory) → RAG
2. Eğer kullanıcı HAYVAN istiyorsa (köpek, kedi, tilki, ördek fotoğraf/bilgi) → ANIMAL  
3. Eğer kullanıcı SOHBET/DUYGU istiyorsa (merhaba, nasılsın, üzgünüm, mutluyum) → EMOTION

Akışlar:
- ANIMAL: Köpek, kedi, tilki, ördek fotoğraf/bilgi isteği
- RAG: Python, Anayasa, Clean Architecture, teknik terimler, bilgi soruları, "nedir", "nasıl", "açıkla", "tanım", "principle", "concept"
- EMOTION: Duygu analizi, sohbet, normal konuşma

Kullanıcı Mesajı: {user_message}

Sadece şu yanıtlardan birini ver: ANIMAL, RAG, EMOTION"""
    )
    
    return LLMChain(
        llm=llm,
        prompt=flow_prompt,
        output_parser=FlowDecisionParser(),
        output_key="flow_decision"
    )


def create_rag_chain():
    """RAG chain'i oluşturur"""
    rag_prompt = PromptTemplate(
        input_variables=["user_message", "context"],
        template="""Sen bir bilgi asistanısın. Kullanıcının sorularını verilen bağlam bilgilerini kullanarak yanıtla. 
Türkçe, kısa ve net yanıtlar ver. Bağlam bilgisini kullan ama gereksiz detay verme. 
Eğer bağlamda yeterli bilgi yoksa bunu belirt. Yanıtını doğrudan metin olarak ver (JSON formatında değil). 
Maksimum 5 cümle ile yanıtla. Özellikle Clean Architecture, Python, Anayasa konularında uzmanlaşmışsın.

BAĞLAM:
{context}

SORU: {user_message}

YANIT:"""
    )
    
    return LLMChain(
        llm=llm,
        prompt=rag_prompt,
        output_key="rag_response"
    )


def create_animal_chain():
    """Animal chain'i oluşturur - API çağrısı yapar"""
    def animal_processor(user_message: str) -> Dict[str, Any]:
        """Hayvan API'sini çağırır ve sonucu döndürür"""
        animal_result = route_animals(user_message, llm)
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
        return {"response": "Hayvan bulunamadı."}
    
    return animal_processor


def create_emotion_chain():
    """Emotion chain'i oluşturur"""
    def emotion_processor(user_message: str) -> Dict[str, Any]:
        """Duygu analizi yapar"""
        global chatbot_instance
        if chatbot_instance is None:
            chatbot_instance = EmotionChatbot(llm)
        
        result = chatbot_instance.chat(user_message)
        stats = {
            "requests": chatbot_instance.stats["requests"],
            "last_request_at": chatbot_instance.stats["last_request_at"],
        }
        
        out = {"response": result.get("response", ""), "stats": stats}
        if "first_emoji" in result:
            out["first_emoji"] = result["first_emoji"]
        if "second_emoji" in result:
            out["second_emoji"] = result["second_emoji"]
        if "request_debug" in result:
            out["request_debug"] = result["request_debug"]
        return out
    
    return emotion_processor


# =============================================================================
# CHAIN SYSTEM - Ana İşlem Zinciri
# =============================================================================

def create_main_processing_chain():
    """Ana işlem zinciri oluşturur"""
    
    # Alt chain'leri oluştur
    flow_decision_chain = create_flow_decision_chain()
    rag_chain = create_rag_chain()
    animal_processor = create_animal_chain()
    emotion_processor = create_emotion_chain()
    
    def process_message(user_message: str) -> Dict[str, Any]:
        """Ana mesaj işleme fonksiyonu"""
        try:
            print("[CHAIN SYSTEM] AŞAMA 1: Akış kararı alınıyor...")
            
            # AŞAMA 1: Akış kararı
            flow_result = flow_decision_chain.run(user_message=user_message)
            # LangChain chain'leri direkt string döndürür, dict değil
            flow_decision = flow_result if isinstance(flow_result, str) else str(flow_result)
            print(f"[CHAIN SYSTEM] Akış kararı: {flow_decision}")
            
            # AŞAMA 2: Seçilen akışa göre işleme
            if flow_decision == "RAG":
                print("[CHAIN SYSTEM] AŞAMA 2: RAG akışı çalışıyor...")
                return _process_rag_flow(user_message, rag_chain)
            elif flow_decision == "ANIMAL":
                print("[CHAIN SYSTEM] AŞAMA 2: Animal akışı çalışıyor...")
                return animal_processor(user_message)
            elif flow_decision == "EMOTION":
                print("[CHAIN SYSTEM] AŞAMA 2: Emotion akışı çalışıyor...")
                return emotion_processor(user_message)
            else:
                print("[CHAIN SYSTEM] Fallback: Emotion akışı çalışıyor...")
                return emotion_processor(user_message)
                
        except Exception as e:
            print(f"[CHAIN SYSTEM] Hata: {e}")
            return {"error": str(e)}
    
    return process_message


def _process_rag_flow(user_message: str, rag_chain) -> Dict[str, Any] | None:
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
        
        # RAG chain ile işle
        result = rag_chain.run(user_message=user_message, context=context)
        
        # Pick first known source for UI hint
        lit = None
        for s in sources:
            if s in RAG_SOURCES:
                lit = s
                break
        ui = RAG_SOURCES.get(lit or "", None)
        return {
            "rag": True,
            "response": result if isinstance(result, str) else str(result),
            "rag_source": ui.get("id") if ui else None,
            "rag_emoji": ui.get("emoji") if ui else None,
        }

    # Source-filtered retrieval
    chunks = rag_service.retrieve_by_source(user_message, source_filename=source, top_k=4)
    if not chunks:
        return None
    context = "\n\n".join([c.get("text", "") for c in chunks])
    
    # RAG chain ile işle
    result = rag_chain.run(user_message=user_message, context=context)
    
    ui = RAG_SOURCES.get(source)
    return {
        "rag": True,
        "response": result if isinstance(result, str) else str(result),
        "rag_source": ui.get("id"),
        "rag_emoji": ui.get("emoji"),
    }


# Ana chain'i oluştur
main_chain = create_main_processing_chain()


# =============================================================================
# FASTAPI ENDPOINTS
# =============================================================================

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
    """Ana chat endpoint'i - CHAIN SYSTEM ile akış yönlendirmesi yapar"""
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
        # CHAIN SYSTEM ile mesaj işleme
        print("[CHAIN SYSTEM] Mesaj işleniyor...")
        result = main_chain(user_message)
        return result

    except HTTPException as e:
        return {"error": e.detail}
    except Exception as e:
        return {"error": str(e)}


# Çalıştırma:
# uvicorn api_web_chatbot:app --host 0.0.0.0 --port 8000 --reload