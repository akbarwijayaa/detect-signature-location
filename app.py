from flask import Flask, request, send_file
from src.main import signature_world
from io import BytesIO
from src.to_dashboard.main import append_data, update_api_status

import time
from datetime import datetime, date 


app = Flask(__name__)
app.config["DEBUG"] = True

@app.route("/detect-signature-location/predict", methods=['POST', 'GET'])
def detect():
    start_time = time.time()

    if request.method == "GET":
        return "API Detect Signature Location"
    
    pdf_file = request.files['pdf_file']
    pdf_bytes = pdf_file.read()
    
    step_approve = request.form.get('step_approve')
    url_gen = request.form.get('url_gen')
    
    crowd = signature_world()
    bbox, change_page, pdf_document = crowd.process_pdf(pdf_bytes=pdf_bytes, 
                                                        approve=int(step_approve),
                                                        creator=False)
    
    result = crowd.draw_qr(pdf_bytes=pdf_bytes, 
                                change_page=change_page, 
                                url=url_gen,
                                bbox=bbox,
                                pdf_document=pdf_document,
                                creator=False)
    
    result_bytes = result.write()
    response = send_file(BytesIO(result_bytes), 
                         mimetype='application/pdf', 
                         as_attachment=True, 
                         download_name=f'{url_gen}.pdf')
    
    ip_addr = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    append_data(
        id_api = 4,
        ip_address = ip_addr,
        request_date = datetime.now(),
        url_api = "http://ai.quick.com/detect-signature-location/predict",
        response = "Success",
        response_time = round((time.time() - start_time) * 100 )
    )

    return response


@app.route("/detect-signature-location/creation", methods=['POST', 'GET'])
def creator():
    start_time = time.time()

    if request.method == "GET":
        return "(For Creator) API Detect Signature Location"
    
    pdf_file = request.files['pdf_file']
    pdf_bytes = pdf_file.read()
    url_gen = request.form.get('url_gen')
    
    crowd = signature_world()
    bbox, change_page, pdf_document = crowd.process_pdf(pdf_bytes=pdf_bytes, 
                                                        creator=True)
    
    result = crowd.draw_qr(pdf_bytes=pdf_bytes, 
                                change_page=change_page, 
                                url=url_gen,
                                bbox=bbox,
                                pdf_document=pdf_document,
                                creator=True)
    
    result_bytes = result.write()
    response = send_file(BytesIO(result_bytes), 
                         mimetype='application/pdf', 
                         as_attachment=True, 
                         download_name=f'{url_gen}.pdf')

    ip_addr = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    append_data(
        id_api = 4,
        ip_address = ip_addr,
        request_date = datetime.now(),
        url_api = "http://ai.quick.com/detect-signature-location/creation",
        response = "Success",
        response_time = round((time.time() - start_time) * 100 )
    )
    return response
    


if __name__ == "__main__":
    try :
        update_api_status(4, 'Active')
        app.run(host="0.0.0.0", port=2060)

    finally:
        update_api_status(4, 'Inactive')