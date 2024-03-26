import pymysql as mysql 
import requests
from bs4 import BeautifulSoup
from time import sleep

#Delete tables if it exists
sqlDropTable = "drop table if exists cuspide100;"
sqlDropTable2 = "drop table if exists erroresCuspide100;"

#Create tables
sqlCreateTable = "CREATE TABLE `cuspide100` ( `idLibro` integer PRIMARY KEY AUTO_INCREMENT, `titulo` VARCHAR(120) NULL,`url` VARCHAR(200) NULL, `precio` DECIMAL(10,2) NULL, `precio_usd` DECIMAL(10,2) NULL, `precio_usd_blue` DECIMAL(10,2) NULL, `fecha` DATE);"
sqlCreateTable2 = "CREATE TABLE `erroresCuspide100` ( `idError` integer PRIMARY KEY AUTO_INCREMENT,`titulo` VARCHAR(120) NULL,`url` VARCHAR(200) NULL, `fecha` DATE);"

#connect database
print('connecting to the database')

with open('claves.txt') as archivo_claves:
    claves = [clave.strip() for clave in archivo_claves]

conexion = mysql.connect(host = claves[0],
                         database = claves[1],
                         user = claves[2],
                         password = claves[3])

cursor = conexion.cursor()
print('Deleting Tables if they exist')

cursor.execute(sqlDropTable)
cursor.execute(sqlDropTable2)
print('Creating Table cuspide100')
print('Creating Table erroresCuspide100')

cursor.execute(sqlCreateTable)
cursor.execute(sqlCreateTable2)

print('\nStarting the scrap, it might take a while...\n')

#URL for scrap
url = 'https://cuspide.com/100-mas-vendidos/'
response = requests.get(url)
sleep(2)
response.encoding = 'utf-8'
html = response.text

#Parse and obtain string from articles
dom = BeautifulSoup(html, features = 'html.parser')
cien_cuspide = dom.find_all(class_="name product-title woocommerce-loop-product__title")


#I get blue dollar value
url = "https://www.infobae.com/economia/divisas/dolar-hoy/?gclid=CjwKCAjwzo2mBhAUEiwAf7wjkjACSsty-ixJoqE5qrAcN4jtjvHTugGhT8JcPkyB7B38GhjLoZ-RoxoCQwgQAvD_BwE"
dom_dolar = requests.get(url).text
dom_dolar = BeautifulSoup(dom_dolar, features = 'html.parser')
precio_dolar_blue = dom_dolar.find_all(class_='exchange-dolar-amount')[2].get_text()[1:].replace('.', '')
print("The price of the blue dollar today is: $", precio_dolar_blue)

##Search for books, links and data on the 100 books 
orden = 0
for libro in cien_cuspide:
    titulo = libro.text.title()
    print('\nBook no.: ', orden+1)
    print('TITLE OF THE BOOK: ',titulo)
    url = libro.a['href']
    print('URL:', url)
    try:
        response_p = requests.get(url)
        sleep(1)
        response_p.encoding = 'utf-8'
        html_precio = response_p.text
        dom_precio = BeautifulSoup(html_precio, features = 'html.parser')
        precio_libro = float(dom_precio.find(class_="price product-page-price").bdi.text.strip('$').replace('.','').replace(',','.'))
        print('PRICE OF THE BOOK IN PESOS:', precio_libro)
        precio_libro_usd = dom_precio.find('span', style='font-size: 1.3em').text.replace('.','').replace(',','.')
        print('BOOK PRICE IN USD:', precio_libro_usd)
        dolar_blue = round(precio_libro / float(precio_dolar_blue), 2)
        print("PRICE OF THE BLUE DOLLAR BOOK:", dolar_blue)    
        print("Inserting...")
        cursor.execute("INSERT INTO cuspide100(titulo, url, precio, precio_usd, precio_usd_blue, fecha) VALUES(%s,%s,%s,%s,%s,curdate())", (titulo, url, precio_libro, precio_libro_usd, dolar_blue))
    except:
        requests.exceptions.HTTPError
        print('Book data ',titulo,' will not be loaded by mistake from the article website')
        cursor.execute("INSERT INTO erroresCuspide100(titulo, url, fecha) VALUES(%s,%s,curdate())", (titulo, url))
    orden +=1
         
print('\nWork completed successfully.\n')
conexion.commit()
cursor.close()
conexion.close()
