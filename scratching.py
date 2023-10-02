import requests
from bs4 import BeautifulSoup
from datetime import datetime
import mysql.connector

URL = "https://www.cuspide.com/100-mas-vendidos"

try:
  response = requests.get(URL, timeout=5)
  response.raise_for_status()  # Esto lanzará una excepción si el código de estado no es 200
except requests.Timeout:
  print("La solicitud excedió el tiempo máximo de espera.")
except requests.RequestException as e:
  print(f"Hubo un error al hacer la solicitud: {e}")

soup = BeautifulSoup(response.text, 'html.parser')
libros = [] #lista

for article in soup.find_all('h3'): # Dentro de cada 'article', buscamos el enlace
    a_tag = article.find('a')
    url = a_tag['href']
    titulo = a_tag.text
    # precio = a_tag
    # Extraer el precio
    precio_tag = article.find_next('span', class_='woocommerce-Price-amount')
    if precio_tag:
        # Obtener el texto del precio y eliminar el símbolo "$" y las comas
        precio_text = precio_tag.bdi.text.replace('$', '').replace('.', '').replace(',', '.')
        precio_text = precio_text.replace(',', '.')
        # Convertir el precio a un formato numérico (float)
        precio_num = float(precio_text)

    # Añadimos la información a nuestra lista de libros
    libros.append({
            'titulo': titulo,
            'url': url,
            'precio_pesos': precio_num
        })
# print(libros)

# Scraping precio del dolar
URL = "https://www.infobae.com/economia/divisas/dolar-hoy/"

try:
  response = requests.get(URL, timeout=5)
  response.raise_for_status()  # Esto lanzará una excepción si el código de estado no es 200
except requests.Timeout:
  print("La solicitud excedió el tiempo máximo de espera.")
except requests.RequestException as e:
  print(f"Hubo un error al hacer la solicitud: {e}")

dolar = BeautifulSoup(response.text, 'html.parser')

dolar_items = dolar.find_all('div', class_='exchange-dolar-item')
precio_dolar = {} #Diccionario

# Iterar sobre cada 'exchange-dolar-item' y extraer el valor del dólar
for item in dolar_items:
    titulo = item.find('a', class_='exchange-dolar-title').text
    valor_dolar = item.find('p', class_='exchange-dolar-amount').text.replace('$', '').replace(',', '.')
    print(f'{titulo}: {valor_dolar}')
    precio_dolar[titulo] = float(valor_dolar)  # Añadimos la URL base para obtener la URL completa
# print(precio_dolar)

for index, libro in enumerate(libros):
    libros[index]['precio_usd'] = round(libro['precio_pesos'] / precio_dolar['Dólar Banco Nación'], 2)
    libros[index]['precio_blue'] = round(libro['precio_pesos'] / precio_dolar['Dólar Libre'], 2)
    libros[index]['fecha'] = datetime.now().strftime('%Y-%m-%d')
    # print(libro)
# print(libros)

# Conéctate a tu base de datos MySQL
nombre_base_datos = 'libros_cuspide'
nombre_tabla_errores = "errores"
conexion = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
)
cursor = conexion.cursor()
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {nombre_base_datos}")
# conexion = mysql.connector.connect(
#     host='localhost',
#     user='root',
#     password='',
#     database=nombre_base_datos
# )
# Crea un cursor para ejecutar consultas
cursor = conexion.cursor()

cursor.execute(f"use {nombre_base_datos}")
# Define la consulta para crear la tabla si no existe
consulta_create_table = f"""
CREATE TABLE IF NOT EXISTS {nombre_base_datos}.libros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200),
    url VARCHAR(200),
    precio FLOAT(20),
    precio_usd FLOAT(20),
    precio_usd_blue FLOAT(20),
    fecha DATE
);
"""
consulta_create_table_errores = f"""
CREATE TABLE IF NOT EXISTS {nombre_base_datos}.{nombre_tabla_errores} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200),
    error VARCHAR(200),
    fecha DATE
);
"""
cursor.execute(consulta_create_table)
cursor.execute(consulta_create_table_errores)
# Define la consulta SQL para insertar los datos en la tabla
consulta_insert = "INSERT INTO libros (titulo, url, precio, precio_usd, precio_usd_blue, fecha) VALUES (%s, %s, %s, %s, %s, %s)"
consulta_insert_error = f"INSERT INTO {nombre_tabla_errores} (titulo, error, fecha) VALUES (%s, %s, %s)"

# # Inserta los datos en la tabla
for libro in libros:
    # if(libro['titulo'] == "ESTE DOLOR NO ES MIO"):
    #   libro['precio_pesos'] = str(libro['precio_pesos'])
    # print(libro)
    if not isinstance(libro['precio_pesos'], (int, float)) or not isinstance(libro['precio_usd'], (int, float)) or not isinstance(libro['precio_blue'], (int, float)):
      print("Error")
      cursor.execute(consulta_insert_error, (libro['titulo'], "Ha ocurrido un error con la carga de uno de los precios", libro['fecha']))
    else:
      cursor.execute(consulta_insert, (libro['titulo'], libro['url'], libro['precio_pesos'], libro['precio_usd'], libro['precio_blue'], libro['fecha']))

# Confirma la transacción y cierra la conexión
conexion.commit()
cursor.close()
conexion.close()