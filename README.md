# Akıllı Chatbot Sistemi (FastAPI)

Bu proje **üç ana akışı** birleştiren gelişmiş bir chatbot sistemidir:
- 🧠 **RAG Sistemi**: PDF'lerden bilgi çekme (Python, Anayasa, Clean Architecture)
- 🐶 **Hayvan Sistemi**: Köpek/kedi/tilki/ördek fotoğraf ve bilgi istekleri
- 💭 **Duygu Sistemi**: Kullanıcı mesajından duygu analizi ve iki aşamalı yanıt

LLM, kullanıcının mesajından hangi akışın çalışacağını akıllıca seçer ve ilgili sistemi devreye sokar.

## 🔗 CHAIN SYSTEM - LangChain Entegrasyonu

### ⚡ Chain-Based Mimari
- **LangChain Framework**: Tüm sistem LangChain chain yapısı ile yönetilir
- **Akış Yönlendirme Chain'i**: LLM ile otomatik akış seçimi (RAG/ANIMAL/EMOTION)
- **Modüler Chain'ler**: Her sistem ayrı chain olarak çalışır
- **Output Parser**: Akış kararlarını temizler ve doğrular
- **Sequential Processing**: Sıralı işlem zinciri ile güvenli yönlendirme

### 🔄 Chain İş Akışı
1. **Flow Decision Chain**: Kullanıcı mesajını analiz eder, akış seçer
2. **RAG Chain**: PDF içeriği + kullanıcı sorusu → bilgi yanıtı
3. **Animal Chain**: Hayvan API çağrısı ve sonuç işleme
4. **Emotion Chain**: Duygu analizi ve iki aşamalı yanıt

### 🛡️ Chain Güvenliği
- **Input Sanitization**: Tüm girişler temizlenir
- **Token Limiti**: Maksimum token kontrolü
- **Error Handling**: Chain hatalarında güvenli fallback
- **Security Patterns**: Injection saldırılarına karşı koruma

### 🧠 ConversationSummaryBufferMemory Sistemi
- **Hibrit Yaklaşım**: Uzun konuşmaları özetler, son mesajları hatırlar
- **Token Kontrolü**: 200 token limit ile maliyet optimizasyonu
- **Global Memory**: Tüm chain'ler aynı memory instance'ını paylaşır
- **Otomatik Yönetim**: Konuşma geçmişi otomatik olarak yönetiliyor
- **Context Preservation**: Önceki konuşmaların bağlamı korunuyor

---

## 🚀 Özellikler

### 🧠 RAG (Retrieval-Augmented Generation) Sistemi
- **PDF Desteği**: Python, Anayasa, Clean Architecture PDF'lerinden bilgi çekme
- **Asenkron Model Yükleme**: Site başlatıldığında model arka planda yüklenir
- **Akıllı Yönlendirme**: Bilgi istekleri otomatik RAG'e yönlendirilir
- **5 Cümle Sınırı**: Kısa ve öz yanıtlar
- **PDF Emojileri**: 🐍 Python, ⚖️ Anayasa, 🏗️ Clean Architecture

### 🐶 Hayvan Sistemi
- **7 Fonksiyon**: dog_photo, dog_facts, cat_photo, cat_facts, fox_photo, duck_photo, help_message
- **API Entegrasyonu**: Gerçek hayvan fotoğrafları ve bilgileri
- **Görsel Efektler**: Aktif fonksiyonda düğüm/halat parlaması

### 💭 Duygu Analizi Sistemi
- **İki Aşamalı Yanıt**: İlk/ikinci duygu ve cevap
- **10 Duygu**: Mutlu, Üzgün, Öfkeli, Şaşkın, Utanmış, Endişeli, Gülümseyen, Flörtöz, Sorgulayıcı, Yorgun
- **Emoji Desteği**: Her duygu için özel emoji koleksiyonu
- **İstatistikler**: "Bugün en çok..." gibi isteklerde sayımlar
- **Yeşil Glow**: Duygu sistemi çalıştığında container kenarı yeşil yanar

### 🎨 Gelişmiş UI/UX
- **Sürüklenebilir Düğümler**: Yan panellerde fonksiyon düğümleri
- **Halat Animasyonu**: Düğümler container'a bağlı, fizik simülasyonu
- **Işın Efekti**: Aktif fonksiyondan chat kutusuna ışın çizimi
- **Lightbox**: Resim büyütme, kapatma ve indirme
- **Tema Desteği**: Açık/koyu tema
- **Matrix Arkaplan**: Animasyonlu arkaplan efekti
- **Mobil Uyum**: Responsive tasarım

---

## 🏗️ Proje Mimarisi

### Modüler Sistem Yapısı
```
├── api_web_chatbot.py     # Ana koordinatör (yönlendirme)
├── emotion_system.py      # Duygu analizi sistemi
├── animal_system.py       # Hayvan API sistemi
├── rag_service.py         # RAG sistemi (PDF + ChromaDB)
├── static/
│   ├── app.css           # Tüm stiller
│   └── app.js            # Frontend mantığı
├── templates/
│   └── index.html        # Web sayfası
├── data/
│   ├── mood_emojis.json  # Duygu emojileri
│   ├── chat_history.txt  # Konuşma geçmişi
│   └── mood_counter.txt  # Duygu istatistikleri
└── PDFs/                 # RAG için PDF dosyaları
    ├── Learning_Python.pdf
    ├── gerekceli_anayasa.pdf
    └── clean_architecture.pdf
```

### Akıllı Yönlendirme Sistemi
1. **LLM Analizi**: Mesajı analiz eder (ANIMAL/RAG/EMOTION)
2. **Sistem Seçimi**: İlgili sistemi devreye sokar
3. **Yanıt Üretimi**: Seçilen sistem yanıtı üretir
4. **UI Güncelleme**: Görsel efektler ve emoji güncellemeleri

---

## 🎯 Kullanım Örnekleri

### RAG Sistemi (Bilgi Sorguları)
- **"Python nedir?"** → 🐍 Python PDF'den bilgi + yeşil glow
- **"Clean Architecture principles"** → 🏗️ Clean Architecture PDF'den bilgi
- **"Anayasa temel haklar"** → ⚖️ Anayasa PDF'den bilgi
- **"THE ACYCLIC DEPENDENCIES PRINCIPLE"** → Clean Architecture PDF'den detaylı açıklama

### Hayvan Sistemi
- **"köpek fotoğrafı ver"** → 🐶 Köpek fotoğrafı + düğüm parlaması
- **"kedi bilgisi ver"** → 🐱 Kedi bilgisi + halat animasyonu
- **"tilki fotoğrafı ver"** → 🦊 Tilki fotoğrafı + ışın efekti

### Duygu Sistemi
- **"bugün köpeğim öldü :("** → Üzgün emoji + container yeşil glow + iki aşamalı yanıt
- **"merhaba nasılsın?"** → Mutlu emoji + sohbet
- **"Bugün en çok hangi duyguyu yaşadım?"** → İstatistik raporu

---

## 🛠️ Kurulum ve Çalıştırma

### 1. Gereksinimler
- Python 3.8+
- OpenAI API anahtarı
- 4GB+ RAM (RAG modeli için)

### 2. Kurulum
```bash
# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 3. API Anahtarı
`.env` dosyasını oluşturun:
```
OPENAI_API_KEY=sk-your-api-key-here
```

### 4. PDF Dosyaları
`PDFs/` klasörüne PDF dosyalarınızı yerleştirin:
- `Learning_Python.pdf`
- `gerekceli_anayasa.pdf` 
- `clean_architecture.pdf`

### 5. Çalıştırma
```bash
# Sunucuyu başlat
uvicorn api_web_chatbot:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Kullanım
Tarayıcınızda: `http://localhost:8000/`

---

## 🔧 Teknik Detaylar

### RAG Sistemi
- **Embedding Model**: all-MiniLM-L6-v2
- **Vector Database**: ChromaDB (persistent)
- **Text Chunking**: 900 karakter, 150 overlap
- **Batch Processing**: 1000'lik parçalara bölünür
- **Asenkron Yükleme**: Site başlatıldığında model arka planda yüklenir

### Hayvan Sistemi
- **API'ler**: random.dog, thecatapi.com, randomfox.ca, random-d.uk
- **Fonksiyon Çağırma**: OpenAI function calling
- **Fallback**: Anahtar kelime tabanlı yönlendirme

### Duygu Sistemi
- **JSON Format**: İlk/ikinci duygu + cevap
- **Emoji Seçimi**: Rastgele seçim
- **İstatistik**: Günlük/toplam sayaçlar
- **Kalıcı Depolama**: JSON dosyaları

### Frontend
- **Vanilla JS**: Framework yok
- **CSS Grid/Flexbox**: Modern layout
- **Canvas API**: Matrix efekti
- **SVG**: Halat animasyonları
- **WebSocket**: Gerçek zamanlı güncellemeler

---

## 🏗️ Modüler Mimari Detayları

### api_web_chatbot.py (Ana Koordinatör)
- FastAPI uygulamasını başlatır, statik dosyaları mount eder
- `OpenAI` istemcisi oluşturur
- Uygulama başlangıcında `rag_service.preload_model_async()` ile embedding modelini arka planda yükler
- **Akış Yönlendirme (Aşama 1)**: `_get_flow_decision(user_message)`
  - LLM'e sistem mesajı ile üç seçenek verilir: `ANIMAL | RAG | EMOTION`
  - Mesajda bilgi/teknik terim varsa RAG; hayvan anahtar kelimeleri varsa ANIMAL; aksi halde EMOTION tercih edilir
- **Akış İşleme (Aşama 2)**:
  - `RAG` → `_process_rag_flow(user_message)`
    - Kaynak belirleme (anayasa/clean architecture/python) veya genel arama
    - RAG sistem prompt'u ile "maksimum 5 cümle" yanıt üretimi
    - UI'ye `rag_source` ve `rag_emoji` döner (PDF düğümünü yeşil parlatır)
  - `ANIMAL` → `_process_animal_flow(user_message)`
    - `animal_system.route_animals` çağrılır; image/text sonucu ve emoji döner
  - `EMOTION` → `_process_emotion_flow(user_message)`
    - `EmotionChatbot.chat()` sonucu, istek sayacı ve debug bilgisi döner
- **HTTP Uç Noktalar**
  - `GET /` → `templates/index.html`
  - `POST /chat` → Yukarıdaki yönlendirme akışı

### rag_service.py (RAG Servisi)
- **Telemetri Kapatma**: PostHog no-op patch (Chroma kaynaklı capture hatalarını engeller)
- **Kalıcı ChromaDB**: `.chroma/` altında `PersistentClient` kullanır
- **Embedding**: `SentenceTransformerEmbeddingFunction('all-MiniLM-L6-v2')`
- **Model Önyükleme**: `preload_model_async()` ile arka planda yüklenir
- **Koleksiyon**: `project_pdfs` (cosine benzerlik; embedder function iliştirilir)
- **PDF Okuma**: `pypdf.PdfReader` (yoksa `PyPDF2` fallback)
- **Chunklama**: `_chunk_text(text, chunk_size=900, chunk_overlap=150)`
- **İndeksleme**: `ensure_index()`
  - Mevcut koleksiyon boşsa `PDFs/*.pdf` taranır, text → chunk → `col.add(...)`
  - Batch ekleme: 1000'lik dilimler; hata halinde 500'lük mini-batch fallback
- **Sorgu**:
  - `retrieve_top(query, top_k)` → genel arama
  - `retrieve_by_source(query, source_filename, top_k)` → kaynağa göre filtreli arama

### emotion_system.py (Duygu Analizi)
- `EmotionChatbot` sınıfı durum tutar (`messages`, `stats`)
- **Kalıcı Dosyalar**: `data/mood_emojis.json`, `data/chat_history.txt`, `data/mood_counter.txt`
- `get_functions()` ile `get_emotion_stats` function-calling desteği
- `chat(user_message)`:
  - Sistem prompt'u ile iki aşamalı duygu formatı veya function-calling (istatistik) üretir
  - Gelen JSON'dan duygu sayaçlarını günceller, random emoji seçer, geçmişe yazar

### animal_system.py (Hayvan API'leri)
- **Fonksiyonlar**: `dog_photo`, `dog_facts`, `cat_photo`, `cat_facts`, `fox_photo`, `duck_photo`
- **API'ler**: random.dog, dogapi.dog, meowfacts, thecatapi, randomfox, random-d.uk
- `route_animals(user_message, client)`:
  - Ön filtre: hayvan anahtar kelimesi yoksa denemez
  - OpenAI function-calling ile uygun fonksiyon seçilir; hata/boşlukta keyword fallback çalışır

### Frontend Detayları (static/*)

#### static/app.js
- **Chat Akışı**: İstek gönderme (`/chat`), durum/emoji güncellemeleri
- **RAG Yanıtı**: `handleRagResponse` ile tek seferde 5 cümleyi sınırlar; `setActivePdfGlow` ile PDF düğümü/halatı sarı parlar
- **Hayvan Yanıtı**: Görsel/text mesaj, ilgili düğümün parlaması ve ışın efekti
- **Duygu Yanıtı**: İki aşamalı mod (Next butonu); PLAIN yolunda sadece node ve ip’ler yeşil parlar
- **Draggable Düğümler**: Fonksiyon düğümleri, halat fiziği (SVG path), Matrix arkaplan, tema (dark/light)
- **Node Hiyerarşisi (Yeni)**: RAG/API/PLAIN büyük node’leri ve onlara bağlı küçük node’ler. Başlangıçta küçük node’ler gizli (collapsed); büyük node’e tıklayınca çocuklar tarafına göre bir yay şeklinde dışarı açılır, tekrar tıklayınca merkeze akıp kaybolur. Sürüklerken açılmaz (drag ile click ayrıştırıldı) ve drag sırasında transition devre dışı olduğundan tepki anlıktır.
- **Tek Hat Tasarımı (Yeni)**: Chat ←→ (tek ip) ←→ Büyük Node ←→ (çoklu ip) ←→ Küçük Node’ler.
- **Otomatik Açılma (Yeni)**: Kapalıyken bir küçük node prompt ile tetiklenirse ilgili büyük node grubu otomatik açılır.
- **Renkler (Yeni)**: RAG sarı, API mavi, PLAIN yeşil; yalnızca node ve ip’ler parlar.

#### static/app.css
- **Tema Değişkenleri**: Light/dark, `glow-green` efekti, düğüm/halat stilleri, chat mesajları, lightbox

#### templates/index.html
- **Düğüm Butonları**: Hayvan ve PDF'ler, matrix canvas, yüz alanı, chat bileşenleri

---

## 🛠️ Sorun Giderme

### Chroma Telemetry / PostHog Hataları
- `rag_service.py` içinde `ANONYMIZED_TELEMETRY=False`, `CHROMA_TELEMETRY_IMPL=noop`, `POSTHOG_DISABLED=true` ve PostHog capture no-op yamaları uygulanmıştır

### Batch Size Hatası
- `Batch size XXXX exceeds maximum ...` hatası için indeksleme 1000'lik batch'lere bölünür; hata durumunda 500 mini-batch ile yeniden denenir

### RAG Boyutu Optimizasyonu
- Chunk değerlerini büyütüp overlap'i düşürmeyi, gereksiz metadata'yı azaltmayı düşünebilirsiniz
- Chunk size: 1200, overlap: 100 gibi ayarlar deneyebilirsiniz

---

## 🎨 UI/UX Özellikleri

### Görsel Efektler
- **Yeşil Glow**: Duygu sistemi çalıştığında container kenarı
- **Düğüm Parlaması**: Aktif hayvan fonksiyonunda
- **Işın Animasyonu**: Düğümden chat kutusuna
- **Emoji Değişimi**: Yüz alanında dinamik emoji
- **Matrix Efekti**: Arka plan animasyonu

#### Node Hiyerarşisi ve Aç/Kapa (Yeni)
- **Büyük Node’ler**: RAG, API, PLAIN (boyut artırıldı)
- **Küçük Node’ler**: Başlangıçta kapalı; tıklayınca açılır ve tarafına göre (sağda→sağa, solda→sola) yayılan bir yay üzerinde konumlanır
- **Tek Hat**: Büyük node ile chat arasında tek ip; küçük node’ler büyük node’e bağlanır
- **Renkli Parlama**: RAG=sarı, API=mavi, PLAIN=yeşil; yalnızca node ve ip’ler yanar
- **Drag Davranışı**: Sürüklerken açılma tetiklenmez; drag sırasında transition kapalıdır → gecikmesiz hareket
- **PLAIN Kısayol**: PLAIN node’üne tıklayınca input “Bugün çok kötü hissediyorum :(” ile doldurulur
- **Küçük Etiketler**: RAG çocuk etiketlerinden “PDF -” kaldırıldı (ör. “Python”, “Anayasa”, “Clean Arch”)

### Etkileşim
- **Sürükle-Bırak**: Düğümleri hareket ettirme
- **Tıklama**: Otomatik prompt doldurma
- **Lightbox**: Resim büyütme/küçültme
- **Tema**: Açık/koyu mod geçişi

---

## 🔮 Gelecek Özellikler

- [ ] Daha fazla PDF desteği
- [ ] Çoklu dil desteği
- [ ] Sesli yanıt
- [ ] Kullanıcı profilleri
- [ ] Gelişmiş analitik
- [ ] API dokümantasyonu

---

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

---

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

---

## 🔒 Güvenlik Önlemleri

### Input Sanitization (Giriş Temizleme)
- **HTML Escape**: Tüm kullanıcı girdileri HTML escape edilir
- **Tehlikeli Pattern Kontrolü**: Script injection, XSS, iframe injection vb. saldırıları önler
- **Regex Filtreleme**: JavaScript, VBScript, data URL'leri ve event handler'ları engeller

### Mesaj Uzunluk Sınırları
- **Ana Sistem**: 2000 karakter maksimum
- **Duygu Sistemi**: 1000 karakter maksimum  
- **Hayvan Sistemi**: 500 karakter maksimum
- **RAG Sistemi**: 1000 karakter maksimum

### Token Koruması
- **Token Hesaplama**: Türkçe için yaklaşık 1 token = 4 karakter
- **Maksimum Token**: 1000 token per request
- **Otomatik Fallback**: Çok fazla token varsa güvenli akışa yönlendirir

### Korunan Saldırı Türleri
- ✅ **XSS (Cross-Site Scripting)**
- ✅ **Script Injection**
- ✅ **Iframe Injection**
- ✅ **Data URL Attacks**
- ✅ **Event Handler Injection**
- ✅ **Token Bombing**
- ✅ **Message Flooding**

### Güvenlik Logları
- Tüm tehlikeli pattern tespitlerinde log kaydı
- Token aşımı durumlarında uyarı
- Güvenlik filtreleme durumlarında bilgilendirme

### Performans Koruması
- Aşırı uzun mesajlar engellenir
- Token limitleri ile maliyet kontrolü
- Sistem kaynaklarını koruma

---

- **GitHub**: [ErenErgin78/Openai-Emotion-Animals-Chatbot](https://github.com/ErenErgin78/Openai-Emotion-Animals-Chatbot)

---