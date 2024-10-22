from bs4 import BeautifulSoup
import urllib.request as main
import time
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.pdfbase.ttfonts import TTFont
import json


def save_file(filename, text, format='txt', original = ''):

    file_path = filename + "." + format

    if format == 'pdf':
        pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        doc = SimpleDocTemplate(file_path, pagesize=letter)

        styles = getSampleStyleSheet()
        style = styles["Normal"]
        style.fontName = "Arial"
        style.language = "el"

        greek_paragraph = Paragraph(text, style)
        doc.build([greek_paragraph])

    elif format == 'txt':
        with open(file_path, 'w', encoding='utf-8') as f:
            lines = text.replace('\n', '').split('.')
        
        # Write each line to the file with a newline character
            for line in lines[:-1]:

                f.write(line + '.' + '\n')

    elif format == 'json':
        data = {
            "query": original,
            "answer": text
        }
        json_string = json.dumps(data)

        with open(file_path, 'w') as json_file:
            json_file.write(json_string)


# Example usage

def convert_txt_to_sdf(input_txt_file, output_sdf_file):
    # Read the text file into a pandas DataFrame
    with open(input_txt_file, "r", encoding='utf-8') as f:
        x = f.read()
        for text in x.split("Article"):
            df = pd.read_csv(input_txt_file, sep='\t', header=None, names=['Column1', 'Column2', 'Column3'])
            df.to_csv(output_sdf_file, sep='\t', index=False)
    # Write the DataFrame to an SDF file
        f.close()
    

# Example usage
# input_txt_file = 'articles.txt'  # Replace with your input text file
# output_sdf_file = 'me.sdf'  # Replace with the desired output SDF file
    convert_txt_to_sdf(input_txt_file, output_sdf_file)

def get_links(url):
    html_content = None
    with main.urlopen(url) as res:
        html_content = res.read()

    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        articles = soup.find_all('div', class_='article-data border-box right')
        links = []
        for article in articles:
            link = article.find('a')
            if link:
                links.append(link['href'])
    return links


def get_text(urls, wanted_year): #delete ,stop after
    text = ""
    k = 0
    for url in urls:
        
        html_content = None
    
        with main.urlopen(url) as res:
            html_content = res.read()
            time.sleep(0.05)
        
        if html_content:
            
            soup = BeautifulSoup(html_content, 'html.parser')
            articles = soup.find('div', class_='post-content mb-30 border-box')
            if articles:
                time_element = soup.find('time')
                datetime_value = time_element['datetime']
                dt = datetime_value[:4]
                # if stop == 2:      #delete after
                #     time = str(2023)    #delete after  
                if wanted_year > dt :
                    return str(dt)


                paragraphs = articles.find_all('p')
                k+=1
                text += "Article {}\n".format(k)
                for paragraph in paragraphs:
                    
                    text += paragraph.get_text() + "\n"
                    
    
            # with open("articles.txt", 'a', encoding='utf-8') as f:
                # f.write(text) 
          
    return text           

if __name__ == "__main__":


    wanted_year = str(input("Give me a year: "))  #ΕΩΣ ΠΟΙΑ (<=) ΧΡΟΝΟΛΟΓΙΑ 
    category = str(input("Give me a category: "))   #ΚΑΤΗΓΟΡΙΑ ΘΕΜΑΤΟΣ


    DEFAULT_SOURCE =  str("https://www.skai.gr")  #ΜΗΝ ΑΛΛΑΞΕΙΣ ΤΟ ΛΙΝΚ, ΑΡΧΙΖΟΥΝ ΜΕ /news/tech....  UPPER CASE = CONSTANT ΣΤΗΝ Python
    current_source = "https://www.skai.gr/news/{}".format(category)  #ΛΙΝΚ ΠΟΥ ΔΙΑΧΕΙΡΙΖΕΤΑΙ ΤΑ NEXT PAGES

    page_var = 1
    tail = "?page={}".format(page_var)   # ΟΥΣΙΑΣΤΙΚΑ ΤΟ ?page={number} π.χ. https://www.skai.gr/news/technology?page=1

    stop = 1  #delete after


    while True:

        links = get_links(current_source)  #Παίρνει τα links
        print(links)
        for i in range(len(links)):   #Προσθέτει το https://www.skai.gr στα links για να γινουν valid
                links[i] = DEFAULT_SOURCE + links[i]

        current_year = get_text(links, wanted_year, stop)[1]  #delete ,stop after
        

        if "?page=" in current_source :     #ελέγχει αν βρίσκεται π.χ. στο https://www.skai.gr/news/technology ή στο https://www.skai.gr/news/technology?page=1
            current_source = current_source[:-1] + str(page_var) 
        else:
            current_source += tail

        page_var += 1

        stop = 2  #delete after
        if current_year < wanted_year:
            break
       

