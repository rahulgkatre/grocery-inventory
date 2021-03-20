import gspread
import requests
import time

from bs4 import BeautifulSoup
from datetime import date
from oauth2client.service_account import ServiceAccountCredentials

def spreadsheet():
    # https://stackoverflow.com/questions/56084171/accessing-google-sheets-api-with-python
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open("Home Inventory List")
    return (spreadsheet.get_worksheet(0), spreadsheet.get_worksheet(1))

def lookup(upc):
    upc = str(upc)
    lookup_table = spreadsheet()[1]
    upc_column = lookup_table.col_values(1)
    
    try:
        row_index = upc_column.index(upc) + 1
        name_row = lookup_table.row_values(row_index)
        return name_row[1]
    except:
        time.sleep(1)
        requests.packages.urllib3.disable_warnings() 

        # https://hackersandslackers.com/scraping-urls-with-beautifulsoup/
        url = 'https://www.upcitemdb.com/upc/' + str(upc)
        header = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36" ,'referer':'https://www.google.com/'}
        req = requests.get(url, headers=header, verify=False)
        soup = BeautifulSoup(req.content, 'html.parser')
        title = str(soup.title).upper()
        print(title)
        name = ''
        try:
            title = title[:title.index(' | ')]
            title = title[title.index(' - ') + 3:]
            name = title
        except:
            name = 'NOT FOUND'
        finally:
            if len(name) == 0:
                name = 'NOT FOUND'

        lookup_table.insert_row([upc, name], 2)
        print('Original title:', soup.title)
        print('Name found:', name)
        return name

def add_product(upc):
    upc = str(upc)
    inventory_list = spreadsheet()[0]
    upc_column = inventory_list.col_values(1)

    try:
        row_index = upc_column.index(upc) + 1
        # https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html
        product_row = inventory_list.row_values(row_index)
        inventory_list.update_cell(row_index, 3, int(product_row[2]) + 1)
        inventory_list.update_cell(row_index, 4, str(date.today()))
    except ValueError:
        name = lookup(upc)
        product_row = [str(upc), name, 1, str(date.today())]
        inventory_list.append_row(product_row)
    finally:
        update_blanks()

def remove_product(upc):
    upc = str(upc)
    inventory_list = spreadsheet()[0]
    upc_column = inventory_list.col_values(1)
    
    try:
        row_index = upc_column.index(upc) + 1
        new_quantity = int(inventory_list.row_values(row_index)[2]) - 1
        if new_quantity > 0:
            inventory_list.update_cell(row_index, 3, new_quantity)
        else:
            try:
                inventory_list.delete_rows(row_index)
            except:
                for col_index in range(inventory_list.col_count):
                    inventory_list.update_cell(row_index, col_index, '')
    finally:
        update_blanks()

def update_blanks():
    inventory_list = spreadsheet()[0]
    names_column = inventory_list.col_values(2)
    for row_index in range(len(names_column)):
        if str(names_column[row_index]) == 'NOT FOUND':
            upc = inventory_list.col_values(1)[row_index]
            name = lookup(upc)
            inventory_list.update_cell(row_index + 1, 2, name)

while True:
    upc = input('UPC: ')
    add_product(upc)
