import re
from collections import Counter, deque
from urllib.parse import urljoin, urldefrag, urlparse
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

STOP_WORDS = {
    "ve", "veya", "ile", "bu", "şu", "o", "bir", "için", "de", "da", "ki",
    "en", "daha", "çok", "gibi", "kadar", "her", "ama", "fakat", "ancak",
    "ise", "mu", "mi", "mı", "mü", "ya", "ne", "hem", "diye", "the", "and",
    "to", "of", "a", "in", "for", "is", "on", "that", "by", "this", "with",
    "i", "you", "it", "not", "or", "be", "are", "from", "at", "as", "your",
    "all", "have", "new", "more", "an", "was", "we", "will"
}


def normalize_domain(netloc: str) -> str:
    """Alan adı önündeki www. önekini temizleyerek standart domain oluşturur."""
    netloc = netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def siteyi_tara(baslangic_url: str, max_sayfa: int = 20):
    """
    Belirtilen web sitesinden başlayarak iç sayfaları gezer (BFS) ve 
    en sık kullanılan kelimelerin frekansını hesaplar.
    """
    if not baslangic_url.startswith(("http://", "https://")):
        baslangic_url = "https://" + baslangic_url

    parsed_baslangic = urlparse(baslangic_url)
    kok_domain = normalize_domain(parsed_baslangic.netloc)

    if not kok_domain:
        return {"error": "Geçerli bir alan adı girilmedi."}

    kuyruk = deque([baslangic_url])
    ziyaret_edilen = set()
    kelime_sayaci = Counter()

    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    sayfa_sayisi = 0

    while kuyruk and sayfa_sayisi < max_sayfa:
        mevcut_url = kuyruk.popleft()
        temiz_url, _ = urldefrag(mevcut_url)

        if temiz_url in ziyaret_edilen:
            continue

        try:
            response = session.get(temiz_url, headers=headers, timeout=6)
            ziyaret_edilen.add(temiz_url)

            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type or response.status_code != 200:
                continue

            sayfa_sayisi += 1
        except requests.exceptions.RequestException:
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        # Görünmeyen / anlamsız etiketleri temizle
        for element in soup(["script", "style", "noscript", "meta", "header", "footer"]):
            element.decompose()

        sayfa_metni = soup.get_text(separator=" ", strip=True).lower()
        kelimeler = re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]{3,}", sayfa_metni)

        for k in kelimeler:
            if k not in STOP_WORDS:
                kelime_sayaci[k] += 1

        # Sayfadaki iç bağlantıları tara
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue

            tam_url = urljoin(temiz_url, href)
            hedef_temiz, _ = urldefrag(tam_url)
            parsed_hedef = urlparse(hedef_temiz)

            if parsed_hedef.scheme not in ("http", "https"):
                continue

            hedef_domain = normalize_domain(parsed_hedef.netloc)

            if hedef_domain == kok_domain and hedef_temiz not in ziyaret_edilen:
                # İndirilebilir dosyaları ve medyayı atla
                if not re.search(r"\.(pdf|jpg|jpeg|png|gif|zip|rar|tar|gz|mp4|mp3|exe|svg)$", parsed_hedef.path.lower()):
                    kuyruk.append(hedef_temiz)

    top_10 = kelime_sayaci.most_common(10)
    return {
        "success": True,
        "domain": kok_domain,
        "taranan_sayfa": sayfa_sayisi,
        "kelimeler": [{"kelime": k, "adet": c} for k, c in top_10],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analiz-et", methods=["POST"])
def analiz_et():
    data = request.get_json() or {}
    hedef_url = data.get("url", "").strip()
    max_sayfa = data.get("max_sayfa", 15)

    try:
        max_sayfa = int(max_sayfa)
        max_sayfa = max(1, min(max_sayfa, 50))
    except (ValueError, TypeError):
        max_sayfa = 15

    if not hedef_url:
        return jsonify({"success": False, "error": "Lütfen bir URL girin."}), 400

    sonuclar = siteyi_tara(hedef_url, max_sayfa=max_sayfa)
    if "error" in sonuclar:
        return jsonify({"success": False, "error": sonuclar["error"]}), 400

    return jsonify(sonuclar)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
