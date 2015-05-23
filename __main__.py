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

def check_file(filePath: str):
    locClassFound = False
    if filePath.endswith(".pdf"):
        loc_nums = getIsbnFromPdf(filePath)
        if len(loc_nums) > 0:
            print(filePath)
            for num in loc_nums:
                if locClassFound:
                    break
                u = urllib.request.urlopen("http://lx2.loc.gov:210/lcdb?version=1.1&operation=searchRetrieve&query="+ num +"&maximumRecords=1")
                doc = parse(u)
                root = doc.getroot()
                for child in root.iter(r'{http://www.loc.gov/zing/srw/}numberOfRecords'):
                    for child in root.iter(r"{http://www.loc.gov/MARC21/slim}datafield"):
                        if child.attrib['tag'] == '050':
                            for grandchild in child.iter(r"{http://www.loc.gov/MARC21/slim}subfield"):
                                print(grandchild.text)
                                locClassFound = True

def main():
    directory = r"D:\Literature"
    [check_file(os.path.join(directory, i)) for i in os.listdir(directory)]

if __name__ == '__main__':
    main()
