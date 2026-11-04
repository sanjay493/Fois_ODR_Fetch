import csv
import os
import ssl
import sys

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter

PORTAL_ORIGIN = 'https://www.fois.indianrail.gov.in'
URL = PORTAL_ORIGIN + '/FOISWebPortal/FWP_RakeOtsg'
# Python's default cipher list leaves this out, which fails the portal's TLS handshake.
LEGACY_CIPHER = 'AES128-GCM-SHA256'
# The CAPTCHA value is still hardcoded, so the server may reject this request.
FORM_DATA = {"Qry": "ODR_RK_OTSG", "Zone": "SE", "captchaText": "7d47p"}
OUTPUT_FILE = 'foistest.csv'
TIMEOUT_SECONDS = (5, 30)  # (connect, read)


def create_ssl_context():
	"""Return Python's default TLS settings plus the one older cipher the portal needs."""
	context = ssl.create_default_context()
	default_ciphers = ':'.join(cipher['name'] for cipher in context.get_ciphers())
	context.set_ciphers(default_ciphers + ':' + LEGACY_CIPHER)
	return context


class LegacyCipherAdapter(HTTPAdapter):
	def init_poolmanager(self, *args, **kwargs):
		kwargs['ssl_context'] = create_ssl_context()
		return super().init_poolmanager(*args, **kwargs)


def create_session():
	session = requests.Session()
	session.mount(PORTAL_ORIGIN + '/', LegacyCipherAdapter())
	return session


def fetch_page():
	with create_session() as session:
		response = session.post(URL, data=FORM_DATA, timeout=TIMEOUT_SECONDS)
	response.raise_for_status()
	return response.content


def find_data_table(soup):
	"""Return the table with the most data rows, ignoring tables that wrap others."""
	tables = [table for table in soup.find_all('table') if not table.find('table')]
	best_table = max(tables, key=lambda table: len(table.select('tr:has(td)')), default=None)
	if best_table is None or not best_table.select('tr:has(td)'):
		raise ValueError('No data table found in the response (was the CAPTCHA rejected?)')
	return best_table


def extract_rows(table):
	"""Return the table's rows as lists of text, keeping a repeated header row only once."""
	rows = []
	seen_headers = set()
	for tr in table.find_all('tr'):
		cells = tr.find_all(['th', 'td'])
		row = [cell.get_text(strip=True) for cell in cells]
		if not row:
			continue
		if not tr.find('td'):
			if tuple(row) in seen_headers:
				continue
			seen_headers.add(tuple(row))
		rows.append(row)
	return rows


def write_csv(rows, path):
	"""Write through a temp file so a failure can't damage the previous export."""
	temp_path = path + '.tmp'
	try:
		# utf-8-sig lets Excel on Windows detect the encoding, including Hindi text.
		with open(temp_path, 'w', newline='', encoding='utf-8-sig') as csv_file:
			csv.writer(csv_file).writerows(rows)
		os.replace(temp_path, path)
	except Exception:
		if os.path.exists(temp_path):
			os.remove(temp_path)
		raise


def main():
	try:
		soup = BeautifulSoup(fetch_page(), 'html.parser')
		print(soup.title.get_text(strip=True) if soup.title else '(no page title)')
		rows = extract_rows(find_data_table(soup))
		write_csv(rows, OUTPUT_FILE)
	except (requests.RequestException, ValueError, OSError) as error:
		print('Error: {}'.format(error), file=sys.stderr)
		return 1
	print('Wrote {} rows to {}'.format(len(rows), OUTPUT_FILE))
	return 0


if __name__ == '__main__':
	sys.exit(main())
