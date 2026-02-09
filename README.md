# AG5 Translator (Persian AI Subtitle Translator)

A specialized Python tool for translating technical subtitles (SRT) from English to Persian (Farsi), powered by Google Gemini. Built for AI researchers, engineers, and developers who need accurate technical translations with perfect RTL display.

[فارسی](#راهنمای-فارسی) | [English](#english-guide)

---

## English Guide

### 🚀 Key Features
- **Context-Aware Translation:** Processes 30 lines (approx. 2-3 minutes of video) per chunk to maintain coherent grammar and meaning.
- **RLE/PDF Sandwich (Industry Standard):** Automatically wraps every Persian line with `RLE` (\u202B) and `PDF` (\u202C) control characters. This prevents LTR words (like "Python" or "RAG") from flipping the sentence order in players like PotPlayer, VLC, or Plex.
- **ASR & Technical Correction:** Uses `glossary.json` and AI instructions to fix Speech-To-Text errors (e.g., `lama index` → `LlamaIndex`) and keeps technical terms in English.
- **Windows Optimized:** Saves files as `UTF-8 with BOM` (utf-8-sig) to ensure Windows Notepad and players detect Persian encoding correctly.

### 🛠️ Setup & Installation
1. **Install Python 3.10+**
2. **Clone/Download** this repository.
3. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure API Key:**
   - Create a `.env` file in the root directory.
   - Add your key: `GEMINI_API_KEY=your_google_ai_studio_key`
   - Get a free key at [Google AI Studio](https://aistudio.google.com/).

### 📖 Usage (Step-by-Step)
1. **Prepare:** Put your English `.srt` files into the `input/` folder.
2. **Translate:**
   ```bash
   # Default: Uses gemini-2.5-flash (Fast & Reliable)
   python main.py

   # Use High Quality:
   python main.py --model gemini-2.5-pro
   ```
3. **Collect:** Your translated file will appear in the `output/` folder.
4. **Customize:**
   - Edit `instructions.md` to change the translation tone.
   - Edit `glossary.json` to add new technical terms that shouldn't be translated.

---

## راهنمای فارسی

### 🇮🇷 معرفی ابزار
این ابزار یک مترجم هوشمند زیرنویس (SRT) است که مخصوص ویدیوهای تکنولوژی و برنامه‌نویسی طراحی شده. برخلاف مترجم‌های معمولی، این ابزار تفاوت بین کدهای برنامه‌نویسی و متن عادی را می‌فهمد و با استفاده از مدل‌های Gemini، ترجمه‌ای روان و دقیق ارائه می‌دهد.

### ✨ قابلیت‌های اصلی
- **درک متن (Context):** زیرنویس را تکه‌تکه (۳۰ خطی) ترجمه می‌کند تا جملاتی که در چند خط پخش شده‌اند، درست معنی شوند.
- **حل مشکل بهم‌ریختگی متن (RTL Fix):** از روش استاندارد `RLE/PDF Sandwich` استفاده می‌کند. این یعنی حتی اگر وسط جمله فارسی کلمه انگلیسی (مثل LlamaIndex) باشد، چیدمان جمله در پلیر (PotPlayer/VLC) بهم نمی‌خورد.
- **اصلاح خطاهای صوتی (ASR):** اگر در فایل اصلی اشتباه شنیداری وجود داشته باشد (مثلاً `land chain`), ابزار آن را به صورت هوشمند به (`LangChain`) اصلاح می‌کند.
- **سازگاری کامل با ویندوز:** فایل‌ها با فرمت `UTF-8 with BOM` ذخیره می‌شوند تا در تمام سیستم‌ها بدون مشکل فونت باز شوند.

### ⚙️ نصب و راه‌اندازی
۱. **پایتون:** مطمئن شوید پایتون ۳.۱۰ به بالا نصب است.
۲. **نصب پیش‌نیازها:**
   ```bash
   pip install -r requirements.txt
   ```
۳. **دریافت کلید API:**
   - یک فایل به نام `.env` بسازید.
   - کد `GEMINI_API_KEY=کد_شما` را داخل آن قرار دهید.
   - کلید رایگان را از [Google AI Studio](https://aistudio.google.com/) بگیرید.

### 🎯 آموزش استفاده گام‌به‌گام
۱. فایل‌های زیرنویس انگلیسی خود را در پوشه `input` کپی کنید.
۲. خط فرمان (Terminal/CMD) را باز کنید و دستور زیر را تایپ کنید:
   ```bash
   python main.py
   ```
۳. منتظر بمانید تا پیام `SUCCESS!` ظاهر شود.
۴. فایل ترجمه شده و آماده تماشا را از پوشه `output` بردارید.

### 💡 شخصی‌سازی
- **glossary.json:** کلماتی که نمی‌خواهید ترجمه شوند را در اینجا وارد کنید.
- **instructions.md:** می‌توانید به هوش مصنوعی بگویید لحن ترجمه چطور باشد (مثلاً خودمانی یا رسمی).
