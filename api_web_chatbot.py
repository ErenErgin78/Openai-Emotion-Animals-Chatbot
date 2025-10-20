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
from statistic_system import StatisticSystem
from animal_system import route_animals, _animal_emoji
from rag_service import rag_service

load_dotenv()

app = FastAPI(title="CHAIN SYSTEM - Akıllı Chatbot Sistemi", version="3.0.0")

# LangChain LLM instance - Fallback mekanizması ile
def get_llm():
    """OpenAI API geçersizse Gemini'yi kullan"""
    try:
        # OpenAI API'yi test et
        print("[LLM] OpenAI API test ediliyor...")
        test_llm = OpenAI(temperature=0.1, max_tokens=1000, request_timeout=15)
        # Basit bir test çağrısı yap
        test_result = test_llm.invoke("test")
        print(f"[LLM] OpenAI test sonucu: {test_result}")
        print("[LLM] OpenAI API kullanılıyor")
        return test_llm
    except Exception as e:
        print(f"[LLM] OpenAI API hatası: {e}")
        try:
            # Gemini API'yi test et - sadece API key ile
            print("[LLM] Gemini API test ediliyor...")
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise Exception("GEMINI_API_KEY bulunamadı")
            genai.configure(api_key=api_key)
            
            # LangChain olmadan direkt Gemini kullan
            model = genai.GenerativeModel('gemini-2.5-flash')
            # Test çağrısı yap
            response = model.generate_content("test")
            print(f"[LLM] Gemini test sonucu: {response.text}")
            
            # LangChain wrapper oluştur - Google Cloud credentials olmadan
            from langchain_google_genai import ChatGoogleGenerativeAI
            gemini_llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.1,
                max_tokens=1000,
                request_timeout=15,
                google_api_key=api_key
            )
            print("[LLM] Gemini API kullanılıyor")
            return gemini_llm
        except Exception as gemini_error:
            print(f"[LLM] Gemini API hatası: {gemini_error}")
            raise Exception(f"API hatası - OpenAI: {e}, Gemini: {gemini_error}")

llm = get_llm()

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

# RAG kaynakları (UI id'leri sabit: pdf-python/anayasa/clean)
RAG_SOURCES = {
    "cat_care.pdf": {"id": "pdf-python", "emoji": "🐱", "alias": "cat"},
    "parrot_care.pdf": {"id": "pdf-anayasa", "emoji": "🦜", "alias": "parrot"},
    "rabbit_care.pdf": {"id": "pdf-clean", "emoji": "🐰", "alias": "rabbit"},
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
        valid_flows = ["ANIMAL", "RAG", "EMOTION", "STATS", "HELP"]
        
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
1. Eğer kullanıcı BİLGİ istiyorsa (hayvan bakımı, beslenme, barınma, sağlık, eğitim, bakım önerileri) → RAG
2. Eğer kullanıcı HAYVAN istiyorsa (köpek, kedi, tilki, ördek fotoğraf/bilgi) → ANIMAL  
3. Eğer kullanıcı SOHBET/DUYGU istiyorsa (merhaba, nasılsın, üzgünüm, mutluyum) → EMOTION
4. Eğer kullanıcı İSTATİSTİK/ÖZET istiyorsa ("kaç kez/defa", "istatistik", "özet", belirli duygu istatistiği, bugün/bugüne ait sayım) → STATS
5. Eğer kullanıcı hiçbir özelliği çağırmıyorsa (genel sorular, yardım, ne yapabilirsin) → HELP

Akışlar:
- ANIMAL: Köpek, kedi, tilki, ördek fotoğraf/bilgi isteği
- RAG: Kedi/Papağan/Tavşan bakımı, beslenme, barınma, sağlık, eğitim, bakım rutinleri
- EMOTION: Duygu analizi, sohbet, normal konuşma
- STATS: Duygu istatistikleri (today/all + isteğe bağlı duygu filtresi)
- HELP: Yardım, ne yapabilirsin, genel bilgi istekleri

Kullanıcı Mesajı: {input}

Sadece şu yanıtlardan birini ver: ANIMAL, RAG, EMOTION, STATS, HELP"""
    )
    
    def flow_processor(input_data):
        """Flow decision işleyicisi - Gemini ve OpenAI çıktılarını normalize eder"""
        result = (flow_prompt | llm).invoke(input_data)
        
        # Ham cevabı konsola yazdır
        print(f"[FLOW DEBUG] Ham result tipi: {type(result)}")
        print(f"[FLOW DEBUG] Ham result: {result}")
        
        # Gemini ve OpenAI çıktılarını normalize et
        if hasattr(result, 'content'):
            # LangChain response objesi
            text = result.content
            print(f"[FLOW DEBUG] Content: {text}")
        elif isinstance(result, str):
            # String çıktı
            text = result
            print(f"[FLOW DEBUG] String: {text}")
        else:
            # Diğer durumlar için string'e çevir
            text = str(result)
            print(f"[FLOW DEBUG] String'e çevriliyor: {text}")
        
        # FlowDecisionParser'ı kullan
        parser = FlowDecisionParser()
        parsed_result = parser.parse(text)
        print(f"[FLOW DEBUG] Parsed result: {parsed_result}")
        return parsed_result
    
    return flow_processor


def create_rag_chain():
    """RAG chain'i oluşturur - ConversationSummaryBufferMemory ile"""
    # Memory ile kullanırken sadece tek input variable kullan - chat_history otomatik eklenir
    # Context bilgisi prompt'a dahil edilir, memory sistemi konuşma geçmişini yönetir
    rag_prompt = PromptTemplate(
        input_variables=["input"],
        template="""Sen bir hayvan bakımı bilgi asistanısın. Verilen bağlam (PDF parçaları) üzerinden
kullanıcının sorusunu yanıtla. Türkçe, kısa ve net yaz. Bağlamı kullan; bağlamda bilgi yoksa bunu açıkça söyle.
Yanıtını doğrudan düz metin olarak ver (JSON değil). Maksimum 5 cümle.

SORU: {input}

YANIT:"""
    )
    
    def rag_processor(input_data):
        """RAG işleyicisi - Gemini ve OpenAI çıktılarını normalize eder"""
        result = (rag_prompt | llm).invoke(input_data)
        
        # Ham cevabı konsola yazdır
        print(f"[RAG DEBUG] Ham result tipi: {type(result)}")
        print(f"[RAG DEBUG] Ham result: {result}")
        
        # Gemini ve OpenAI çıktılarını normalize et
        if hasattr(result, 'content'):
            # LangChain response objesi
            print(f"[RAG DEBUG] Content: {result.content}")
            return result.content
        elif isinstance(result, str):
            # String çıktı
            print(f"[RAG DEBUG] String: {result}")
            return result
        else:
            # Diğer durumlar için string'e çevir
            print(f"[RAG DEBUG] String'e çevriliyor: {str(result)}")
            return str(result)
    
    return rag_processor


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
            # Fallback mekanizması ile client oluştur
            try:
                from openai import OpenAI
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                # Test çağrısı yap
                client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
                chatbot_instance = EmotionChatbot(client)
                print("[EMOTION] OpenAI API kullanılıyor")
            except Exception as e:
                print(f"[EMOTION] OpenAI API hatası: {e}")
                # Gemini kullan
                chatbot_instance = EmotionChatbot()  # client=None, Gemini kullanacak
                print("[EMOTION] Gemini API kullanılıyor")
        
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


def create_stats_chain():
    """Stats chain'i oluşturur - data/ dosyalarından hesaplar"""
    stats_system = StatisticSystem()

    def stats_processor(user_message: str) -> Dict[str, Any]:
        try:
            result = stats_system.answer(user_message)
            # Memory'ye kaydet
            memory.save_context({"input": user_message}, {"output": result.get("response", "")})
            return result
        except Exception as e:
            err = f"İstatistik sistemi hatası: {e}"
            memory.save_context({"input": user_message}, {"output": err})
            return {"response": err}

    return stats_processor

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
    stats_processor = create_stats_chain()
    
    def process_message(user_message: str) -> Dict[str, Any]:
        """Ana mesaj işleme fonksiyonu - ConversationSummaryBufferMemory ile"""
        try:
            print("[CHAIN SYSTEM] AŞAMA 1: Akış kararı alınıyor...")
            
            # Memory sistemi aktif - ConversationSummaryBufferMemory ile konuşma geçmişi yönetiliyor
            
            # AŞAMA 1: Akış kararı
            flow_decision = flow_decision_chain({"input": user_message})
            print(f"[CHAIN SYSTEM] Akış kararı: {flow_decision}")
            
            # AŞAMA 2: Seçilen akışa göre işleme
            if flow_decision == "RAG":
                print("[CHAIN SYSTEM] AŞAMA 2: RAG akışı çalışıyor...")
                rag_result = _process_rag_flow(user_message, rag_chain)
                if rag_result is None:
                    print("[CHAIN SYSTEM] RAG sonucu None, HELP akışına yönlendiriliyor...")
                    return _process_help_flow(user_message)
                return rag_result
            elif flow_decision == "ANIMAL":
                print("[CHAIN SYSTEM] AŞAMA 2: Animal akışı çalışıyor...")
                return animal_processor(user_message)
            elif flow_decision == "EMOTION":
                print("[CHAIN SYSTEM] AŞAMA 2: Emotion akışı çalışıyor...")
                return emotion_processor(user_message)
            elif flow_decision == "STATS":
                print("[CHAIN SYSTEM] AŞAMA 2: Stats akışı çalışıyor...")
                return stats_processor(user_message)
            elif flow_decision == "HELP":
                print("[CHAIN SYSTEM] AŞAMA 2: Help akışı çalışıyor...")
                result = _process_help_flow(user_message)
                print(f"[CHAIN SYSTEM] Help result: {result}")
                return result
            else:
                print("[CHAIN SYSTEM] Fallback: Help akışı çalışıyor...")
                result = _process_help_flow(user_message)
                print(f"[CHAIN SYSTEM] Fallback result: {result}")
                return result
                
        except Exception as e:
            print(f"[CHAIN SYSTEM] Hata: {e}")
            return {"error": str(e)}
    
    return process_message


def _process_rag_flow(user_message: str, rag_chain) -> Dict[str, Any] | None:
    """RAG akışını işler - PDF'lerden bilgi çeker"""
    t = user_message.lower()
    
    # Heuristic: explicit source keywords (hayvan bakım)
    if ("kedi" in t or "cat" in t):
        source = "cat_care.pdf"
    elif ("papağan" in t or "parrot" in t or "kuş" in t):
        source = "parrot_care.pdf"
    elif ("tavşan" in t or "rabbit" in t):
        source = "rabbit_care.pdf"
    else:
        # LLM RAG seçtiyse anahtar kelime kontrolü yapmadan genel retrieval dene
        chunks = rag_service.retrieve_top(user_message, top_k=4)
        if not chunks:
            print("[RAG] RAG'de ilgili bilgi bulunamadı")
            return None
        context = "\n\n".join([c.get("text", "") for c in chunks])
        sources = list({(c.get("metadata", {}) or {}).get("source", "?") for c in chunks})
        
        # RAG chain ile işle - context'i prompt'a dahil et
        combined_input = f"BAĞLAM:\n{context}\n\nSORU: {user_message}"
        result = rag_chain({"input": combined_input})
        
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
    result = rag_chain({"input": combined_input})
    
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
• Kedi / Papağan / Tavşan bakımı (beslenme, barınma, sağlık, eğitim)
• "Kedi yavrusu nasıl beslenir?", "Papağan kafes bakımı nasıl yapılır?", "Tavşan tırnak kesimi nasıl yapılır?"

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
        
        # Result'u kontrol et ve hata varsa düzelt
        if isinstance(result, dict) and "error" in result:
            print(f"[CHAIN SYSTEM] Hata tespit edildi: {result['error']}")
            return {"error": result["error"]}
        
        # Result'un geçerli olduğundan emin ol
        if not isinstance(result, dict):
            print(f"[CHAIN SYSTEM] Geçersiz result tipi: {type(result)}")
            return {"error": "Geçersiz response formatı"}
            
        print(f"[CHAIN SYSTEM] Başarılı response: {result}")
        return result

    except HTTPException as e:
        print(f"[CHAIN SYSTEM] HTTPException: {e.detail}")
        return {"error": e.detail}
    except Exception as e:
        print(f"[CHAIN SYSTEM] Exception: {str(e)}")
        return {"error": f"Sunucu hatası: {str(e)}"}


# Çalıştırma:
# uvicorn api_web_chatbot:app --host 0.0.0.0 --port 8000 --reload