from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from scraper import fetch_case_details
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    # Get form data
    case_type = request.form.get('case_type', '').strip()
    case_number = request.form.get('case_number', '').strip()
    filing_year = request.form.get('filing_year', '').strip()

    # Validate input
    if not all([case_type, case_number, filing_year]):
        flash('Please fill all fields', 'error')
        return redirect(url_for('home'))

    try:
        # Fetch and return data
        case_data = fetch_case_details(case_type, case_number, filing_year)
        return render_template('result.html', 
                            basic_info=case_data['basic_info'],
                            pdf_path=case_data['pdf_path'])
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('home'))

@app.route('/download_pdf/<filename>')
def download_pdf(filename):
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)