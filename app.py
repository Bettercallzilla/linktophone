from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)

def extract_phone(text):
    match = re.search(r'(\+974\s?\d{4}\s?\d{4}|\b\d{4}\s?\d{4}\b)', text)
    return match.group(0) if match else None

def scrape_phone_number(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(5000)
        full_text = page.inner_text("body")
        phone = extract_phone(full_text)
        browser.close()
        return phone

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400
    try:
        phone = scrape_phone_number(url)
        return jsonify({"phone": phone or "Not found"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/scrape_bulk', methods=['POST'])
def scrape_bulk():
    data = request.json
    urls = data.get("urls", [])
    if not isinstance(urls, list) or not urls:
        return jsonify({"error": "Provide a list of URLs under 'urls' key"}), 400
    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for url in urls:
                page = browser.new_page()
                try:
                    page.goto(url, timeout=60000)
                    page.wait_for_timeout(5000)
                    text = page.inner_text("body")
                    phone = extract_phone(text)
                    results.append({"url": url, "phone": phone or "Not found"})
                except Exception as e:
                    results.append({"url": url, "error": str(e)})
                finally:
                    page.close()
            browser.close()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5965)
