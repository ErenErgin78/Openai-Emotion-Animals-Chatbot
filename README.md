# Animal & Emotion Chatbot (FastAPI)

Bu proje iki akışı birleştirir:
- Hayvan özellikleri: köpek/kedi/tilki/ördek için fotoğraf ve bilgi istekleri (7 fonksiyon).
- Duygu analizi: Kullanıcı mesajından duygu çıkarımı ve iki aşamalı yanıt.

LLM, kullanıcının mesajından hangi akışın çalışacağını seçer. Hayvan talebi varsa ilgili fonksiyon çağrılır; değilse duygu akışı devreye girer.

## Özellikler

- 🐶🐱🦊🦆 **Hayvan Fonksiyonları**: dog_photo, dog_facts, cat_photo, cat_facts, fox_photo, duck_photo, help_message
- 🔌 **LLM Yönlendirme**: Mesajdan niyeti algılar; hayvan talebinde fonksiyon çağırır, aksi halde duygu analizi yapar
- 💬 **Duygu Analizi**: İki aşamalı (ilk/ikinci duygu ve cevap), emoji desteği
- 📈 **İstatistikler**: "Bugün en çok..." gibi isteklerde sayımlar
- 🧠 **UI Eklentileri**: Yan panellerde sürüklenebilir fonksiyon düğümleri ve halat animasyonu
- ✨ **Görsel Efektler**: Aktif fonksiyonda düğüm/halat parlaması, node→chat ışın animasyonu; duygu akışında container kenarı yeşil parlayışı
- 🌗 **Tema** ve 🎞️ **Matrix** arkaplan, 📱 mobil uyum

---

## Proje Dosyaları

```
Duygusal-Ai-Openai/
  api_web_chatbot.py        # Ana uygulama (FastAPI, tüm akışlar)
  templates/
    index.html             # Web sayfası iskeleti (CSS/JS dışarı alındı)
  static/
    app.css                # Tüm stiller (yan paneller, halat, lightbox, tema)
    app.js                 # Tüm istemci JS (chat, yönlendirme, halat fiziği, animasyonlar)
  data/
    mood_emojis.json       # Duygu emojileri veritabanı
    chat_history.txt       # Konuşma geçmişi
    mood_counter.txt       # Duygu istatistikleri
  requirements.txt         # Gerekli Python paketleri
  .env                     # Gizli ayarlar (OpenAI API anahtarı)
  README.md               # Bu dosya
```

---

## Nasıl Çalışır?

### 1) Web Sunucusu
- Python ile çalışan web sunucusu
- Kullanıcı mesajlarını alır, OpenAI'ye gönderir, yanıt döner
- İki endpoint: ana sayfa (`/`) ve chat (`/chat`)

### 2) Yapay Zeka Motoru ve Yönlendirme
- OpenAI GPT-3.5-turbo (function calling) ile niyet tespiti
- Hayvan niyeti: 7 fonksiyondan biri çalışır ve sonuç JSON'u döner
- Değilse: duygu analizi için özel sistem promptu ile JSON döner (ilk/ikinci duygu+cevap)

### 3) Kullanıcı Arayüzü
- Yan paneller: sürüklenebilir fonksiyon düğümleri, halat ile `container` kenarına bağlı
- Düğme tıklama: yazma alanına otomatik prompt doldurur (örn. "Bana bir köpek fotoğrafı ver")
- Aktif fonksiyon: düğüm/halat yeşil parlayıp chat kutusuna ışın çizilir
- Duygu akışı: düğümler devreye girmez; `container` kenarı yeşil parlayarak çalışmayı gösterir
- Lightbox: Resme tıklandığında büyütme, kapatma ve indirme butonu
- Tema, Matrix efekti, mobil uyum

---

## Duygu Sistemi

Bot şu duyguları tanır ve analiz eder:

**Temel Duygular**: Mutlu, Üzgün, Öfkeli, Şaşkın, Utanmış, Endişeli, Gülümseyen, Flörtöz, Sorgulayıcı, Yorgun

---

## Emoji Veritabanı

Her duygu için özel emoji ve kaomoji (metin yüzler) koleksiyonu:

**Örnek**: Mutlu → 😊, 😄, ^_^, (◠‿◠)

Bot, her duygu için rastgele emoji seçer ve yüz alanında gösterir.

---

## Kullanım Örnekleri

### Normal Konuşma (Duygu Akışı)
- **Siz**: "Bugün çok mutluyum!"
- **Bot**: İlk aşama: "Mutlu: Harika! Bu güzel haberi duymak beni de mutlu ediyor."
- **Siz**: "Sonraki" butonuna basın
- **Bot**: İkinci aşama: "Gülümseyen: Bu pozitif enerjinizi koruyun!"

### İstatistik Sorguları
### Hayvan İstekleri
- "köpek fotoğrafı ver" → Köpek fotoğrafı döner, 🐶 düğümü/halatı yeşil parlar ve node→chat ışını oynar
- "kedi bilgisi ver" → Bir kedi bilgisi döner, 🐱 cat - facts düğümü yeşil parlar
- "tilki fotoğrafı ver" → Tilki fotoğrafı (redirect fixli), 🦊 düğümü yeşil
- **Siz**: "Bugün en çok hangi duyguyu yaşadım?"
- **Bot**: "Bugün 3 kez mutlu, 1 kez endişeli duygularınızı yaşadınız."

---

## Kurulum ve Çalıştırma

### 1. Gereksinimler
- Python 3.8+ yüklü olmalı
- OpenAI API anahtarı gerekli

### 2. Kurulum
```bash
# Gerekli paketleri yükle
pip install -r requirements.txt
```

### 3. API Anahtarı
`.env` dosyasını düzenleyin:
```
OPENAI_API_KEY=sk-your-api-key-here
```

### 4. Çalıştırma
```bash
# Sunucuyu başlat
python -m uvicorn api_web_chatbot:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Kullanım
Tarayıcınızda şu adresi açın:
```
http://localhost:8000/
```

Notlar
- `.env` içinde `OPENAI_API_KEY` yoksa anahtar kelimeye dayalı yönlendirme devreye girer.
- `static/` altındaki dosyalar otomatik servis edilir: `/static/app.css` ve `/static/app.js`.

### 6. Sanal Ortam (Önerilir)

Windows (PowerShell):
```powershell
# Proje klasörüne geç
cd <project_dir>

# Sanal ortam oluştur (isim serbest)
python -m venv <venv_name>

# Ortamı aktive et ve bağımlılıkları kur
./<venv_name>/Scripts/Activate.ps1
pip install -r requirements.txt
```

macOS / Linux:
```bash
# Proje klasörüne geç
cd <project_dir>

# Sanal ortam oluştur (isim serbest)
python3 -m venv <venv_name>

# Ortamı aktive et ve bağımlılıkları kur
source <venv_name>/bin/activate
pip install -r requirements.txt
```

Devre dışı bırakma:
```bash
deactivate
```