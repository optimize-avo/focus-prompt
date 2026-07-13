# Panduan Lengkap: Cara Kerja Focus-Prompt

## Daftar Isi

1. [Apa itu Focus-Prompt?](#apa-itu-focus-prompt)
2. [Mengapa Ini Penting untuk Brand Anda?](#mengapa-ini-penting-untuk-brand-anda)
3. [Bagian 1: Persiapan - Setup Awal](#bagian-1-persiapan---setup-awal)
4. [Bagian 2: Memulai Proyek - Inisialisasi Brand](#bagian-2-memulai-proyek---inisialisasi-brand)
5. [Bagian 3: Riset Awal - Mendapatkan Data dari Google](#bagian-3-riset-awal---mendapatkan-data-dari-google)
6. [Bagian 4: Penemuan Masalah - Apa yang Dicari Orang](#bagian-4-penemuan-masalah---apa-yang-dicari-orang)
7. [Bagian 5: Clustering Fokus - Mengelompokkan Topik](#bagian-5-clustering-fokus---mengelompokkan-topik)
8. [Bagian 6: Generate Prompt - Membuat Prompt untuk AI](#bagian-6-generate-prompt---membuat-prompt-untuk-ai)
9. [Bagian 7: Skor Relevansi - Menilai Setiap Prompt](#bagian-7-skor-relevansi---menilai-setiap-prompt)
10. [Bagian 8: Export Hasil - Mengambil Data](#bagian-8-export-hasil---mengambil-data)
11. [Bagian 9: MCP Server - Integrasi dengan AI Editor](#bagian-9-mcp-server---integrasi-dengan-ai-editor)
12. [Bagian 10: Troubleshooting dan FAQ](#bagian-10-troubleshooting-dan-faq)

---

## Apa itu Focus-Prompt?

Focus-prompt adalah tools AI yang membantu brand Anda muncul di chatbot seperti ChatGPT, Claude, atau Gemini. Tools ini memprediksi dan menghasilkan pertanyaan (prompt) yang mungkin diketik orang ke AI untuk menemukan brand seperti Anda.

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
- Jika sudah terinstall, Anda bisa update dengan: `pipx upgrade focus-prompt`

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

## Bagian 3: Riset Awal - Mendapatkan Data dari Google

Sekarang saatnya mengumpulkan pertanyaan nyata yang orang ketik di Google tentang industri Anda.

### 3.1 Menjalankan Perintah Research

**Perintah:**
```bash
fp research
```

**Apa yang terjadi:**
1. Sistem mengirim query ke Google Autocomplete
2. Google mengembalikan saran lengkapan otomatis
3. Data dikumpulkan dan disimpan

**Apa yang didapat:**
- Daftar pertanyaan yang sering dicari orang
- Variasi dari pertanyaan tersebut
- Data ini menjadi bahan untuk langkah selanjutnya

**Contoh hasil:**
Jika industri Anda "digital marketing", mungkin akan muncul:
- "cara digital marketing untuk pemula"
- "jasa digital marketing terbaik"
- "biaya digital marketing"
- "tips digital marketing 2026"

### 3.2 Validasi Data

**Perintah:**
```bash
fp prompt-list
```

**Cara memeriksa:**
- Pastikan data yang masuk relevan dengan industri Anda
- Periksa apakah ada data yang aneh atau tidak relevan
- Jika ada masalah, Anda bisa mengulang riset

**Tips:**
- Riset ini menggunakan data real dari Google
- Semakin banyak data, semakin akurat analisis selanjutnya

---

## Bagian 4: Penemuan Masalah - Apa yang Dicari Orang

Sekarang saatnya menganalisis pertanyaan-pertanyaan tadi untuk menemukan masalah nyata yang dihadapi orang.

### 4.1 Menjalankan Perintah Discover

**Perintah:**
```bash
fp discover
```

**Apa yang terjadi:**
1. Sistem mengirim data riset ke AI (LLM) untuk analisis
2. AI menganalisis semua pertanyaan
3. AI mengidentifikasi masalah-masalah utama
4. AI mengelompokkan masalah berdasarkan kategori

**Apa yang dihasilkan:**
- Daftar masalah yang ditemukan
- Penjelasan singkat tentang setiap masalah
- Kategori atau topik terkait

**Contoh hasil:**
Jika industri Anda "digital marketing", mungkin akan muncul masalah:
1. "Kesulitan mendapatkan leads berkualitas"
2. "Budget marketing terbatas"
3. "Tidak tahu cara mengukur ROI"
4. "Kompetitor lebih agresif di digital"

### 4.2 Review Hasil

**Perintah:**
```bash
fp focus-list
```

**Cara memeriksa:**
- Periksa apakah masalah-masalah yang ditemukan relevan
- Pastikan tidak ada masalah yang terlewat
- Jika ada masalah yang kurang tepat, bisa diulang

**Tips:**
- Masalah yang ditemukan akan menjadi dasar untuk generate prompt
- Semakin akurat masalah, semakin relevan prompt yang dihasilkan

---

## Bagian 5: Clustering Fokus - Mengelompokkan Topik

Sekarang saatnya mengelompokkan masalah-masalah tadi menjadi topik-topik besar yang saling terkait.

### 5.1 Apa itu Focus

**Penjelasan:**
Focus adalah kelompok topik yang saling terkait. Biasanya menghasilkan 4-8 topik besar.

**Contoh:**
Jika industri Anda "digital marketing", mungkin akan muncul focus:
1. "Content Marketing Strategy"
2. "SEO Optimization"
3. "Social Media Management"
4. "Paid Advertising"
5. "Email Marketing"

### 5.2 Informasi dalam Setiap Focus

**Setiap focus berisi:**
- **Nama focus**: Topik utama (misal: "Content Marketing Strategy")
- **Deskripsi**: Penjelasan singkat tentang topik ini
- **Perspektif**: Sudut pandang atau pendekatan
- **Sinyal**: Ciri khas atau tanda-tanda
- **Skor kecocokan**: Seberapa cocok dengan layanan Anda

### 5.3 Review Focus

**Perintah:**
```bash
fp focus-list
```

**Cara memeriksa:**
- Periksa apakah pengelompokan sudah tepat
- Pastikan setiap focus memiliki deskripsi yang jelas
- Jika ada focus yang kurang tepat, bisa diulang

---

## Bagian 6: Generate Prompt - Membuat Prompt untuk AI

Sekarang saatnya membuat pertanyaan-pertanyaan yang mungkin diketik orang ke AI chatbot.

### 6.1 Menjalankan Perintah Generate

**Perintah:**
```bash
fp prompt-generate
```

**Apa yang terjadi:**
1. AI membuat berbagai variasi pertanyaan untuk setiap focus
2. Setiap prompt memiliki intent yang berbeda
3. Prompt bisa unbranded atau branded

**Apa yang dihasilkan:**
- Daftar prompt untuk setiap focus
- Setiap prompt memiliki:
  - **Teks pertanyaan**: Pertanyaan yang sebenarnya
  - **Intent**: Tujuan dari pertanyaan (misal: "membandingkan", "mencari solusi")
  - **Mode**: Unbranded atau branded
  - **Bahasa**: Indonesia atau Inggris

**Contoh hasil:**
Untuk focus "Content Marketing Strategy":
- "Bagaimana cara membuat konten yang menarik untuk bisnis?" (unbranded)
- "Apa keunggulan Tech Solutions dalam content marketing?" (branded)

### 6.2 Sanitasi Otomatis

**Apa yang terjadi:**
Sistem secara otomatis memperbaiki karakter non-Latin (misal: karakter Cina/Arab) menjadi Latin menggunakan AI untuk mengganti karakter dengan padanan yang tepat dalam konteks kalimat, bukan sekadar penggantian karakter satu-ke-satu.

**Mengapa perlu:**
Memastikan prompt bisa digunakan di platform manapun tanpa masalah encoding.

**Opsi skip sanitasi:**
```bash
fp prompt-generate --no-sanitize
```
Gunakan ini jika ingin prompt tetap dalam bahasa asli.

### 6.3 Review Prompt

**Perintah:**
```bash
fp prompt-list
```

**Filter yang tersedia:**
- `--focus`: Filter berdasarkan focus tertentu
- `--mode`: Filter unbranded/branded
- `--review`: Filter yang perlu review manual

**Tips:**
- Review prompt yang menandai `needs_review: true`
- Pastikan prompt sudah sesuai dengan brand voice Anda

---

## Bagian 7: Skor Relevansi - Menilai Setiap Prompt

Sekarang saatnya menilai seberapa relevan dan berpotensi menyebut brand Anda setiap prompt.

### 7.1 Menjalankan Perintah Score

**Perintah:**
```bash
fp score
```

**Apa yang terjadi:**
1. Sistem mengirim setiap prompt ke AI untuk penilaian
2. AI menilai berdasarkan beberapa kriteria
3. Skor dan prioritas ditentukan

**Kriteria penilaian:**
1. **Service Match**: Seberapa cocok dengan layanan Anda
2. **Mention Likelihood**: Kemungkinan prompt ini menyebut brand Anda
3. **Overall Score**: Skor keseluruhan (dihitung dari kombinasi Service Match dan Mention Likelihood)

**Catatan:** Jika skor Service Match rendah (<40), prompt akan ditandai `needs_review: true` untuk review manual.

**Klasifikasi prioritas:**
- **High**: Prompt yang sangat relevan (skor kecocokan layanan ≥75)
- **Medium**: Prompt yang cukup relevan (skor kecocokan layanan ≥55)
- **Low**: Prompt yang kurang relevan (skor kecocokan layanan <55)

### 7.2 Review Skor

**Perintah:**
```bash
fp prompt-list
```

**Filter yang berguna:**
- Filter berdasarkan skor atau prioritas
- Perhatikan prompt yang menandai `needs_review: true`

**Tips:**
- Fokus pada prompt dengan skor "High" terlebih dahulu
- Review prompt yang membutuhkan review manual
- Gunakan skor untuk memprioritaskan action items

---

## Bagian 8: Export Hasil - Mengambil Data

Sekarang saatnya mengambil hasil analisis dalam format yang bisa digunakan.

### 8.1 Export JSON

**Perintah:**
```bash
fp export json
```

**Apa yang dihasilkan:**
File JSON berisi semua data:
- Informasi brand
- Semua focus dengan deskripsi
- Semua prompt dengan skor
- Metadata proyek

**Kapan menggunakan JSON:**
- Untuk integrasi dengan sistem lain
- Untuk backup data
- Untuk analisis lebih lanjut dengan tools lain

### 8.2 Export CSV

**Perintah:**
```bash
fp export csv
```

**Apa yang dihasilkan:**
File CSV yang bisa dibuka di Excel/Google Sheets:
- Baris per prompt
- Kolom: focus, focus_priority, prompt, mode, intent, language, service_match, mention_likelihood, overall_score, needs_review

**Kapan menggunakan CSV:**
- Untuk analisis di Excel/Google Sheets
- Untuk dibagikan ke tim
- Untuk presentasi

**Tips:**
- CSV lebih mudah dianalisis di spreadsheet
- JSON lebih fleksibel untuk integrasi sistem
- Keduanya bisa digunakan sesuai kebutuhan

---

## Bagian 9: MCP Server - Integrasi dengan AI Editor

Focus-prompt bisa dijalankan sebagai MCP server — terintegrasi langsung di AI editor seperti OpenCode, Claude Code, atau Cursor.

### 9.1 Konfigurasi MCP Server

**Untuk OpenCode:**
Tambahkan di `~/.config/opencode/opencode.jsonc`:
```json
{
  "mcp": {
    "focus-prompt": {
      "type": "local",
      "command": ["fp-mcp"],
      "env": {
        "FP_MODEL": "minimax/MiniMax-M2.1",
        "MINIMAX_API_KEY": "your-key-here"
      }
    }
  }
}
```

**Untuk Claude Code:**
Tambahkan di `.claude/settings.json` (project-level) atau `~/.claude.json` (global):
```json
{
  "mcpServers": {
    "focus-prompt": {
      "command": "fp-mcp",
      "env": {
        "FP_MODEL": "minimax/MiniMax-M2.1",
        "MINIMAX_API_KEY": "your-key-here"
      }
    }
  }
}
```

**Untuk Cursor:**
Tambahkan di `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "focus-prompt": {
      "command": "fp-mcp",
      "env": {
        "FP_MODEL": "minimax/MiniMax-M2.1",
        "MINIMAX_API_KEY": "your-key-here"
      }
    }
  }
}
```

### 9.2 Setelah Konfigurasi

**Langkah:**
1. Restart AI editor
2. Sekarang Anda bisa menggunakan tools focus-prompt langsung dari AI editor
3. Tools yang tersedia:
   - `fp_init`: Init brand project
   - `fp_research`: Fetch real queries dari Google Autocomplete
   - `fp_discover`: Problem discovery + focus clustering
   - `fp_generate_prompts`: Generate prompt variants
   - `fp_score`: Score prompts
   - `fp_export`: Export data
   - `fp_status`: Project status

### 9.3 Menggunakan MCP Server

**Cara penggunaan:**
- Anda bisa menjalankan semua perintah focus-prompt melalui AI editor
- AI editor akan menggunakan fp-mcp sebagai backend
- Hasilnya sama persis dengan menggunakan CLI

**Keuntungan:**
- Tidak perlu buka terminal terpisah
- Bisa langsung dari AI editor yang sudah Anda gunakan
- Lebih integrasi dengan workflow development

---

## Bagian 10: Troubleshooting dan FAQ

### 10.1 Masalah Umum dan Solusi

**1. Warning "API Key belum diset"**
- **Solusi:** Jalankan `fp setup` lagi dan pastikan API key benar
- **Cek:** Jalankan `fp status` untuk melihat warning lengkap

**2. Error saat connect ke AI provider**
- **Solusi:**
  - Cek koneksi internet
  - Pastikan API key masih valid
  - Coba provider lain
  - Periksa kuota API Anda

**3. Hasil tidak muncul setelah perintah**
- **Solusi:**
  - Jalankan `fp status` untuk cek status proyek
  - Pastikan sudah menjalankan langkah sebelumnya secara berurutan
  - Periksa apakah ada error message

**4. Prompt mengandung karakter aneh**
- **Solusi:**
  - Jalankan `fp prompt-generate` lagi (otomatis sanitasi)
  - Atau gunakan `--no-sanitize` jika ingin tetap asli

### 10.2 FAQ

**Q: Berapa biaya menggunakan focus-prompt?**
A: Gratis untuk tool-nya. Biaya hanya dari penggunaan API AI (tergantung provider dan jumlah penggunaan).

**Q: Bisa ganti provider di tengah jalan?**
A: Bisa. Jalankan `fp setup` lagi dan pilih provider baru. Data lama tetap tersimpan.

**Q: Apakah data saya aman?**
A: Ya. Data tersimpan lokal di komputer Anda. Tidak ada data yang dikirim ke server kami.

**Q: Berapa lama proses analisis?**
A: Tergantung jumlah data dan provider AI. Biasanya 1-5 menit per langkah.

**Q: Bisa digunakan untuk beberapa brand sekaligus?**
A: Bisa. Buat folder terpisah untuk setiap brand dan jalankan `fp init` di masing-masing folder.

---
