# Babatassoft Quantum Security Vault (QSV)

**Babatassoft QSV**, klasik Pseudo-Random Number Generator (PRNG) zafiyetlerini son veren, NVIDIA GPU tabanlı Kuantum Rastgele Sayı Üreticisi (QRNG) destekli, yüksek güvenceli (high-assurance) bir dosya şifreleme ve erişim denetim servisidir. 

Proje, hassas verilerin korunması için Kuantum Entropisi, Eşik Kriptografisi (Threshold Cryptography) ve AEAD (Authenticated Encryption with Associated Data) standartlarını bir araya getirerek askeri sınıf bir veri izolasyonu sağlar.

---

## 🏗️ Sistem Mimarisi ve Kriptografik Protokoller

Sistem, veri güvenliğini sağlamak için uluslararası standartlarda kabul görmüş kriptografik primitifleri özel bir iş akışıyla birleştirir.

### 1. Donanım Hızlandırmalı Kuantum Entropi (QRNG)
Klasik işletim sistemi entropisine (/dev/urandom) güvenmek yerine, sistem **NVIDIA CUDA-Q** kütüphanesini kullanarak fiziksel donanım üzerinde gerçek zamanlı kuantum devre çökmesi simüle eder.
* **Mekanizma:** 16 Qubit'lik bir kuantum kaydı tahsis edilir. Hadamard ($H$) kapıları uygulanarak sistem deterministik olmayan bir süperpozisyona sokulur. Yapılan anlık Pauli-Z ölçümleri ($M_z$) ile kuantum durumu çökertilir ve mutlak (true) entropi elde edilir.
* **Key Derivation (KDF):** Kuantumdan elde edilen ham entropi, OS tabanlı entropi ile birleştirilerek **NIST SP 800-56C** standartlarına uygun `HKDF-SHA384` algoritmasından geçirilir ve 256-bit kriptografik anahtar türetilir.

### 2. AEAD ile Askeri Sınıf Şifreleme (AES-256-GCM)
Veri şifreleme aşamasında `AES-GCM` (Galois/Counter Mode) algoritması kullanılır.
* **Gizlilik:** 256-bit anahtar ve 96-bit (12-byte) güvenli Nonce kullanılarak veri şifrelenir.
* **Bütünlük:** GCM modunun doğası gereği oluşturulan 128-bit Authentication Tag (Doğrulama Etiketi) ciphertext'e entegre edilir. Şifreli dosya üzerinde yapılacak 1 bitlik manipulasyon bile yetkilendirme aşamasında `InvalidTag` exception fırlatarak işlemi reddeder.

### 3. XOR-Tabanlı Eşik Kriptografisi (2-of-3 Secret Sharing)
Tekil hata noktalarını (Single Point of Failure) önlemek amacıyla üretilen 256-bit nihai anahtar, XOR tabanlı parçalama algoritması ile 3 otonom parçaya (share) bölünür.
* Cipher key ($K$), rastgele üretilmiş $R_1$ ve $R_2$ vektörleri kullanılarak $R_3 = K \oplus R_1 \oplus R_2$ şeklinde türetilir.
* Yetki 3 farklı yöneticiye (CEO, CFO, CTO) `part1`, `part2`, `part3` formatında dağıtılır. Verinin şifresinin çözülmesi (reconstruction) için sisteme herhangi 2 parçanın eşzamanlı sunulması kriptografik bir zorunluluktur.

### 4. Stateful Anti-Brute Force (Self-Destruct)
Uygulama, payload başlıklarının (header) `SHA-256` hash'lerini in-memory veya persistence katmanında takip eder. Her dosya için maksimum 3 hatalı rekonstrüksiyon denemesine izin verilir. Limit aşıldığında hedef dosya hash'i sistemin kara listesine alınır ve kriptografik mühürleme kalıcı olarak reddedilir.

---

## ⚙️ Teknik Gereksinimler

Proje, Production (Canlı) ortam hedeflenerek containerize edilmiştir. Uygulamanın GPU-Pass-Through (Ekran kartı aktarımı) gereksinimi nedeniyle çıplak metal (bare-metal) yerine Docker üzerinden koşturulması zorunludur.

* **İşletim Sistemi:** Ubuntu 22.04 LTS / Debian 11 (Host OS) veya WSL2 (Windows)
* **Donanım:** NVIDIA GPU (Compute Capability 6.0+, Örn: RTX Serisi, Tesla, A100)
* **Sürücüler:** NVIDIA Display Driver v525.xx veya üzeri
* **Altyapı:** Docker Engine `24.0+` ve [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

---

## 🚀 Deployment (Kurulum)

Sistemi Gunicorn WSGI sunucusu üzerinden ayağa kaldırmak için aşağıdaki adımları izleyin.

**1. Repoyu Klonlayın:**
```bash
git clone [[https://github.com/babatassoft/quantum-security-vault.git](https://github.com/babatassoft/quantum-security-vault.git)](https://github.com/ozanbabatas59/Babatassoft-Kuantum-G-venlik-Kasas-Quantum-Security-Vault-.git)
cd quantum-security-vault
