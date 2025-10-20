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
from langchain.schema import BaseOutputParser
from langchain.memory import ConversationSummaryBufferMemory

# Sistem modüllerini import et
from emotion_system import EmotionChatbot
from animal_system import route_animals, _animal_emoji
from rag_service import rag_service

load_dotenv()

app = FastAPI(title="CHAIN SYSTEM - Akıllı Chatbot Sistemi", version="3.0.0")

# LangChain LLM instance
llm = OpenAI(temperature=0.1, max_tokens=1000, request_timeout=15)

# =============================================================================
# CONVERSATIONSUMMARYBUFFERMEMORY - GLOBAL MEMORY SİSTEMİ
# =============================================================================
# Hibrit yaklaşım: uzun konuşmaları özetler, son mesajları hatırlar
# Token limiti ile maliyet kontrolü sağlar
# Tüm chain'ler bu memory sistemi ile konuşma geçmişini paylaşır
memory = ConversationSummaryBufferMemory(
    llm=llm,
    max_token_limit=200,  # 200 token limit - maliyet kontrolü için
    memory_key="chat_history",  # Memory anahtarı - chain'lerde otomatik kullanılır
    return_messages=True  # Mesaj formatında döndür - LangChain uyumluluğu için
)

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
        valid_flows = ["ANIMAL", "RAG", "EMOTION", "HELP"]
        
        for flow in valid_flows:
            if flow in text:
                return flow
        
        return "HELP"  # Varsayılan fallback - yardım mesajı


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
    """Akış kararı chain'i oluşturur - ConversationSummaryBufferMemory ile"""
    # Memory sistemi ile akış kararı - önceki konuşma bağlamı otomatik eklenir
    flow_prompt = PromptTemplate(
        input_variables=["input"],
        template="""Kullanıcının mesajını analiz et ve şu akışlardan birini seç:

ÖNEMLİ KURALLAR:
1. Eğer kullanıcı BİLGİ istiyorsa (nedir, nasıl, açıkla, tanım, principle, concept, theory) → RAG
2. Eğer kullanıcı HAYVAN istiyorsa (köpek, kedi, tilki, ördek fotoğraf/bilgi) → ANIMAL  
3. Eğer kullanıcı SOHBET/DUYGU istiyorsa (merhaba, nasılsın, üzgünüm, mutluyum) → EMOTION
4. Eğer kullanıcı hiçbir özelliği çağırmıyorsa (genel sorular, yardım, ne yapabilirsin) → HELP

Akışlar:
- ANIMAL: Köpek, kedi, tilki, ördek fotoğraf/bilgi isteği
- RAG: Python, Anayasa, Clean Architecture, teknik terimler, bilgi soruları, "nedir", "nasıl", "açıkla", "tanım", "principle", "concept"
- EMOTION: Duygu analizi, sohbet, normal konuşma
- HELP: Yardım, ne yapabilirsin, genel bilgi istekleri

Kullanıcı Mesajı: {input}

Sadece şu yanıtlardan birini ver: ANIMAL, RAG, EMOTION, HELP"""
    )
    
    # RunnableSequence kullanarak modern LangChain syntax
    return flow_prompt | llm | FlowDecisionParser()


def create_rag_chain():
    """RAG chain'i oluşturur - ConversationSummaryBufferMemory ile"""
    # Memory ile kullanırken sadece tek input variable kullan - chat_history otomatik eklenir
    # Context bilgisi prompt'a dahil edilir, memory sistemi konuşma geçmişini yönetir
    rag_prompt = PromptTemplate(
        input_variables=["input"],
        template="""Sen bir bilgi asistanısın. Kullanıcının sorularını verilen bağlam bilgilerini kullanarak yanıtla. 
Türkçe, kısa ve net yanıtlar ver. Bağlam bilgisini kullan ama gereksiz detay verme. 
Eğer bağlamda yeterli bilgi yoksa bunu belirt. Yanıtını doğrudan metin olarak ver (JSON formatında değil). 
Maksimum 5 cümle ile yanıtla.

SORU: {input}

YANIT:"""
    )
    
    # RunnableSequence kullanarak modern LangChain syntax
    return rag_prompt | llm


def create_animal_chain():
    """Animal chain'i oluşturur - API çağrısı yapar - ConversationSummaryBufferMemory ile"""
    def animal_processor(user_message: str) -> Dict[str, Any]:
        """Hayvan API'sini çağırır ve sonucu döndürür - memory sistemi ile timeout handling"""
        # Hayvan API'leri için timeout ve hata yönetimi
        # Memory sistemi ile konuşma geçmişi otomatik olarak yönetiliyor
        try:
            print("[ANIMAL CHAIN] Hayvan API'si çağrılıyor...")
            # OpenAI client oluştur - route_animals client bekliyor
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
                
                # Memory'ye animal yanıtını kaydet
                memory.save_context(
                    {"input": user_message},
                    {"output": out["response"]}
                )
                
                print(f"[ANIMAL CHAIN] Başarılı: {animal}")
                return out
            
            # Hayvan bulunamadı durumu için de memory'ye kaydet
            error_response = "Hayvan bulunamadı."
            memory.save_context(
                {"input": user_message},
                {"output": error_response}
            )
            print("[ANIMAL CHAIN] Hayvan bulunamadı")
            return {"response": error_response}
            
        except Exception as e:
            print(f"[ANIMAL CHAIN] Hata: {e}")
            # Timeout veya API hatası durumunda fallback yanıt
            error_response = "Hayvan API'si şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin."
            memory.save_context(
                {"input": user_message},
                {"output": error_response}
            )
            return {"response": error_response}
    
    return animal_processor


def create_emotion_chain():
    """Emotion chain'i oluşturur - ConversationSummaryBufferMemory ile"""
    def emotion_processor(user_message: str) -> Dict[str, Any]:
        """Duygu analizi yapar - memory sistemi ile"""
        # Emotion sistemi için OpenAI client oluşturma
        # Memory sistemi ile konuşma geçmişi otomatik olarak yönetiliyor
        global chatbot_instance
        if chatbot_instance is None:
            # OpenAI client oluştur - llm değil client kullan
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            chatbot_instance = EmotionChatbot(client)
        
        # Memory sistemi ile önceki konuşma geçmişi otomatik olarak yönetiliyor
        
        result = chatbot_instance.chat(user_message)
        stats = {
            "requests": chatbot_instance.stats["requests"],
            "last_request_at": chatbot_instance.stats["last_request_at"],
        }
        
        # Memory'ye yeni konuşmayı kaydet
        memory.save_context(
            {"input": user_message},
            {"output": result.get("response", "")}
        )
        
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
        """Ana mesaj işleme fonksiyonu - ConversationSummaryBufferMemory ile"""
        try:
            print("[CHAIN SYSTEM] AŞAMA 1: Akış kararı alınıyor...")
            
            # Memory sistemi aktif - ConversationSummaryBufferMemory ile konuşma geçmişi yönetiliyor
            
            # AŞAMA 1: Akış kararı
            flow_result = flow_decision_chain.invoke({"input": user_message})
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
            elif flow_decision == "HELP":
                print("[CHAIN SYSTEM] AŞAMA 2: Help akışı çalışıyor...")
                return _process_help_flow(user_message)
            else:
                print("[CHAIN SYSTEM] Fallback: Help akışı çalışıyor...")
                return _process_help_flow(user_message)
                
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
        
        # RAG chain ile işle - context'i prompt'a dahil et
        combined_input = f"BAĞLAM:\n{context}\n\nSORU: {user_message}"
        result = rag_chain.invoke({"input": combined_input})
        
        # Memory'ye RAG yanıtını kaydet
        memory.save_context(
            {"input": user_message},
            {"output": result if isinstance(result, str) else str(result)}
        )
        
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
    
    # RAG chain ile işle - context'i prompt'a dahil et
    combined_input = f"BAĞLAM:\n{context}\n\nSORU: {user_message}"
    result = rag_chain.invoke({"input": combined_input})
    
    # Memory'ye RAG yanıtını kaydet
    memory.save_context(
        {"input": user_message},
        {"output": result if isinstance(result, str) else str(result)}
    )
    
    ui = RAG_SOURCES.get(source)
    return {
        "rag": True,
        "response": result if isinstance(result, str) else str(result),
        "rag_source": ui.get("id"),
        "rag_emoji": ui.get("emoji"),
    }


def _process_help_flow(user_message: str) -> Dict[str, Any]:
    """Help akışını işler - kullanıcıya yönlendirici mesaj verir"""
    help_message = """🤖 Merhaba! Ben akıllı bir chatbot'um ve size şu özelliklerle yardımcı olabilirim:

📚 **BİLGİ SİSTEMİ (RAG)**: 
• Python, Anayasa, Clean Architecture konularında sorular sorabilirsiniz
• "Python nedir?", "Clean Architecture principles" gibi sorular

🐶 **HAYVAN SİSTEMİ**:
• Köpek, kedi, tilki, ördek fotoğraf ve bilgileri
• "köpek fotoğrafı ver", "kedi bilgisi ver" gibi istekler

💭 **DUYGU ANALİZİ**:
• Duygularınızı analiz eder ve size uygun yanıtlar verir
• "Bugün çok mutluyum", "Üzgün hissediyorum" gibi mesajlar

🎯 **KULLANIM**: Ekranda gördüğünüz kutucukları kullanarak veya yukarıdaki örnekler gibi mesajlar göndererek bu chatbot'u kullanabilirsiniz!"""
    
    # Memory'ye help yanıtını kaydet
    memory.save_context(
        {"input": user_message},
        {"output": help_message}
    )
    
    return {
        "help": True,
        "response": help_message
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