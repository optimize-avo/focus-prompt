# Panduan Lengkap: Cara Kerja Focus-Prompt

## Apa itu Focus-Prompt?

Focus-prompt adalah tools AI yang membantu brand Anda muncul di chatbot seperti ChatGPT, Claude, atau Gemini. Tools ini memprediksi dan menghasilkan pertanyaan (prompt) yang mungkin diketip orang ke AI untuk menemukan brand seperti Anda.

## Mengapa Ini Penting untuk Brand Anda?

Bayangkan calon pelanggan Anda bertanya ke ChatGPT: "Apa rekomendasi layanan digital marketing yang bagus?" Jika brand Anda tidak muncul dalam jawaban ChatGPT, Anda kehilangan potensi pelanggan.

Focus-prompt membantu Anda:
1. Menemukan pertanyaan apa yang orang tanyakan tentang industri Anda
2. Membuat strategi agar brand Anda muncul dalam jawaban AI
3. Memahami bagaimana AI "melihat" brand Anda dibanding kompetitor

---

## Bagian 1: Persiapan - Setup Awal

Sebelum menggunakan focus-prompt, Anda perlu melakukan beberapa persiapan awal. Ibarat mau masak, kita perlu siapkan bahan-bahannya dulu.

### 1.1 Installasi focus-prompt

**Apa yang terjadi:**
Anda mengunduh dan memasang program focus-prompt ke komputer Anda. Program ini terdiri dari dua bagian:
- `fp`: Untuk perintah langsung dari terminal komputer
- `fp-mcp`: Untuk integrasi dengan AI editor seperti OpenCode atau Cursor

**Cara install:**
```bash
pipx install focus-prompt
```

**Mengapa perlu:**
Seperti memasang aplikasi baru di HP Anda. Setelah terpasang, Anda bisa menggunakan perintah `fp` dari terminal komputer.

**Tips:**
- Pastikan Anda sudah install `pipx` terlebih dahulu
- Jika sudah terinstall, Anda bisa update dengan: `pip install --upgrade focus-prompt`

### 1.2 Konfigurasi API Key

**Apa yang terjadi:**
Anda memilih provider AI yang akan digunakan dan memasukkan API key (seperti password untuk mengakses layanan AI).

**Cara setup:**
```bash
fp setup
```

**Langkah-langkah:**
1. Jalankan `fp setup`
2. Pilih provider dari daftar (1-9):
   - 1. OpenAI
   - 2. MiniMax (Singapore)
   - 3. DeepSeek
   - 4. Qwen/Alibaba
   - 5. MiMo (Singapore)
   - 6. Zhipu/GLM
   - 7. Moonshot/Kimi
   - 8. ByteDance/Doubao
   - 9. Tencent/Hunyuan
3. Masukkan API key yang sesuai
4. Config disimpan di `~/.config/fp/config.env`

**Mengapa perlu:**
focus-prompt perlu menghubungi layanan AI untuk menganalisis data. API key adalah "tiket masuk" untuk menggunakan layanan AI tersebut.

**Verifikasi:**
```bash
fp status
```
Pastikan tidak ada warning tentang API key yang belum diset.

### 1.3 Persiapan Proyek

**Apa yang terjadi:**
Anda membuat folder khusus untuk proyek focus-prompt. Di dalam folder ini, semua data dan hasil akan disimpan.

**Cara membuat:**
```bash
mkdir my-brand-focus
cd my-brand-focus
```

**Mengapa perlu:**
- Agar data tidak tercampur dengan proyek lain
- Memudahkan pengelolaan dan backup
- Setiap proyek bisa memiliki konfigurasi berbeda

---

## Bagian 2: Memulai Proyek - Inisialisasi Brand

Setelah persiapan selesai, saatnya mendaftarkan brand Anda ke dalam sistem focus-prompt.

### 2.1 Menjalankan Perintah Init

**Perintah:**
```bash
fp init "Nama Brand" \
  --desc "Deskripsi brand" \
  --url "https://brand.com" \
  --services "service1, service2" \
  --competitors "Kompetitor1, Kompetitor2" \
  --mode unbranded \
  --lang id
```

**Penjelasan parameter:**
- `--desc`: Menjelaskan apa yang brand Anda jual/layani
- `--url`: Website resmi brand Anda
- `--services`: Kategori layanan (misal: "digital marketing, SEO, content creation")
- `--competitors`: Siapa saja kompetitor utama Anda
- `--mode`: 
  - `unbranded`: Fokus pada prompt tanpa nama brand (paling umum)
  - `branded`: Fokus pada prompt yang menyebut nama brand
  - `both`: Keduanya
- `--lang`:
  - `id`: Bahasa Indonesia
  - `en`: Bahasa Inggris

**Contoh nyata:**
```bash
fp init "Tech Solutions Indonesia" \
  --desc "Perusahaan digital marketing yang membantu UMKM go online" \
  --url "https://techsolutions.co.id" \
  --services "digital marketing, SEO, social media management" \
  --competitors "Digital Agency XYZ, Marketing Pro, Online Success" \
  --mode unbranded \
  --lang id
```

### 2.2 Apa yang Disimpan

**Apa yang terjadi:**
Sistem membuat file `fp-project.json` di folder Anda. File ini berisi semua informasi brand yang Anda masukkan.

**Isi file:**
- Informasi brand (nama, deskripsi, website)
- Daftar layanan yang ditawarkan
- Daftar kompetitor
- Konfigurasi mode dan bahasa

**Mengapa penting:**
- Semua langkah selanjutnya akan menggunakan data dari file ini
- Anda bisa mengedit file ini kapan saja jika ada perubahan
- File ini seperti "profil" brand Anda di dalam focus-prompt

**Tips:**
- Backup file `fp-project.json` secara berkala
- Jika ingin mengubah informasi brand, edit file ini langsung

---
