from flask import Flask, request, jsonify
import requests
import fitz  # PyMuPDF
import os

SERPAPI_API_KEY ="c037fd318028673fd26d308e1fafb329a0eaf03e90b4882654a4e909fb850fef"

app = Flask(__name__)

def search_pdf_manual(title, language):
    base_url = "https://serpapi.com/search"

    # Étape 1 : Recherche sur les plateformes fiables
    query_priority = f"{title} filetype:pdf site:pdfdrive.com OR site:z-lib.io OR site:pdfcoffee.com"
    params_priority = {
        "q": query_priority,
        "engine": "google",
        "api_key": SERPAPI_API_KEY,
        "hl": language,
        "num": 10
    }
    response = requests.get(base_url, params=params_priority).json()
    results = response.get("organic_results", [])
    for r in results:
        link = r.get("link", "")
        if link.lower().endswith(".pdf"):
            return link

    # Étape 2 : Recherche générale si rien trouvé
    query_backup = f"{title} filetype:pdf"
    params_backup = {
        "q": query_backup,
        "engine": "google",
        "api_key": SERPAPI_API_KEY,
        "hl": language,
        "num": 10
    }
    response = requests.get(base_url, params=params_backup).json()
    results = response.get("organic_results", [])
    for r in results:
        link = r.get("link", "")
        if link.lower().endswith(".pdf"):
            return link

    return None

def analyze_pdf(pdf_url):
    r = requests.get(pdf_url)
    if r.status_code != 200:
        return None

    with open("temp.pdf", "wb") as f:
        f.write(r.content)

    doc = fitz.open("temp.pdf")
    num_pages = len(doc)
    has_color = False
    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n > 4:  # couleur
                has_color = True
                break
        if has_color:
            break

    doc.close()
    os.remove("temp.pdf")
    return num_pages, has_color

def calculate_price(num_pages, has_color):
    price = num_pages * 0.17 + 130
    if num_pages > 1000:
        price *= 2
    if has_color:
        price += 30
    return round(price, 2)

@app.route('/analyze-book', methods=['POST'])
def analyze_book():
    data = request.get_json()
    title = data.get("title")
    language = data.get("language", "en")

    if not title:
        return jsonify({"status": "error", "message": "Missing title"}), 400

    pdf_url = search_pdf_manual(title, language)
    if not pdf_url:
        return jsonify({"status": "error", "message": "No PDF found"}), 404

    result = analyze_pdf(pdf_url)
    if not result:
        return jsonify({"status": "error", "message": "Failed to analyze PDF"}), 500

    num_pages, has_color = result
    price = calculate_price(num_pages, has_color)

    return jsonify({
        "status": "success",
        "pdf_url": pdf_url,
        "num_pages": num_pages,
        "has_color_images": has_color,
        "calculated_price": price
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)


