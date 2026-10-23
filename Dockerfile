# Yapay zeka ve Kuantum kütüphaneleri için en stabil sürüm olan Python 3.10'a geçiyoruz
FROM python:3.10-slim

WORKDIR /app

# Gerekli C++ derleyicilerini kuruyoruz
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# ÇÖZÜM: Kütüphaneleri kurmadan önce pip, setuptools ve wheel araçlarını en güncel sürüme çekiyoruz
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Artık kütüphaneler güvenle ve hatasız kurulabilir
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]