import fitz
import qrcode
import numpy as np
from PIL import Image, ImageOps
from io import BytesIO
from paddleocr import PaddleOCR


class signature_world:

    
    def __init__(self):
        self.ocr = PaddleOCR(lang='en')
        
    def process_pdf(self, pdf_bytes, approve=10, creator=True):
        pdf_stream = BytesIO(pdf_bytes)
        pdf_document = fitz.open(stream=pdf_stream)
        
        privileges = ["Creator"] if creator else [f"Approver {approve}"]
        bbox, change_page = self.core_pdf(pdf_document, privileges)
        return bbox[0], change_page[0], pdf_document
    
    def core_pdf(self, pdf_doc, privileges):
        bbox = []
        change_page = []
        for page_number in range(pdf_doc.page_count):
            page = pdf_doc[page_number]
            rect = page.rect

            image = page.get_pixmap()
            image_array = np.frombuffer(image.samples, dtype=np.uint8)
            image_array = image_array.reshape((image.height, image.width, len(image.samples) // (image.height * image.width)))

            image_res = Image.fromarray(image_array)
            result = self.ocr.ocr(img=np.array(image_res), det=True, rec=True, cls=True)
            for a in result[0]:
                if a[1][0] in privileges:
                    x1, y1, x2, y2 = self.to_xyxy(a[0])
                    data = [x1, y1, x2, y2]
                    bbox.append(data)
                    change_page.append(page_number)
                    
        return bbox, change_page
               
    def draw_qr(self, pdf_bytes, change_page, url, bbox, pdf_document, creator=False): # bbox akan berformat list
        logo = Image.open('img/logo.jpg').resize((40,40))
        logo_border = ImageOps.expand(logo, border=5,fill='white') 

        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            border=0, 
            box_size=6
        )
        
        qr.add_data(url)
        qr.make()
        qrgb = qr.make_image().convert('RGB')
        
        pos = ((qrgb.size[0] - logo_border.size[0]) // 2, (qrgb.size[1] - logo_border.size[1]) // 2)
        qrgb.paste(logo_border, pos)
        
        img_byte = BytesIO()
        qrgb.save(img_byte, format='PNG')
        im_bytes = img_byte.getvalue()

        margin_x, margin_y = (-12 if creator else -2, -35)
        increase_x, increase_y = (11 if creator else 3, 17)
        x0, y0, x1, y1 = (bbox[0] + margin_x, bbox[1] + margin_y, bbox[2] + increase_x, bbox[3] + increase_y)
    
        image_rectangle = fitz.Rect(x0, y0, x1, y1)
        pdf_stream = BytesIO(pdf_bytes)
        file_handle = fitz.open(stream=pdf_stream)
        first_page = file_handle[change_page]
        first_page.insert_image(image_rectangle,stream=im_bytes,xref=0)
        
        pdf_document.close()
        
        return file_handle # as fitz document

    def to_xyxy(self, bbox):
        x_min, y_min = bbox[0]
        x_max, y_max = bbox[2]
        
        return int(x_min), int(y_min), int(x_max), int(y_max)