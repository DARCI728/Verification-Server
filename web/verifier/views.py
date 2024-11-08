from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests


@csrf_exempt
def verify_pdf(request):
    if request.method == "POST":
        if "file" not in request.FILES:
            return render(request, "verify.html", {"error": "No file uploaded"})

        pdf_file = request.FILES["file"]
        password = request.POST.get("password", None)

        api_url = "https://twdcctest.twca.com.tw:10100/diplomaVerification/api/v1/dcert-moe/verify"
        files = {"file": pdf_file}
        data = {}

        if password:
            data["mima"] = password

        try:
            response = requests.post(api_url, files=files, data=data)
            result = response.json()
            return render(request, "verify.html", {"result": result})
        except requests.exceptions.RequestException as e:
            return render(request, "verify.html", {"error": str(e)})

    return render(request, "verify.html")
