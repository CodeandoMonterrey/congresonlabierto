import requests
import PyPDF2
import pyocr
import pyocr.builders
import io
import os
import random
import string

from subprocess import Popen, PIPE
from wand.image import Image
from PIL import Image as PI

try:
    from xml.etree.cElementTree import XML
except ImportError:
    from xml.etree.ElementTree import XML
import zipfile

ext = {"application/pdf":"pdf", "application/msword":"doc", "application/vnd.openxmlformats-officedocument.wordprocessingml.document":"docx"}
language_conversion = {"de":"deu", "el":"ell", "en":"eng","es":"spa", "fr":"fra","he":"heb","hr":"hrv", "hu":"hun","it":"ita", "nl":"nld", "pt":"por", "ru":"rus", "sk":"slk", "tr":"tur","zh-CHT": "chi_tra", "uk":"ukr" }

WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
PARA = WORD_NAMESPACE + 'p'
TEXT = WORD_NAMESPACE + 't'

def return_name():
    word = ''.join(random.sample(string.ascii_uppercase, 6))
    return word


def download_file(url):
    print(url)
    request = requests.get(url)
    data= request.content
    mime = request.headers["Content-Type"]
    extension = ext[mime]
    path = "temp/"+return_name() + "." + extension
    with open(path, 'wb') as f:
            f.write(data)
    return path, extension


def doc_text(path):
    cmd = ['antiword', path]
    p = Popen(cmd, stdout=PIPE)
    stdout, stderr = p.communicate()
    text = stdout.decode('ascii', 'ignore').replace("\n", " ")
    return text


def pdf_ocr(path, language):
    lang = language_conversion[language]
    tool = pyocr.get_available_tools()[0]
    req_image = []
    text = ""
    image_pdf = Image(filename=path, resolution=300)
    image_jpeg = image_pdf.convert('jpeg')
    for img in image_jpeg.sequence:
        img_page = Image(image=img)
        req_image.append(img_page.make_blob('jpeg'))
    for img in req_image:
        txt = tool.image_to_string(
            PI.open(io.BytesIO(img)),
            lang=lang,
            builder=pyocr.builders.TextBuilder()
        )
        text= text + " " + txt
    return text


def pdf_text(path, language):
    pdfFileObj = open(path,"rb")     #'rb' for read binary mode
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    text = ""
    for page in range(1,pdfReader.numPages):
        pageObj = pdfReader.getPage(page)          #'9' is the page number
        text = text + pageObj.extractText()
    text_density = float(len(text.split(" ")))/float(pdfReader.numPages)
    if text_density < 3:
        text = pdf_ocr(path, language)
    text = text.replace("\n"," ")
    return text


def docx_text(path):
    document = zipfile.ZipFile(path)
    xml_content = document.read('word/document.xml')
    document.close()
    tree = XML(xml_content)

    paragraphs = []
    for paragraph in tree.getiterator(PARA):
        texts = [node.text
                 for node in paragraph.getiterator(TEXT)
                 if node.text]
        if texts:
            paragraphs.append(''.join(texts))
    text = '\n\n'.join(paragraphs).replace("\n", " ")
    return text


def get_text(path, extension, language):
    text = "[Not a valid text file]"
    if extension == "pdf":
        text = pdf_text(path, language)
    if extension == "doc":
        text = doc_text(path)
    if extension == "docx":
        text = docx_text(path)
    return text


def document_data(url, language):
    try:
        path, extension = download_file(url)
        print(path)
        print(extension)
        text = get_text(path, extension, language)
        print("Got text")
        os.remove(path)
    except:
        text = "[Not a valid text file]"
    output_doc = {}
    output_doc["extension"] = extension
    output_doc["text"]= text
    output_doc["language"] = language
    output_doc["_id"] = url
    return output_doc
