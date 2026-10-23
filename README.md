# 🛡️ Babatassoft Kuantum Güvenlik Kasası (Quantum Security Vault)


Babatassoft Kuantum Güvenlik Kasası, klasik sözde-rastgele sayı üreteçlerinin (PRNG) zafiyetlerini ortadan kaldırarak **Kuantum Fiziği yasalarına dayalı mutlak rastgelelik (QRNG)** kullanan, donanım hızlandırmalı ve izole bir dosya şifreleme sistemidir.

Proje, NVIDIA CUDA-Q kütüphanesini kullanarak GPU (Örn: RTX 4050) üzerinde donanımsal kuantum devre simülasyonu yapar ve elde edilen kuantum entropisini, askeri sınıf AES-256-GCM algoritmasıyla harmanlar.

---

## 🚀 Temel Özellikler

### ⚛️ 1. Kuantum Rastgele Sayı Üretimi (QRNG)
Klasik şifreleme sistemleri formüllere (PRNG) dayanır ve geriye dönük hesaplanabilir. Babatassoft, **16 Qubit'lik bir kuantum devresi** oluşturur. Hadamard kapıları (H) ile süperpozisyona sokulan Qubit'lerin ölçüm anındaki (mz) evrensel çöküşü kullanılarak %100 saf, tahmin edilemez Kuantum Entropisi elde edilir.

### 🧩 2. Shamir's Secret Sharing (Nükleer Çanta Mantığı)
Oluşturulan 256-bit Kuantum Anahtarı, XOR tabanlı 2-of-3 parçalama algoritması ile 3 ayrı parçaya bölünür (`.part1`, `.part2`, `.part3`). Dosyanın şifresini çözmek için herhangi 2 yetkilinin (parçanın) yan yana gelmesi zorunludur. Tek parça ile kilit asla açılamaz.

### 💥 3. Kendi Kendini İmha (Anti-Brute Force)
Sistem, kilitli `.quantum` dosyalarının hash özetlerini (SHA-256) bellekte tutar. Brute-Force (Kaba Kuvvet) saldırılarına karşı, 3 kez hatalı veya eksik anahtar parçası girildiği an dosya kalıcı olarak **dijital mühürlenir**. Doğru anahtar sonradan bulunsa bile dosya kendini imha etmiş sayılır.

### 🔍 4. Dijital Bütünlük Koruması (HMAC)
AES-GCM (Galois/Counter Mode) algoritmasının doğrulama etiketleri sayesinde, `.quantum` uzantılı şifreli dosyanın içine ağ üzerinden taşınırken 1 byte'lık bile müdahale edilirse, sistem "Dijital Bütünlük İhlali" alarmı verir ve şifre çözme işlemini reddeder.

---

## 🧠 Teknik Mimari (Under the Hood)

Sistemin kalbindeki QRNG, NVIDIA'nın `cuda-quantum` (cudaq) kütüphanesi ile aşağıdaki çekirdek (kernel) üzerinde çalışır:

```python
@cudaq.kernel
def quantum_superposition_16():
    q = cudaq.qvector(16) # 16 Qubit tahsis edilir
    h(q)                  # Qubit'ler Süperpozisyona (Hem 0 Hem 1) sokulur
    mz(q)                 # Durum çökertilir ve mutlak entropi ölçülür
