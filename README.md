# AG5 Translator (Persian AI Subtitle Translator)

A specialized Python tool for translating technical subtitles (SRT) from English to Persian (Farsi), powered by Google Gemini (Pro/Flash).
Built with a focus on **technical accuracy**, **context awareness**, and **RTL direction correction**.

[فارسی](#راهنمای-فارسی) | [English](#english-guide)

---

## English Guide

### Features
- **Context-Aware Translation:** Translates in chunks (20 lines) to maintain context.
- **Strict Instruction Following:** Uses `instructions.md` to prevent translating technical terms (e.g., "RAG", "LangChain").
- **Glossary Support:** Enforces specific terminology via `glossary.json`.
- **RTL Fix (Nuclear Option):** Automatically wraps every Persian line with `RLE` (Right-to-Left Embedding) and `PDF` (Pop Directional Format) characters to ensure perfect display in players like PotPlayer/VLC mixed with English words.
- **Windows Friendly:** Saves as `UTF-8-SIG` (BOM) to prevent encoding issues on Windows players.

### Setup
1. **Install Python 3.10+**
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **API Key:**
   - Create a `.env` file (see `.env.example` if available) and add: `GEMINI_API_KEY=your_key_here`
   - Or pass it via command line.

### Usage
1. Place your `.srt` files in the `input/` folder.
2. Run the script:
   ```bash
   # Default (Uses Gemini 2.5 Pro for best quality)
   python main.py

   # Use a faster model
   python main.py --model gemini-2.0-flash
   ```
3. Find the translated files in `output/` folder.

---

## راهنمای فارسی

### معرفی
این ابزار برای ترجمه دقیق و تخصصی زیرنویس‌های انگلیسی به فارسی طراحی شده است. تمرکز اصلی روی حفظ کلمات تخصصی (مثل RAG, Embedding) و حل مشکل نمایش متون فارسی/انگلیسی در پلیرها است.

### ویژگی‌ها
- **ترجمه هوشمند:** زیرنویس‌ها را خط به خط ترجمه نمی‌کند، بلکه ۲۰ خط را همزمان می‌خواند تا معنی جملات ناقص را بفهمد.
- **حل مشکل راست‌چین (RTL):** به صورت خودکار کدهای نامرئی `RLE` را به خطوط اضافه می‌کند تا در PotPlayer و KMPlayer کلمات انگلیسی باعث بهم‌ریختگی جمله نشوند.
- **دیکشنری تخصصی:** با استفاده از فایل `glossary.json` می‌توانید تعیین کنید چه کلماتی ترجمه نشوند.
- **فرمت استاندارد:** خروجی `UTF-8-SIG` است که بهترین سازگاری را با ویندوز دارد.

### نصب و اجرا
۱. پایتون را نصب کنید.
۲. پیش‌نیازها را نصب کنید:
   ```bash
   pip install -r requirements.txt
   ```
۳. کلید API جمنای (Google Gemini) را در فایل `.env` قرار دهید.

### روش استفاده
۱. فایل‌های SRT انگلیسی را در پوشه `input` بریزید.
۲. دستور زیر را اجرا کنید:
   ```bash
   python main.py
   ```
۳. فایل ترجمه شده در پوشه `output` قرار می‌گیرد.
