import sys
import ctypes
import itertools
import urllib.request
import os
import re
import json
import pickle
import time
import urllib
import requests
import img as img
import glob
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class Ticket(object):
    number = 0
    url = ""


class TicketPictures(object):
    title = ""
    src = ""


class TicketDocuments(object):
    name = ""
    src = ""


class Customer(object):
    name = ""
    url = ""


# THIS WILL LOG YOU INTO SERVICE FUSION
def login(driver, u, p):
    driver.get("https://admin.servicefusion.com/")

    ###AUTHENTICATION VARIABLES###
    companyID = driver.find_element_by_id("Authenticate_company")
    username = driver.find_element_by_id("Authenticate_uid")
    password = driver.find_element_by_id("Authenticate_pwd")
    companyID.send_keys("COMPANYID")
    username.send_keys(str(u))
    password.send_keys(str(p))
    driver.find_element_by_xpath("""//*[@id="login-form"]/div[5]/button""").click()
    return driver


def moveFile(path):
    time.sleep(1)
    downloadCheck = glob.glob("C:/tmp/*")
    for download in downloadCheck:
        if ".crdownload" in download:
            # ctypes.windll.user32.MessageBoxW(0, "FILE STILL DOWNLOADING, CRDOWNLOAD FOUND! - EXCEPTION", "SFScraper by Chuck", 1)
            print("File is still downloading, sleeping 30 seconds")
            time.sleep(30)

        if ".tmp" in download:
            # ctypes.windll.user32.MessageBoxW(0, "FILE STILL DOWNLOADING, TMP FOUND! - EXCEPTION", "SFScraper by Chuck", 1)
            print("File is still downloading, sleeping 30 seconds")
            time.sleep(30)

    files = glob.glob("C:/tmp/*")
    for file in files:
        print("Moving file %s to %s" % (file, path))
        try:
            os.rename(file, path)
        except PermissionError:
            # ctypes.windll.user32.MessageBoxW(0, "FILE STILL DOWNLOADING, PERMISSION ERROR FOUND! - EXCEPTION", "SFScraper by Chuck", 1)
            print("PERMISSION ERROR, FILE NOT READY TO MOVE")
            moveFile(path)
        except FileExistsError:
            # ctypes.windll.user32.MessageBoxW(0, "FILE ALREADY EXISTS! - EXCEPTION", "SFScraper by Chuck",1)
            os.remove(file)
            print("FILE ALREADY EXISTS")
        # time.sleep(3)
        print("Deleting file %s" % (file))
        # os.remove(file)
        time.sleep(3)


def loadCookies(driver, path):
    cookiefile = open(path, "r")
    raw_cookiedata = cookiefile.read()
    loaded_cookie_data = json.loads(raw_cookiedata)
    for cookie in loaded_cookie_data:
        driver.add_cookie(cookie)
    return driver


def rawCookies(path):
    cookiefile = open(path, "r")
    raw_cookiedata = cookiefile.read()
    loaded_cookie_data = json.loads(raw_cookiedata)
    return loaded_cookie_data


def saveCookies(driver, path):
    cookie_data = str(json.dumps(driver.get_cookies()))
    cookie_file = open(path, "w")
    cookie_file.write(cookie_data)
    return driver


def saveData(data, path):
    with open(path, "w") as f:
        pickle.dump(data, f)
    # filedata = pickle.dump(data)
    # file = open(path, "w")
    # file.write(data)


def getData(path):
    try:
        with open(path) as f:
            data = pickle.load(f)
    except:
        print("DUNNO")

    return data
    # filedata = open(path, "r")
    # rawfiledata = filedata.read()
    # loadedfiledata = json.loads(rawfiledata)
    # return loadedfiledata


def getTotalCustomers(driver):
    driver.get("https://admin.servicefusion.com/customer/customerList")
    total_pages = driver.find_element_by_class_name('dataTables_info').text.strip()
    total_pages = re.sub(r"Showing\s(\d+)\sto\s(\d+)\sof\s(\d+)\sentries", r"\3", total_pages)
    if total_pages.isdigit():
        return total_pages
    else:
        return 0


def getCustomers(driver, url):
    driver.get(
        "https://admin.servicefusion.com/serviceSpot/customerListAjaxLoading?name=&parentId=0&onlyParent=0&lastServSortOrder=&locationSortOrder=&tagSortOrder=&sortOrderFirst=&sortOrderSecond=&sortOrderThird=&perpage=100000&starting=193200&onlyInactive=0&random=0.2736582207864424")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "demo-dtable-03")))

    customers_table = driver.find_element_by_tag_name('table')
    customers_tbody = customers_table.find_element_by_tag_name('tbody')
    customers_tr = customers_tbody.find_elements_by_tag_name('tr')
    customerArr = []
    customerCount = len(customers_tr)
    i = 1
    for tr in customers_tr:
        tds = tr.find_elements_by_tag_name("td")
        customerObject = Customer()
        customerObject.name = str(tds[0].text.strip())
        customerObject.name = re.sub('[*]', '', customerObject.name)
        customerObject.name = re.sub('["]', '', customerObject.name)
        customerObject.name = re.sub('[/]', '-', customerObject.name)
        customerObject.name = re.sub("\\nParent.*$", "", customerObject.name)
        print("[%d/%d] Adding Customer To Array: %s" % (i, customerCount, customerObject.name))
        customerObject.url = tds[0].find_element_by_tag_name('a').get_attribute('href')
        customerArr.append(customerObject)
        i = i + 1

    return customerArr


def getTickets(driver, url):
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tab_history")))
    driver.find_element_by_id("tab_history").click()
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="demo-dtable-01"]/tbody/tr[1]/td[1]/a')))
    except:
        print("TimeoutException, No Tickets?")
    driver.execute_script("$('#demo-dtable-01').dataTable().fnDestroy()")
    tickets = driver.find_elements_by_xpath("//table[@id='demo-dtable-01']/tbody/tr")
    ticketCount = len(tickets)
    ticketArr = []
    i = 0
    for ticket in tickets:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="demo-dtable-01"]/tbody/tr[1]/td[1]/a')))
        driver.execute_script("$('#demo-dtable-01').dataTable().fnDestroy()")
        tds = ticket.find_elements_by_tag_name("td")

        first_td = tds[0].find_element_by_tag_name("a")
        ticketObject = Ticket()
        ticketObject.number = first_td.text.strip()
        print("[%d/%d] Getting Ticket: %s" % (i, ticketCount, ticketObject.number))
        ticketObject.url = first_td.get_attribute("href")
        ticketArr.append(ticketObject)
        i = i + 1

    return ticketArr


def getTicketDocs(driver, ticket, path):
    driver.get(ticket.url)
    docs = driver.find_element_by_id('documents-title')
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'documents-title')))
    try:
        docs.click()
    except:
        # ctypes.windll.user32.MessageBoxW(0, "HAD TROUBLE CLICKING DOCS, TRYING TO FIX! - EXCEPTION", "SFScraper by Chuck", 1)
        print("HAD TROUBLE CLICKING DOCS, TRYING TO FIX!")
        driver.get(ticket.url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'documents-title')))
        time.sleep(10)
        docs.click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'job_docs')))
    document_data = driver.find_element_by_id("job_docs")
    documents = document_data.find_elements_by_class_name("document-row")
    # doc_url = driver.find_elements_by_xpath('//*[@title="Download"]')
    ticketDocArr = []
    ticketDocCount = len(documents)
    i = 0
    for doc in documents:
        inputs = doc.find_elements_by_tag_name("input")
        ticketDocObject = TicketDocuments()
        ticketDocObject.name = inputs[1].get_attribute("value")
        ticketDocObject.name = re.sub(r"(\,|\s|\/|\.)", '-', ticketDocObject.name)
        ticketDocObject.name = re.sub(r"-(png|jpg|pdf|doc|docx|jpeg|gif|PNG|JPG|PDF|DOC|DOCX|JPEG|GIF)", r".\1",
                                      ticketDocObject.name)
        ticketDocObject.src = doc.find_element_by_class_name("btn-doc-download").get_attribute('href')
        ticketDocArr.append(ticketDocObject)
        print("[%d/%d] Getting Ticket Doc: %s" % (i, ticketDocCount, ticketDocObject.name))
        # doc_path = "images/" + customer_name2 + "/" + ticket_number + "/docs/"
        i = i + 1
        print(ticketDocObject.src)
        if not os.path.exists(path):
            os.makedirs(path)
        if "amazonaws" not in ticketDocObject.src:
            driver.get(ticketDocObject.src)
            moveFile(path + ticketDocObject.name)
        else:
            urllib.request.urlretrieve(ticketDocObject.src, path + ticketDocObject.name)
    return ticketDocArr


def getTicketPics(driver, ticket, path):
    driver.get(ticket.url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'pictures-title')))
    pics = driver.find_element_by_id('pictures-title')
    try:
        pics.click()
    except:
        # ctypes.windll.user32.MessageBoxW(0, "Having trouble clicking Pics - EXCEPTION", "SFScraper by Chuck", 1)
        print("HAD TROUBLE CLICKING PICS, TRYING TO FIX!")
        driver.get(ticket.url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'pictures-title')))
        time.sleep(10)
        pics.click()
    pics.click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'image-ids')))
    pictures = driver.find_elements_by_xpath('//*[@id="gallery"]/div/div[1]/div/ul/li')
    ticketPicArr = []
    ticketPictureCount = len(pictures)
    i = 0
    for pic in pictures:
        ticketPictureObject = TicketPictures()
        ticketPictureObject.title = pic.find_element_by_tag_name('a').get_attribute('data-title')
        ticketPictureObject.title = re.sub(r"(\,|\s|\/|\.)", '-', ticketPictureObject.title)
        ticketPictureObject.title = re.sub(r"-(png|jpg|pdf|doc|docx|jpeg|gif|PNG|JPG|PDF|DOC|DOCX|JPEG|GIF)", r".\1",
                                           ticketPictureObject.title)
        ticketPictureObject.src = pic.find_element_by_tag_name('a').get_attribute('href')
        ticketPicArr.append(ticketPictureObject)
        print("[%d/%d] Getting Ticket Picture: %s" % (i, ticketPictureCount, ticketPictureObject.title))
        i = i + 1
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                print('Couldnt make directory')
        if "amazonaws" not in ticketPictureObject.src:
            driver.get(ticketPictureObject.src)
            moveFile(path + ticketPictureObject.title)
        else:
            try:
                urllib.request.urlretrieve(ticketPictureObject.src, path + ticketPictureObject.title)
            except:
                # ctypes.windll.user32.MessageBoxW(0, "Couldnt download Image", "SFScraper by Chuck", 1)
                print("Couldn't download the image")

    return ticketPicArr

def getTicketNotes(driver, ticket, path):
    driver.get(ticket.url)
    notes = driver.find_elements_by_xpath('//*[@id="note-list"]')
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="note-list"]')))
    for note in notes:
        print(note.text)
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                print('Couldnt make directory')
        text = open(path + "Notes.txt","w+")
        try:
            text.write(note.text)
        except UnicodeEncodeError:
            print("Something went wrong with Notes...")
        text.close()
    return note

# options = webdriver.ChromeOptions()
# options.add_argument("download.default_directory=C:/tmp")
# chrome_path = r"C:\Users\User\PycharmProjects\SFScraper\venv\Include\chromedriver.exe"
# driver = webdriver.Chrome(chrome_path, chrome_options=options)

chromeOptions = webdriver.ChromeOptions()
prefs = {"download.default_directory": "C:/tmp"}
chromeOptions.add_experimental_option("prefs", prefs)
chromedriver = "C:/Users/User/PycharmProjects/SFScraper/venv/Include/chromedriver.exe"
driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions)

driver.get("https://admin.servicefusion.com/customer/customerList?index=0&search=&page=1")

# if os.path.isfile("cookie.txt"):
#     loadCookies(driver, "C:/Users/User/PycharmProjects/SFScraper/cookie.txt")
# else:
login(driver, "USERNAME", "PASSWORD")
saveCookies(driver, "cookie.txt")

driver.get("https://admin.servicefusion.com/customer/customerList?index=0&search=&page=1")

print("HERE WE GOOOOOOOOO!")

customers = getCustomers(driver,
                         "https://admin.servicefusion.com/serviceSpot/customerListAjaxLoading?name=&parentId=0&onlyParent=0&lastServSortOrder=&locationSortOrder=&tagSortOrder=&sortOrderFirst=&sortOrderSecond=&sortOrderThird=&perpage=100000&starting=193200&onlyInactive=0&random=0.2736582207864424")

print("Found %d Customers" % (len(customers)))
for customer in customers[0:]:
    try:
        customerName = customer.name
        customerName = re.sub(r"(\/)", "-", customerName)
        customerName = re.sub("\\nParent.*$", "", customerName)
    except NameError:
        customerName = "N/A"
    print("Scraping Customer %s" % (customerName))
    try:
        customerUrl = customer.url
        print("Navigating to %s" % (customerUrl))
        print("Getting Tickets")
        tickets = getTickets(driver, customerUrl)
        print("Found %d Tickets for customer %s" % (len(tickets), customerName))
        for ticket in tickets:
            ticketNumber = ticket.number
            print("Ticket Number: %s" % (ticket.number))
            ticketPics = getTicketPics(driver, ticket, "images/" + customerName + "/" + ticketNumber + "/pics/")
            print("Found And Saved %d Ticket Pictures" % (len(ticketPics)))
            ticketDocs = getTicketDocs(driver, ticket, "images/" + customerName + "/" + ticketNumber + "/docs/")
            print("Found And Saved %d Ticket Documents" % (len(ticketDocs)))
            getTicketNotes(driver, ticket, "images/" + customerName + "/" + ticketNumber + "/")
    except NameError:
        print("NO URL FOR THIS CUSTOMER")