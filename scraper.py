
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
from fpdf import FPDF
import os
from flask import Flask, send_file, abort

def fetch_case_details(case_type, case_number, filing_year):
    """Scrape all required case details from eCourts site with manual CAPTCHA"""
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options)

    try:
        driver.get("https://services.ecourts.gov.in/ecourtindia_v6/")
        print("\n" + "="*60)
        print(f"""MANUAL STEPS REQUIRED:
1. Select State/District/Court from dropdowns
2. Enter:
   - Case Type: {case_type}
   - Case Number: {case_number}
   - Year: {filing_year}
3. Solve CAPTCHA and click Submit
4. Return here and press ENTER""")
        print("="*60 + "\n")
        input("Press ENTER after submission...")

        # Wait for page to load with relevant data or invalid message
        WebDriverWait(driver, 30).until(
            lambda d: ("Invalid Request" not in d.page_source and (
                EC.presence_of_element_located((By.XPATH, 
                    "//*[contains(text(), 'Case Details')]"))(d) or
                EC.presence_of_element_located((By.XPATH,
                    "//*[contains(text(), 'Petitioner')]"))(d)
            ))
        )

        if "Invalid Request" in driver.page_source:
            raise Exception("Invalid request or CAPTCHA failed on site")

        # Extract details
        data = {
            'court_info': get_court_info(driver),
            'case_metadata': get_case_metadata(driver),
            'parties': get_parties_with_advocates(driver),
            'acts_sections': get_acts_sections(driver),
            'case_status': get_case_status(driver),
            'case_history': get_case_history(driver),
            'interim_orders': get_interim_orders(driver),
        }

        pdf_filename = f"case_{case_number}_{filing_year}.pdf"
        generate_complete_pdf(data, pdf_filename)

        return {
            'basic_info': {
                'court_info': data['court_info'],
                'parties': format_parties(data['parties']),
                'filing_date': data['case_metadata'].get('Filing Date', 'Not available'),
                'next_hearing': data['case_status'].get('Next Hearing Date', 'Not available'),
                'case_stage': data['case_status'].get('Case Stage', 'Not available'),
            },
            'full_details': data,
            'pdf_path': pdf_filename
        }

    except Exception as e:
        driver.save_screenshot('error.png')
        raise Exception(f"Error during scraping: {str(e)}")
    finally:
        driver.quit()


def get_court_info(driver):
    """Get Court name or info"""
    try:
        elem = driver.find_element(By.XPATH, "//h3[contains(text(),'Case Details')]/preceding-sibling::div | //div[contains(@class,'court-info')]")
        return elem.text.strip()
    except:
        # Try alternative location for court name (e.g. page header)
        try:
            return driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            return "Court information not available"


def get_case_metadata(driver):
    """Extract case type, filing number/date, registration no/date, CNR number etc."""
    metadata = {}
    try:
        table = driver.find_element(By.XPATH, "//h3[contains(text(),'Case Details')]/following-sibling::table[1] | //table[contains(@class,'case-details')]")
        rows = table.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            # Instead of assuming two cells per row, check pairs of cells
            i = 0
            while i < len(cells) - 1:
                key = cells[i].text.strip().rstrip(':')
                val = cells[i+1].text.strip()
                if key:
                    metadata[key] = val
                i += 2
    except:
        pass
    return metadata

def get_parties_with_advocates(driver):
    """Extract petitioners/respondents and advocates with fallback"""
    parties = {'petitioners': [], 'respondents': [], 'advocates': []}
    try:
        container = driver.find_element(By.XPATH, "//h3[contains(text(),'Petitioner and Advocate')]/following-sibling::div | //div[contains(@class,'party-info')]")
        # Petitioners
        try:
            petitioner_text = container.find_element(By.XPATH, ".//*[contains(text(),'Petitioner')]/following-sibling::*").text.strip()
            parties['petitioners'] = [line.strip() for line in petitioner_text.split('\n') if line.strip()]
        except:
            pass
        # Respondents
        try:
            respondent_text = container.find_element(By.XPATH, ".//*[contains(text(),'Respondent')]/following-sibling::*").text.strip()
            parties['respondents'] = [line.strip() for line in respondent_text.split('\n') if line.strip()]
        except:
            pass
        # Advocates - sometimes listed under each party or separately
        try:
            advocates_text = container.find_element(By.XPATH, ".//*[contains(text(),'Advocate')]/following-sibling::*").text.strip()
            parties['advocates'] = [line.strip() for line in advocates_text.split('\n') if line.strip()]
        except:
            pass
    except:
        # fallback: page wide search
        try:
            petitioners = driver.find_elements(By.XPATH, "//*[contains(text(),'Petitioner')]/following::td[1]")
            parties['petitioners'] = [p.text.strip() for p in petitioners if p.text.strip()]
        except:
            pass
        try:
            respondents = driver.find_elements(By.XPATH, "//*[contains(text(),'Respondent')]/following::td[1]")
            parties['respondents'] = [r.text.strip() for r in respondents if r.text.strip()]
        except:
            pass
    return parties


def get_acts_sections(driver):
    """Extract Acts and Sections table"""
    acts_sections = {}
    try:
        container = driver.find_element(By.XPATH, "//h3[contains(text(),'Acts')]/following-sibling::table | //table[contains(@class,'acts-sections')]")
        rows = container.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                act = cells[0].text.strip()
                section = cells[1].text.strip()
                acts_sections[act] = section
    except:
        pass
    return acts_sections


def get_case_status(driver):
    """Extract case status fields like First Hearing Date, Next Hearing Date, Case Stage, Court Number/Judge"""
    status = {}
    try:
        table = driver.find_element(By.XPATH, "//h3[contains(text(),'Case Status')]/following-sibling::table | //table[contains(@class,'case-status')]")
        rows = table.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                key = cells[0].text.strip().rstrip(':')
                val = cells[1].text.strip()
                status[key] = val
    except:
        pass
    return status


def get_case_history(driver):
    """Extract case history table"""
    history = []
    try:
        table = driver.find_element(By.XPATH, "//h3[contains(text(),'Case History')]/following-sibling::table | //table[contains(@class,'case-history')]")
        headers = [th.text.strip() for th in table.find_elements(By.TAG_NAME, "th")]
        for row in table.find_elements(By.TAG_NAME, "tr")[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) == len(headers):
                history.append({headers[i]: cells[i].text.strip() for i in range(len(headers))})
    except:
        pass
    return history


def get_interim_orders(driver):
    """Extract interim orders and their PDF links"""
    orders = []
    try:
        table = driver.find_element(By.XPATH, "//h3[contains(text(),'Interim Orders')]/following-sibling::table | //table[contains(@class,'interim-orders')]")
        headers = [th.text.strip() for th in table.find_elements(By.TAG_NAME, "th")]
        for row in table.find_elements(By.TAG_NAME, "tr")[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) == len(headers):
                order = {headers[i]: cells[i].text.strip() for i in range(len(headers))}
                try:
                    link = row.find_element(By.TAG_NAME, "a").get_attribute('href')
                    order['pdf_link'] = link
                except:
                    order['pdf_link'] = None
                orders.append(order)
    except:
        pass
    return orders


def format_parties(parties):
    """Format parties and advocates for display"""
    formatted = []
    if parties.get('petitioners'):
        formatted.append("PETITIONERS:\n" + "\n".join(parties['petitioners']))
    if parties.get('respondents'):
        formatted.append("RESPONDENTS:\n" + "\n".join(parties['respondents']))
    if parties.get('advocates'):
        formatted.append("ADVOCATES:\n" + "\n".join(parties['advocates']))
    return "\n\n".join(formatted) if formatted else "Parties information not found"


def generate_complete_pdf(data, filename):
    """Generate PDF including all extracted details"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "eCourts Case Details Report", ln=1, align='C')
    pdf.ln(5)

    # Court Info
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Court Information", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, data.get('court_info', 'Not available'))
    pdf.ln(5)

    # Case Metadata
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Case Details", ln=1)
    pdf.set_font("Arial", size=12)
    for key, val in data.get('case_metadata', {}).items():
        pdf.cell(50, 10, f"{key}:", ln=0)
        pdf.cell(0, 10, val, ln=1)
    pdf.ln(5)

    # Parties
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Parties and Advocates", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, format_parties(data.get('parties', {})))
    pdf.ln(5)

    # Acts and Sections
    acts_sections = data.get('acts_sections', {})
    if acts_sections:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Acts and Sections", ln=1)
        pdf.set_font("Arial", size=12)
        for act, section in acts_sections.items():
            pdf.cell(0, 10, f"{act} - {section}", ln=1)
        pdf.ln(5)

    # Case Status
    case_status = data.get('case_status', {})
    if case_status:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Case Status", ln=1)
        pdf.set_font("Arial", size=12)
        for key, val in case_status.items():
            pdf.cell(50, 10, f"{key}:", ln=0)
            pdf.cell(0, 10, val, ln=1)
        pdf.ln(5)

    # Case History Table
    case_history = data.get('case_history', [])
    if case_history:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Case History", ln=1)
        pdf.set_font("Arial", size=10)
        headers = list(case_history[0].keys())
        col_width = pdf.w / len(headers) - 10
        # Header row
        pdf.set_fill_color(200, 220, 255)
        for header in headers:
            pdf.cell(col_width, 8, header, border=1, fill=True)
        pdf.ln()
        # Data rows
        pdf.set_fill_color(255, 255, 255)
        for row in case_history:
            for header in headers:
                pdf.cell(col_width, 8, row.get(header, ''), border=1)
            pdf.ln()
        pdf.ln(5)

    # Interim Orders Table
    interim_orders = data.get('interim_orders', [])
    if interim_orders:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Interim Orders", ln=1)
        pdf.set_font("Arial", size=10)
        headers = [h for h in interim_orders[0].keys() if h != 'pdf_link']
        col_width = pdf.w / len(headers) - 10
        # Header row
        pdf.set_fill_color(200, 220, 255)
        for header in headers:
            pdf.cell(col_width, 8, header, border=1, fill=True)
        pdf.ln()
        # Data rows
        pdf.set_fill_color(255, 255, 255)
        for order in interim_orders:
            for header in headers:
                pdf.cell(col_width, 8, order.get(header, ''), border=1)
            pdf.ln()
    pdf.output(filename)


# --- Example Flask route to serve PDF file for download ---
app = Flask(__name__)

@app.route('/download/<case_number>/<filing_year>')
def download_pdf(case_number, filing_year):
    pdf_path = f"case_{case_number}_{filing_year}.pdf"
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    else:
        abort(404, description="PDF file not found")