from django.shortcuts import render
from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timezone, timedelta

import base64
import hashlib
import hmac
import json
import os
import uuid
import requests


def base64url_encode(input):
    return base64.urlsafe_b64encode(input).rstrip(b"=").decode("utf-8")


def base64url_decode(input):
    padding_needed = 4 - (len(input) % 4)
    if padding_needed and padding_needed != 4:
        input += "=" * padding_needed
    return base64.urlsafe_b64decode(input)


def generate_jwt_token(header, payload, shared_key):
    encoded_header = base64url_encode(json.dumps(header).encode("utf-8"))
    encoded_payload = base64url_encode(payload)

    message = f"{encoded_header}.{encoded_payload}"

    key_bytes = bytes.fromhex(shared_key)
    signature = hmac.new(key_bytes, message.encode("ascii"), hashlib.sha256).digest()
    encoded_signature = base64url_encode(signature)

    jwt_token = f"{message}.{encoded_signature}"
    return jwt_token


def parse_jwt_token(jwt_token, shared_key):
    try:
        encoded_header, encoded_payload, encoded_signature = jwt_token.split(".")
    except ValueError:
        print("Invalid JWT structure.")
        return None

    message = f"{encoded_header}.{encoded_payload}"

    key_bytes = bytes.fromhex(shared_key)
    signature = hmac.new(key_bytes, message.encode("ascii"), hashlib.sha256).digest()
    expected_encoded_signature = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")

    if not hmac.compare_digest(expected_encoded_signature, encoded_signature):
        print("Verify failed.")
        return None

    try:
        payload_bytes = base64url_decode(encoded_payload)
        return payload_bytes
    except Exception as e:
        print(f"Error decoding JWT payload: {e}")
        return None


def download_signed_pdf(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, "rb"), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    else:
        return HttpResponse("File not found.", status=404)


@csrf_exempt
def AATL(request):
    if request.method != "POST":
        return render(request, "download.html")

    if "file" not in request.FILES:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    pdf_file = request.FILES["file"]
    file_data = pdf_file.read()
    filename = os.path.basename(pdf_file.name)

    api_url = "https://twiddemo.twca.com.tw/DspWeb/api/v3/signing"
    shared_key = "68A0A5865A7B6A7BFBAA2536875F4C9EE329D5BA69397F52A329886773ED6E36"

    req_id = "69115908-TEST-0001"
    req_seq = uuid.uuid4().hex[:20]
    taiwan_tz = timezone(timedelta(hours=8))
    req_time = datetime.now(taiwan_tz).strftime("%Y%m%d%H%M%S%f")[:-3]

    headers = {"Content-Type": "application/jose"}

    header = {
        "alg": "HS256",
        "ver": "1.0",
        "reqId": req_id,
        "reqSeq": req_seq,
        "reqType": "Signing",
        "reqTime": req_time,
        "filename": filename,
    }

    try:
        jws_token = generate_jwt_token(header, file_data, shared_key)
    except Exception as e:
        return JsonResponse({"error": f"JWT generation failed: {str(e)}"}, status=500)

    try:
        response = requests.post(api_url, headers=headers, data=jws_token)
    except requests.exceptions.RequestException as e:
        return render(request, "download.html", {"error": "Error communicating with signing API: 502"})

    if response.status_code == 200:
        response_content = response.content.decode("utf-8")
        resp_payload = parse_jwt_token(response_content, shared_key)

        if resp_payload is None:
            return render(request, "download.html", {"error": "400"})

        signed_filename = f"sign_{filename}"
        signed_file_path = os.path.join(settings.MEDIA_ROOT, signed_filename)

        with open(signed_file_path, "wb") as f:
            f.write(resp_payload)

        return render(request, "download.html", {"result": "Sign Successfully", "signed_file": signed_filename})
    else:
        return render(
            request,
            "download.html",
            {"error": f"Signing API returned HTTP {response.status_code}"},
            status=response.status_code,
        )
