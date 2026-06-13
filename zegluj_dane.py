import pandas as pd
import urllib
from urllib.request import Request
from bs4 import BeautifulSoup
import re
import ssl

def pobierz_dane():
    url = "https://zegluj.pl/mazury?page="

    pages = []
    context = ssl._create_unverified_context()
    
    # pobieramy strony 1-20
    for page_number in range(1, 21): 
        print(f'Pobieranie strony {page_number}')
        req = Request(f'{url}{page_number}', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=context) as resp:
            processed_page = BeautifulSoup(resp.read().decode('utf-8'), "html.parser")
            pages.append(processed_page)

    # wyciągamy dane pojedynczych jachtów z każdej strony
    full_yacht_data = []
    for page in pages:
        full_yacht_data += page.find_all(class_="yacht-box")

    # przerabiamy dane jachtó na słowniki
    yachts_data = []
    for yacht_html in full_yacht_data:
        yacht = {}
        
        name_tag = yacht_html.find(class_="yacht-box__name")
        yacht['name'] = name_tag.text.strip() if name_tag else "Nieznany"
        
        price = yacht_html.select_one("div.price span")
        yacht['price'] = float(price.contents[0].replace(' ', '').replace('zł', '').replace('PLN', '')) if price else None
        
        img_tag = yacht_html.select_one('.yacht-box__image img')
        if img_tag and img_tag.get('src'):
          yacht['img'] = f"https://zegluj.pl{img_tag['src']}"
        
        yacht_link = yacht_html.select_one('.yacht-box__image a')
        yacht['url'] = f"https://zegluj.pl{yacht_link['href']}" if yacht_link and yacht_link.get('href') else None
        
        desc_tag = yacht_html.find(class_='yacht-box__description')
        yacht['description'] = desc_tag.text.strip() if desc_tag else ""
        
        # wyciągamy parametry
        for param_row in yacht_html.select('li.yacht-box-info__item'):
            param_data = param_row.find_all('div')
            if len(param_data) < 2: continue
            
            param_type = param_data[0].text.strip()
            param_value = re.sub(r'\s+', '', param_data[1].text.strip())
            
            if 'osób' in param_type:
                try:
                  yacht['people'] = int(param_value.split('-')[-1])
                except ValueError:
                  yacht['people'] = None
            elif 'kabin' in param_type:
                try:
                    yacht['cabins'] = int(param_value.split('-')[-1])
                except ValueError:
                    yacht['cabins'] = None
            elif 'produkcji' in param_type:
                yacht['year'] = param_value

        yachts_data.append(yacht)

    # tworzymy DataFrame
    df_scraped = pd.DataFrame.from_dict(yachts_data)
    if 'cabins' in df_scraped.columns:
        df_scraped['cabins'] = df_scraped['cabins'].fillna(0) # zypełnienie braków danych o kabinach ( = 0)

    # ZAPIS DO CSV
    csv_filename = "zegluj_dane.csv"
    df_scraped.to_csv(csv_filename, index=False, encoding='utf-8-sig')
    print(f"Gotowe! Dane scraped({len(df_scraped)} wierszy) zapisano do: {csv_filename}")

if __name__ == "__main__":
    pobierz_dane()
