import sqlite3
import numpy as np
import cv2
import os
import pytesseract
from PIL import Image as Img
from pdf2image import convert_from_path
import layoutparser as lp

def extract_title_abstract(pdf_path):
    try:
        # Convert first page to image
        images = convert_from_path(pdf_path, first_page=1, last_page=2, poppler_path=r'C:/Program Files/poppler/poppler-23.11.0/Library/bin')
        first_page = np.array(images[0])
        
        # Initialize layout model
        model = lp.Detectron2LayoutModel(
                config_path ='lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config', # In model catalog
                label_map   ={0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"}, # In model`label_map`
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8] # Optional
            )
        
        # Detect layout
        layout = model.detect(first_page)
        
        # Extract title (usually the first text block)
        title = ""
        for block in layout:
            if block.type == "Title":
                segment_image = (block
                            .crop_image(first_page))
                title = pytesseract.image_to_string(segment_image).strip()
                break
        
        # Extract abstract
        text = pytesseract.image_to_string(first_page)
        abstract_start = text.find('Abstract') + len('Abstract')
        abstract_end = text.find('Introduction')
        
        # If not found in first page, try second page
        if abstract_start == -1 or abstract_end == -1:
            if len(images) > 1:
                text = pytesseract.image_to_string(images[1])
                abstract_start = text.find('Abstract') + len('Abstract')
                abstract_end = text.find('Introduction')
        
        abstract = text[abstract_start:abstract_end].strip() if abstract_start != -1 and abstract_end != -1 else ""
        
        return title, abstract
    except Exception as e:
        print(e)
        return "testing", "testing"


#detect text in passed image
def detect_text(hsv_img):
  #print("in text")
  pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'
  resized_block = hsv_img.resize((hsv_img.width * 4, hsv_img.height * 4))
  text = pytesseract.image_to_string(resized_block, lang='eng',config= '--psm 3 --oem 1')
  return text

# function to segment rows
def rows(hsv,row,hsv_img,pg_no):
    st1=""
    st2=""
    f_st1=""
    f_st2=""
    whitespace = [[0,0,0]]
    p=0
    start=0
    for i in range(row):
        c=0
        for element in hsv[i]: #hsv[i] is a single row of pixels
            if element!=255: #checking for black pixel (hsv value for white = 255)
                c=1
                break
        if c==0:
            p+=1
        else:
            p+=1
            whitespace.append([p,start,i]) #storing position of whitespaces
            p=0
            c=0
            start=i
    whitespace.remove([0,0,0])
    whitespace_1 = [[0,0,0]]
    for ele,spos,epos in whitespace:
        if ele!=1:
            whitespace_1.append([ele, spos, epos]) #removing row of height=1
    whitespace_1.remove([0,0,0])
    l = (len(whitespace_1))
    tex = []
    for i in range(l-1):
        sp = whitespace_1[i][2] #storing start of text block
        ep = whitespace_1[i+1][1] #storing end of text block
        h = hsv[sp:ep]
        tex.append([sp,ep])
        hsv1 = Img.fromarray(h)
        width,height = hsv1.size
        #print(width,height)
        #display(hsv1)
        if height>0 and width>0:
            st1,st2=cols(hsv1,h,height,width,pg_no) #detecting columns and hence text
            f_st1=f_st1+st1 #storing single column and left hand column strings
            f_st2=f_st2+st2 #storing only right hand column strings because no case of single column at end of page has been seen
            #print(st1)
            #print(st2)
    f_st = f_st1+f_st2 #combining text obtained from both columns
    return f_st

# function to segment columns
def cols(hsv_img,hsv,height,width,pg_no):
    mid=int(width/2)
    element=255
    sp=mid
    ep=mid
    st1 = ""
    st2= ""
    c1=0 #counter to break loop when black pixel has been detected on left side
    c2=0 #same function as c1 but for right side
    for i in range(mid):
        p1 = hsv[:,mid-i] #column left of mid
        p2 = hsv[:,mid+i] #column right of mid
        if c1==0:
            for element in p1: #checking for black pixel on left side
                if element!=255:
                    sp=mid-i
                    c1=1
                    break
        if c2==0:
            for element in p2: #checking for black pixel on left side
                if element!=255:
                    ep=mid+i
                    c2=1
                    break
        if c1==1 and c2==1:#to break outermost loop when columns with black pixel on both sides have been detected
            break
    if (ep-sp)>40:#check for column break
        #print("1")
        hsv1 = hsv[:,0:sp] #croping image for left column
        hsv2 = hsv[:,ep:width] #croping image for right column
        img1 = Img.fromarray(hsv1)
        img2 = Img.fromarray(hsv2)
        st1 = detect_text(img1)#detect text in left cloumn
        st2 = detect_text(img2)#detect text in right column
    else:#if not single column text
        #print("2")
        st1 = detect_text(hsv_img)
    return st1,st2

def text_extraction(pdf_dir, progress_callback=None):
    print(pdf_dir)
    success = True
    try:
        conn = sqlite3.connect('database/articles.db')
        c = conn.cursor()
        f_corpora = open('database/text_corpora.txt', 'w')
        # Create table
        c.execute('''
            CREATE TABLE IF NOT EXISTS articles
            (id INTEGER, text TEXT, title TEXT, abstract TEXT, text_corpora TEXT)
        ''')
        
        pdf_file_no=10
        for filename in pdf_dir:
            if filename.endswith('.pdf'):
                # print(os.path.join(pdf_dir, filename))
                # pdf_file = os.path.join(pdf_dir, filename)
                pdf_file = filename
                images = convert_from_path(pdf_file, poppler_path=r'C:/Program Files/poppler/poppler-23.11.0/Library/bin')
                text = ""
                pg_no=0
                total_images = len(images)
                for i, image in enumerate(images):
                    pg_no+=1
                    img_array = np.array(image)
                    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                    #print(hsv)
                    hsv_img = Img.fromarray(hsv)
                    #display(hsv_img)
                    row = np.size(hsv, axis=0) #calculating rows
                    col = np.size(hsv, axis=1) #calculating columns
                    tex = rows(hsv,row,hsv_img,pg_no) #pagewise text extraction
                    #print(tex)
                    text=text+tex #store text as extracted page by page
                    if progress_callback is not None:
                        progress_callback(i / total_images)
                f_corpora.write(text + '\n')
                
                title, abstract = extract_title_abstract(pdf_file)
                print(title, abstract)
                
                c.execute('''
                    INSERT INTO articles (id, text, title, abstract)
                    VALUES (?, ?, ?, ?)
                ''', (pdf_file_no, text, title, abstract))
                pdf_file_no += 1
            # only for testing purpose
            # if(pdf_file_no > 1):
            #   break
        conn.commit()
        conn.close()
        f_corpora.close()
    except Exception as e:
        print(e)
        success = False
    return success
        

