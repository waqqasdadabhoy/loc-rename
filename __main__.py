import os
import PyPDF2
import multiprocessing
from joblib import Parallel, delayed
import re
import urllib.request
from xml.etree.ElementTree import parse

p = re.compile(r"((?:[0-9]{3}-)?[0-9]{1,5}-[0-9]{1,7}-[0-9]{1,6}-[0-9])")

def getIsbnFromPdf(filePath: str):
    with open(filePath, 'rb') as f:
        try:
            fileObject = PyPDF2.PdfFileReader(f)
            if fileObject.isEncrypted or fileObject.numPages < 20:
                return []
            for page_num in range(20):
                text = fileObject.getPage(page_num).extractText()
                if ("ISBN" in text):
                    isbns = p.findall(text)
                    return [re.sub("[^0-9]", "", isbn) for isbn in isbns]
            return []
        except:
            return []

def getBookInfoFromIsbn(isbn: str) -> str:
    u = urllib.request.urlopen("http://lx2.loc.gov:210/lcdb?version=1.1&operation=searchRetrieve&query="+ isbn +"&maximumRecords=1")
    doc = parse(u)
    root = doc.getroot()
    for child in root.iter(r'{http://www.loc.gov/zing/srw/}numberOfRecords'):
        for child in root.iter(r"{http://www.loc.gov/MARC21/slim}datafield"):
            for grandchild in child.iter(r"{http://www.loc.gov/MARC21/slim}subfield"):
                if child.attrib['tag'] == '050':
                    if grandchild.attrib['code'] == 'a':
                        locClass_firstPart = grandchild.text
                    if grandchild.attrib['code'] == 'b':
                        locClass_secondPart = grandchild.text
                if child.attrib['tag'] == '100':
                    if grandchild.attrib['code'] == 'a':
                        # TODO handle multiple authors
                        locAuthor = grandchild.text.split(',')[0]
                if child.attrib['tag'] == '245':
                    if grandchild.attrib['code'] == 'a':
                        locTitle = grandchild.text.replace("\\","")
                        locTitle = locTitle.replace("/","")
                        locTitle = locTitle.replace(".","")
                        locTitle = locTitle.replace(":","")
                        #locTitle = locTitle.replace("?"," Sharp")
                        locTitle = locTitle.replace("\u266f"," Sharp")
                        locTitle = locTitle.strip()

        try:
            return (locClass_firstPart + locClass_secondPart), locAuthor, locTitle
        except (UnboundLocalError, NameError):
            return None, None, None
        return None, None, None

def check_file(filePath: str):
    locClassFound = False
    if filePath.endswith(".pdf"):
        isbn = getIsbnFromPdf(filePath)
        if len(isbn) > 0:
            #print(filePath)
            #print(isbn)
            for num in isbn:
                if locClassFound:
                    break
                loc_class, loc_author, loc_title = getBookInfoFromIsbn(num)
                if loc_class is not None:
                    locClassFound = True
                    newFileName = (loc_class + " ("+loc_author+") "+loc_title+".pdf")
                    print(rename_cmd + " \""+filePath+"\"", "\""+os.path.join(directory, newFileName)+"\"")
if os.name == 'nt':
    rename_cmd = 'rename'
else:
    rename_cmd = 'mv'
directory = r"D:\Literature"
[check_file(os.path.join(directory, i)) for i in os.listdir(directory)]

