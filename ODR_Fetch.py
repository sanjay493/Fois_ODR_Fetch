import requests
from bs4 import BeautifulSoup
import csv


url = 'https://www.allsides.com/media-bias/media-bias-ratings'
page=requests.post('https://www.fois.indianrail.gov.in/FOISWebPortal/FWP_RakeOtsg',{"Qry": "ODR_RK_OTSG","Zone": "SE", "captchaText": "7d47p"})
#print(page.content[:100])
soup=BeautifulSoup(page.content,'html.parser')
title=soup.title.text
print(title)
csv_writer = csv.writer(open('foistest.csv','+w'))
page_table_body=soup.find('tbody')
for tr in soup.find_all('tr'):
	data = []
	
	# for extracting header, Only onece
	
	#for th in tr.find_all('th'):
		#data.append(th.text)
	#if data:
		#print("Inserted Header : {}".format(','.join(data)))
		#csv_writer.writerow(data)
		#continue
		
		
    # for table Data
	for td in tr.find_all('td'):
		data.append(td.text.strip())
	if data:
		#print("Inserting Table Data :{}".format(','.join(data)))
		csv_writer.writerow(data)
		
	
	
