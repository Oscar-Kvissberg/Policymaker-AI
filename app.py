from flask import Flask, render_template, send_file, make_response, request, jsonify
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import logging
import json
import os

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')

@app.route('/download_empty_pdf')
def download_empty_pdf():
    logging.info("Försöker generera tom PDF")
    try:
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 100, "Detta är en tom PDF")
        p.showPage()
        p.save()
        buffer.seek(0)
        
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=empty.pdf'
        
        logging.info("PDF genererad och skickad framgångsrikt")
        return response
    except Exception as e:
        logging.error(f"Ett fel uppstod vid generering av PDF: {str(e)}")
        return "Ett fel uppstod vid generering av PDF", 500

@app.route('/policy', methods=['POST'])
def policy():
    name = request.form['name']
    club = request.form['club']
    position = request.form['position']
    
    # Läs JSON-filen för den valda klubben
    policy_file = os.path.join('Policies', f"{club}.json")
     
    try:
        with open(policy_file, 'r', encoding='utf-8') as f:
            policy_data = json.load(f)
    except FileNotFoundError:
        return f"Policy-fil för {club} hittades inte.", 404
    except json.JSONDecodeError:
        return f"Kunde inte läsa policy-filen för {club}. Kontrollera filformatet.", 400
    
    # Skicka policy_data till mallen istället för hela policies
    return render_template('policy.html', name=name, club=club, position=position, policy=policy_data)

@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())

@app.route('/skicka_email', methods=['POST'])
def skicka_email():
    app.logger.debug('skicka_email route called')
    # ... resten av din kod här ...

if __name__ == '__main__':
    app.run(debug=True)