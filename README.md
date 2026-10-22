# Web Kelime Frekans Analizörü (Flask)

Bu proje, klavyeden girilen bir web sitesinin kök alan adına ait iç sayfalarını BFS (Breadth-First Search) algoritmasıyla dolaşır, HTML içerisindeki metinleri temizler (stop words ve anlamsız etiketleri filtreler) ve en çok kullanılan 10 kelimeyi grafiksel olarak sunar.

## Kurulum ve Çalıştırma

1. Sanal ortamınızı oluşturun ve aktif edin:
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS / Linux
   # veya: .\venv\Scripts\activate # Windows
   ```

2. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. Uygulamayı başlatın:
   ```bash
   python app.py
   ```

4. Tarayıcınızdan açın:
   `http://127.0.0.1:5000`
