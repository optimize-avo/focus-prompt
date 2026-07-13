# Design Spec: Focus-Prompt Tools Explanation

## Overview

Penjelasan detail cara kerja tools focus-prompt (CLI & MCP) dari awal sampai akhir, ditulis dalam bahasa non-teknis untuk presentasi ke stakeholders non-teknis.

## Context

- **Target audience**: Stakeholders non-teknis (manajemen, klien, tim marketing)
- **Tujuan**: Memahami bagaimana focus-prompt membantu brand mereka muncul di AI chatbot
- **Format**: Dokumen tertulis (Markdown/PDF)
- **Scope**: Lengkap - pipeline utama, konfigurasi, MCP server, semua fitur
- **Pendekatan**: Berdasarkan use case (Marketer/Brand Manager)

## Document Structure

### Bagian Pembuka
- Apa itu focus-prompt (1 kalimat)
- Mengapa penting untuk brand Anda

### Bagian Utama (Use Case: Marketer/Brand Manager)

#### 1. Persiapan - Setup Awal
- **Sub-step 1: Installasi focus-prompt**
  - Mengunduh dan memasang program
  - Perintah: `pipx install focus-prompt`
  - Menjelaskan dua bagian: `fp` (CLI) dan `fp-mcp` (MCP server)
  
- **Sub-step 2: Konfigurasi API Key**
  - Memilih provider AI (OpenAI, DeepSeek, MiniMax, dll)
  - Memasukkan API key
  - Penyimpanan di `~/.config/fp/config.env`
  - Sub-step 2.1: Pilih Provider (`fp setup`)
  - Sub-step 2.2: Verifikasi Konfigurasi (`fp status`)
  
- **Sub-step 3: Persiapan Proyek**
  - Membuat folder khusus
  - Penjelasan mengapa perlu isolasi proyek

#### 2. Memulai Proyek - Inisialisasi Brand
- **Sub-step 1: Menjalankan Perintah Init**
  - Perintah: `fp init "Nama Brand" --desc "Deskripsi" --url "https://brand.com" --services "service1,service2" --competitors "Kompetitor1,Kompetitor2"`
  - Sub-step 1.1: Input Data Brand (desc, url, services, competitors)
  - Sub-step 1.2: Pilih Mode (unbranded/branded/both)
  - Sub-step 1.3: Pilih Bahasa (id/en)
  
- **Sub-step 2: Apa yang Disimpan**
  - File `fp-project.json`
  - Penjelasan isi file
  - Mengapa penting

#### 3. Riset Awal - Mendapatkan Data dari Google
- **Sub-step 1: Menjalankan Perintah Research**
  - Perintah: `fp research`
  - Sub-step 1.1: Proses Pengambilan Data (Google Autocomplete)
  - Sub-step 1.2: Apa yang Didapat (daftar pertanyaan)
  
- **Sub-step 2: Validasi Data**
  - Perintah: `fp prompt-list`
  - Cara memeriksa relevansi data

#### 4. Penemuan Masalah - Apa yang Dicari Orang
- **Sub-step 1: Menjalankan Perintah Discover**
  - Perintah: `fp discover`
  - Sub-step 1.1: Proses Analisis AI
  - Sub-step 1.2: Apa yang Dihasilkan (daftar masalah)
  
- **Sub-step 2: Review Hasil**
  - Perintah: `fp focus-list`
  - Cara memeriksa relevansi masalah

#### 5. Clustering Fokus - Mengelompokkan Topik
- **Sub-step 1: Proses Clustering**
  - Penjelasan Apa itu Focus
  - Biasanya 4-8 topik besar
  - Sub-step 1.1: Apa itu Focus (kelompok topik terkait)
  - Sub-step 1.2: Informasi dalam Setiap Focus (nama, deskripsi, perspektif, sinyal, skor)
  
- **Sub-step 2: Review Focus**
  - Perintah: `fp focus-list`
  - Cara memeriksa pengelompokan

#### 6. Generate Prompt - Membuat Prompt untuk AI
- **Sub-step 1: Menjalankan Perintah Generate**
  - Perintah: `fp prompt-generate`
  - Sub-step 1.1: Proses Generate (AI membuat variasi)
  - Sub-step 1.2: Apa yang Dihasilkan (teks, intent, mode, bahasa)
  
- **Sub-step 2: Sanitasi Otomatis**
  - Perbaikan karakter non-Latin
  - Sub-step 2.1: Opsi Skip Sanitasi (`--no-sanitize`)
  
- **Sub-step 3: Review Prompt**
  - Perintah: `fp prompt-list`
  - Filter berdasarkan focus, mode, status review

#### 7. Skor Relevansi - Menilai Setiap Prompt
- **Sub-step 1: Menjalankan Perintah Score**
  - Perintah: `fp score`
  - Sub-step 1.1: Proses Penilaian (service_match, mention_likelihood, overall_score)
  - Sub-step 1.2: Klasifikasi Prioritas (high/medium/low)
  
- **Sub-step 2: Review Skor**
  - Perintah: `fp prompt-list`
  - Filter berdasarkan skor/prioritas
  - Penjelasan `needs_review: true`

#### 8. Export Hasil - Mengambil Data
- **Sub-step 1: Export JSON**
  - Perintah: `fp export json`
  - Sub-step 1.1: Apa yang Ada di JSON
  - Sub-step 1.2: Kapan Menggunakan JSON
  
- **Sub-step 2: Export CSV**
  - Perintah: `fp export csv`
  - Sub-step 2.1: Apa yang Ada di CSV
  - Sub-step 2.2: Kapan Menggunakan CSV

### Bagian Tambahan

#### 9. MCP Server - Integrasi dengan AI Editor
- **Sub-step 1: Konfigurasi MCP Server**
  - Contoh konfigurasi untuk OpenCode, Claude Code, Cursor
  - Sub-step 1.1: Contoh Konfigurasi untuk OpenCode
  - Sub-step 1.2: Setelah Konfigurasi (restart, tools tersedia)
  
- **Sub-step 2: Menggunakan MCP Server**
  - Menjalankan perintah melalui AI editor
  - Hasil sama dengan CLI

#### 10. Troubleshooting dan FAQ
- **Masalah Umum dan Solusi**
  1. Warning "API Key belum diset"
  2. Error saat connect ke AI provider
  3. Hasil tidak muncul setelah perintah
  4. Prompt mengandung karakter aneh
  
- **FAQ**
  1. Berapa biaya menggunakan focus-prompt?
  2. Bisa ganti provider di tengah jalan?
  3. Apakah data saya aman?
  4. Berapa lama proses analisis?

## Key Design Decisions

1. **Pendekatan Use Case**: Fokus pada skenario nyata Marketer/Brand Manager
2. **Bahasa Non-Teknis**: Menggunakan analogi sehari-hari (seperti "tiket masuk" untuk API key)
3. **Sub-step Detail**: Setiap langkah dipecah menjadi sub-step yang lebih kecil
4. **Contoh Perintah**: Menyertakan contoh perintah CLI yang sebenarnya
5. **Penjelasan "Mengapa"**: Setiap langkah dijelaskan mengapa penting

## Success Criteria

- [ ] Dokumen bisa dipahami oleh non-teknis tanpa bantuan
- [ ] Setiap langkah memiliki contoh perintah yang bisa dicoba
- [ ] Penjelasan cukup detail untuk presentasi 15-30 menit
- [ ] Termasuk troubleshooting untuk masalah umum
- [ ] Format konsisten di seluruh dokumen

## Out of Scope

- Detail teknis implementasi kode
- Perbandingan dengan tools lain
- Roadmap pengembangan mendatang
- Analisis kompetitor
