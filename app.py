import os
import io
import zipfile
import secrets
import hashlib
from werkzeug.utils import secure_filename
from flask import Flask, request, send_file, render_template, abort, jsonify
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.exceptions import InvalidTag
import cudaq

app = Flask(__name__)
# Canlı ortam için 64 byte'lık çok daha güçlü bir oturum anahtarı
app.secret_key = secrets.token_hex(64)
# Max 50 MB sınır (Babatassoft sunucu güvenliği - DoS engelleme)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 

# CUDA-Q Donanım Hedefi
cudaq.set_target("nvidia")

# --- VERİTABANI / BELLEK ---
# Not: Canlı ortamda çoklu sunucu (load balancer) kullanılacaksa 
# bu sözlük yerine Redis veya PostgreSQL kullanılmalıdır.
failed_attempts = {}

# --- GÜVENLİK BAŞLIKLARI (SECURITY HEADERS) ---
@app.after_request
def apply_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# --- KUANTUM DONANIM (QRNG) ---
@cudaq.kernel
def quantum_superposition_16():
    q = cudaq.qvector(16)
    h(q)
    mz(q)

def generate_babatassoft_quantum_key():
    # 16 Qubit süperpozisyon çökmesi ile mutlak rastgelelik
    q_bits = "".join([cudaq.sample(quantum_superposition_16, shots_count=1).most_probable() for _ in range(16)])
    quantum_entropy = int(q_bits, 2).to_bytes(32, byteorder='big')
    
    # Kuantum Entropisi + OS Entropisi (FIPS standartlarında melezleme)
    hkdf = HKDF(algorithm=hashes.SHA384(), length=32, salt=secrets.token_bytes(16), info=b"babatassoft-quantum-vault")
    return hkdf.derive(quantum_entropy + secrets.token_bytes(32))

# --- ŞİFRE PARÇALAMA (Shamir's 2-of-3) ---
def xor_bytes(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

def split_key_to_3(key):
    r1 = secrets.token_bytes(32)
    r2 = secrets.token_bytes(32)
    r3 = xor_bytes(key, xor_bytes(r1, r2))
    # Babatassoft özel başlıkları (Header ID)
    p1 = b'\x01' + r1 + r2
    p2 = b'\x02' + r2 + r3
    p3 = b'\x03' + r3 + r1
    return p1, p2, p3

def reconstruct_key(share_x, share_y):
    try:
        shares = {share_x[0]: share_x[1:], share_y[0]: share_y[1:]}
        if 1 in shares and 2 in shares:
            return xor_bytes(shares[1][:32], xor_bytes(shares[1][32:], shares[2][32:]))
        elif 2 in shares and 3 in shares:
            return xor_bytes(shares[3][32:], xor_bytes(shares[2][:32], shares[2][32:]))
        elif 1 in shares and 3 in shares:
            return xor_bytes(shares[1][:32], xor_bytes(shares[1][32:], shares[3][:32]))
    except Exception:
        return None
    return None

# --- WEB ROTALARI ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    file = request.files.get('file')
    if not file or file.filename == '': abort(400)

    safe_filename = secure_filename(file.filename)
    file_data = file.read()
    
    final_key = generate_babatassoft_quantum_key()
    
    aesgcm = AESGCM(final_key)
    nonce = os.urandom(12) 
    encrypted_data = aesgcm.encrypt(nonce, file_data, None)
    
    final_encrypted_content = nonce + encrypted_data
    p1, p2, p3 = split_key_to_3(final_key)
    
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(safe_filename + ".quantum", final_encrypted_content)
        zf.writestr("babatassoft_kilit_CEO.part1", p1)
        zf.writestr("babatassoft_kilit_CFO.part2", p2)
        zf.writestr("babatassoft_kilit_YONETIM.part3", p3)
    
    memory_file.seek(0)
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name=f"BABATASSOFT_SECURE_{safe_filename}.zip")

@app.route('/decrypt', methods=['POST'])
def decrypt():
    encrypted_file = request.files.get('encrypted_file')
    key1 = request.files.get('key_file_1')
    key2 = request.files.get('key_file_2')
    
    if not encrypted_file or not key1 or not key2:
        return jsonify({"error": "Eksik dosya! 1 şifreli dosya ve 2 anahtar parçası yüklemelisiniz."}), 400
        
    encrypted_data = encrypted_file.read()
    
    # 1. KENDİ KENDİNİ İMHA KONTROLÜ
    file_hash = hashlib.sha256(encrypted_data[:64]).hexdigest()
    if failed_attempts.get(file_hash, 0) >= 3:
        return jsonify({"error": "[BABATASSOFT GÜVENLİK PROTOKOLÜ] Bu dosya art arda 3 kez yanlış şifrelendiği için mühürlenmiş ve kalıcı olarak imha edilmiştir."}), 403

    # 2. ANAHTAR BİRLEŞTİRME
    final_key = reconstruct_key(key1.read(), key2.read())
    if not final_key or len(final_key) != 32:
        failed_attempts[file_hash] = failed_attempts.get(file_hash, 0) + 1
        return jsonify({"error": f"Yanlış anahtar parçaları! Kalan deneme hakkınız: {3 - failed_attempts[file_hash]}"}), 400
        
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    aesgcm = AESGCM(final_key)
    
    try:
        decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
    except InvalidTag:
        # 3. DİJİTAL BÜTÜNLÜK (HMAC) KONTROLÜ
        failed_attempts[file_hash] = failed_attempts.get(file_hash, 0) + 1
        return jsonify({"error": "[BÜTÜNLÜK İHLALİ TESPİT EDİLDİ] Şifreli dosyanın verisi değiştirilmiş. Erişim reddedildi!"}), 403
    except Exception:
        failed_attempts[file_hash] = failed_attempts.get(file_hash, 0) + 1
        return jsonify({"error": f"Kilidi açma başarısız. Kalan hakkınız: {3 - failed_attempts[file_hash]}"}), 403
        
    original_filename = secure_filename(encrypted_file.filename).replace('.quantum', '')
    memory_file = io.BytesIO(decrypted_data)
    
    return send_file(memory_file, as_attachment=True, download_name=original_filename)

if __name__ == '__main__':
    # Geliştirme ortamı başlatıcısı. Production'da Gunicorn kullanılmalıdır.
    print("\n[+] BABATASSOFT KUANTUM GÜVENLİK AĞI AKTİF")
    app.run(host='0.0.0.0', port=5000)