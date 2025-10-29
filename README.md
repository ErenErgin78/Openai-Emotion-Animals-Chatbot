# Kairu LLM Eğitimi - Kapsamlı Chatbot Projesi

Bu proje, **Kairu LLM eğitiminin tüm haftalarını** birleştiren kapsamlı bir chatbot sistemidir. Her hafta öğrenilen konular, gerçek bir projede uygulanarak pekiştirilmiştir.

- **GitHub**: [ErenErgin78/Openai-Emotion-Animals-Chatbot](https://github.com/ErenErgin78/Openai-Emotion-Animals-Chatbot)

## 🎓 Eğitim Süreci ve Proje Gelişimi

### 📚 **1. Hafta: LLM Temelleri**
- **Öğrenilen Konular**: LLM modellerine genel giriş, model türleri ve özellikleri
- **Projede Uygulama**: OpenAI API entegrasyonu ve temel LLM çağrıları
- **Kod Yapısı**: `OpenAI` istemcisi oluşturma ve sistem mesajları

### 🎯 **2. Hafta: Prompt Engineering**
- **Öğrenilen Konular**: Etkili prompt yazma teknikleri, sistem mesajları
- **Projede Uygulama**: Base prompt ayarları ve 7 farklı public API entegrasyonu
- **Kod Yapısı**: `animal_system.py` - Hayvan API'leri ve function calling
- **Özellikler**: 
  - Köpek/kedi/tilki/ördek fotoğraf ve bilgi API'leri
  - OpenAI function calling ile akıllı yönlendirme
  - Görsel efektler ve animasyonlar

### 🔧 **3. Hafta: Model Optimizasyonu ve Summarizer Entegrasyonu**
- **Öğrenilen Konular**: AutoTokenizer & AutoModel, GPT/BERT/T5 karşılaştırması, CPU/GPU performans
- **Summarizer Modeli (T5-small)**: Kullanıcı mesajları 200+ token olduğunda otomatik olarak özetleyerek AI'ya gönderilir, böylece token maliyetleri ve işlem süreleri optimize edilir
- **Projeye Etkisi**: Uzun mesajlar özetlenerek hem API maliyetleri düşürülür hem de sistem performansı artırılır. Summarizer çalıştığında konsola kısaltılmış metin yazdırılır

### 🧠 **4. Hafta: RAG Sistemleri**
- **Öğrenilen Konular**: Retrieval-Augmented Generation, vektör veritabanları, embedding
- **Projede Uygulama**: ChromaDB ile PDF tabanlı bilgi sistemi
- **Kod Yapısı**: `rag_service.py` - RAG servisi
- **Özellikler**:
  - PDF'lerden bilgi çekme (Python, Anayasa, Clean Architecture)
  - ChromaDB vektör veritabanı
  - Asenkron model yükleme
  - Akıllı kaynak belirleme

### ⚡ **5. Hafta: LangChain ve Memory Yönetimi** *(Devam Ediyor)*
- **Öğrenilen Konular**: Chain yapıları, Memory yönetimi, Tool integration, Agent'lar
- **Projede Uygulama**: LangChain entegrasyonu ve ConversationSummaryBufferMemory
- **Kod Yapısı**: Chain-based mimari ve hibrit memory sistemi
- **Özellikler**:
  - **LangChain Framework**: Tüm sistem chain yapısı ile yönetilir
  - **ConversationSummaryBufferMemory**: Uzun konuşmaları özetler, son mesajları hatırlar
  - **Akış Yönlendirme Chain'i**: LLM ile otomatik akış seçimi
  - **Modüler Chain'ler**: Her sistem ayrı chain olarak çalışır

---

## 🏗️ Proje Mimarisi

### 🎯 **Dört Ana Akış Sistemi**
1. **🧠 RAG Sistemi**: PDF'lerden bilgi çekme ve akıllı yanıt üretimi
2. **🐶 Hayvan Sistemi**: 7 farklı API ile hayvan fotoğraf ve bilgi servisi
3. **💭 Duygu Analizi**: 10 duygu tespiti ve iki aşamalı yanıt sistemi
4. **📊 İstatistik Sistemi**: Duygu verilerini analiz eden ayrı akış

### 🧠 **Memory Yönetimi**
- **ConversationSummaryBufferMemory**: Hibrit yaklaşım
- **Token Kontrolü**: 200 token limit ile maliyet optimizasyonu
- **Global Memory**: Tüm chain'ler aynı memory instance'ını paylaşır
- **Context Preservation**: Önceki konuşmaların bağlamı korunuyor

---

## 🚀 Özellikler

### 🧠 **RAG Sistemi**
- PDF'lerden bilgi çekme (Python, Anayasa, Clean Architecture)
- ChromaDB vektör veritabanı
- Asenkron model yükleme
- 5 cümle sınırlı yanıtlar

### 🐶 **Hayvan Sistemi**
- 7 farklı API entegrasyonu
- Gerçek hayvan fotoğrafları ve bilgileri
- OpenAI function calling
- Görsel efektler ve animasyonlar

### 💭 **Duygu Analizi**
- 10 farklı duygu tespiti
- İki aşamalı yanıt sistemi
- Emoji desteği
- Kalıcı veri depolama

### 📊 **İstatistik Sistemi**
- Duygu verilerini analiz eder
- Bugün/tüm zamanlar filtreleme
- Belirli duygu istatistikleri
- data/ klasöründen otomatik veri okuma

### 📝 **Summarizer Modeli (T5-small)**
- 200+ token olan uzun mesajları otomatik özetler
- Token maliyetlerini optimize eder
- API işlem sürelerini kısaltır
- Konsola özet çıktısı loglar

### 🎨 **Gelişmiş UI/UX**
- Sürüklenebilir düğümler ve halat animasyonları
- Matrix arkaplan efekti
- Lightbox resim görüntüleme
- Açık/koyu tema desteği
- Node hiyerarşisi (büyük-küçük node sistemi)

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
- `.pdf`
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

## 🎯 Kullanım Örnekleri

### RAG Sistemi
- **"Python nedir?"** → 🐍 Python PDF'den bilgi
- **"Clean Architecture principles"** → 🏗️ Clean Architecture PDF'den bilgi
- **"Anayasa temel haklar"** → ⚖️ Anayasa PDF'den bilgi

### Hayvan Sistemi
- **"köpek fotoğrafı ver"** → 🐶 Köpek fotoğrafı + düğüm parlaması
- **"kedi bilgisi ver"** → 🐱 Kedi bilgisi + halat animasyonu
- **"tilki fotoğrafı ver"** → 🦊 Tilki fotoğrafı + ışın efekti

### Duygu Sistemi
- **"bugün köpeğim öldü :("** → Üzgün emoji + container yeşil glow
- **"merhaba nasılsın?"** → Mutlu emoji + sohbet

### İstatistik Sistemi
- **"Bugün kaç kere mutlu oldum?"** → Bugünkü mutluluk sayısı
- **"En çok hangi duyguyu yaşadım?"** → Tüm zamanlar duygu özeti
- **"Üzgün duygu istatistikleri"** → Sadece üzgün duygu analizi

---

## 🔧 Teknik Detaylar

### RAG Sistemi
- **Embedding Model**: all-MiniLM-L6-v2
- **Vector Database**: ChromaDB (persistent)
- **Text Chunking**: 900 karakter, 150 overlap
- **Batch Processing**: 1000'lik parçalara bölünür

### Hayvan Sistemi
- **API'ler**: random.dog, thecatapi.com, randomfox.ca, random-d.uk
- **Fonksiyon Çağırma**: OpenAI function calling
- **Fallback**: Anahtar kelime tabanlı yönlendirme

### Duygu Sistemi
- **JSON Format**: İlk/ikinci duygu + cevap
- **Emoji Seçimi**: Rastgele seçim
- **Kalıcı Depolama**: JSON dosyaları

### İstatistik Sistemi
- **Veri Kaynağı**: data/chat_history.txt ve mood_counter.txt
- **Filtreleme**: Bugün/tüm zamanlar + isteğe bağlı duygu
- **Analiz**: Regex ile mesaj ayrıştırma
- **Bağımsız Akış**: Ayrı sistem olarak çalışır

### Frontend
- **Vanilla JS**: Framework yok
- **CSS Grid/Flexbox**: Modern layout
- **Canvas API**: Matrix efekti
- **SVG**: Halat animasyonları

---

## 🏗️ Modüler Mimari

### Dosya Yapısı
```
├── api_web_chatbot.py     # Ana koordinatör (LangChain entegrasyonu)
├── emotion_system.py      # Duygu analizi sistemi
├── animal_system.py       # Hayvan API sistemi (2. hafta)
├── rag_service.py         # RAG sistemi (4. hafta)
├── statistic_system.py    # İstatistik sistemi
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

---

## 🔒 Güvenlik Önlemleri

### Input Sanitization
- **HTML Escape**: Tüm kullanıcı girdileri HTML escape edilir
- **Tehlikeli Pattern Kontrolü**: Script injection, XSS, iframe injection vb. saldırıları önler
- **Regex Filtreleme**: JavaScript, VBScript, data URL'leri ve event handler'ları engeller

### Mesaj Uzunluk Sınırları
- **Ana Sistem**: 2000 karakter maksimum
- **Duygu Sistemi**: 1000 karakter maksimum  
- **Hayvan Sistemi**: 500 karakter maksimum
- **RAG Sistemi**: 1000 karakter maksimum

---

## 🎨 UI/UX Özellikleri

### Görsel Efektler
- **Yeşil Glow**: Duygu sistemi çalıştığında container kenarı
- **Düğüm Parlaması**: Aktif hayvan fonksiyonunda
- **Işın Animasyonu**: Düğümden chat kutusuna
- **Emoji Değişimi**: Yüz alanında dinamik emoji
- **Matrix Efekti**: Arka plan animasyonu

### Node Hiyerarşisi
- **Büyük Node'ler**: RAG, API, PLAIN
- **Küçük Node'ler**: Başlangıçta kapalı; tıklayınca açılır
- **Tek Hat**: Büyük node ile chat arasında tek ip
- **Renkli Parlama**: RAG=sarı, API=mavi, PLAIN=yeşil

---