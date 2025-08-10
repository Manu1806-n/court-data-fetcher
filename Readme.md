## Project Title

Court-Data Fetcher & Mini-Dashboard

⸻

## Demo Video

Watch the working demo of the Court-Data Fetcher here:  
[![Demo Video](https://img.youtube.com/vi/wS4zEtfzBoc/0.jpg)](https://youtu.be/wS4zEtfzBoc)

⸻

## Court Website Targeted

This project targets the Faridabad District Court eCourts portal at:
https://districts.ecourts.gov.in

⸻

## Objective

A Flask-based web app to input Case Type, Case Number, and Filing Year, scrape case metadata and latest orders from the court’s public site, display results, and allow downloading a PDF report.

⸻

## Features
	•	Simple and user-friendly web UI with dropdown for Case Type
	•	Selenium-based backend scraper with manual CAPTCHA handling
	•	Parses parties, filing & hearing dates, case status, interim orders with PDF links
	•	Stores query logs in SQLite
	•	Generates downloadable PDF report with complete case details
	•	User-friendly error handling for invalid cases or site issues

⸻

## Setup & Installation

Prerequisites
	•	Python 3.8+
	•	Google Chrome installed
	•	ChromeDriver or undetected-chromedriver (preferred) installed

Install dependencies

    pip install -r requirements.txt

    (requirements.txt includes Flask, selenium, undetected-chromedriver, fpdf, etc.)

Running the app

    python app.py

## CAPTCHA Handling

The court site uses CAPTCHA to prevent automated scraping. This app opens a Chrome window for manual CAPTCHA input. Steps:
	1.	The browser window will open to the court’s case search page.
	2.	Select State, District, and Court manually.
	3.	Enter Case Type, Case Number, and Filing Year as per the form.
	4.	Solve the CAPTCHA shown and submit the form manually.
	5.	Return to the terminal and press ENTER to continue scraping.

This manual step ensures compliance with the site’s terms and avoids automated CAPTCHA solving.

⸻

## Usage
	•	Open the web app in your browser at http://127.0.0.1:5000/
	•	Select Case Type from dropdown, enter Case Number and Filing Year
	•	Click Search
	•	Complete manual CAPTCHA in the opened browser window as instructed
	•	View parsed case details on the results page
	•	Download detailed PDF report if needed

⸻

## Notes
	•	Only Faridabad District Court is supported currently.
	•	Query logs are stored in cases.db SQLite database.
	•	PDF files are saved locally with filenames case_<case_number>_<filing_year>.pdf.
	•	The app handles basic errors and invalid inputs gracefully.

⸻

## License

MIT License

