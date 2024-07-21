
import json
from django.http import JsonResponse
from django.shortcuts import render
from .interperator import main
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def editor(request):
    print("xx")
    return render(request,'index.html')

def datapath(request):
    print("data")
    return render(request , 'datapath.html')

def decoder(request):
    return render(request , 'decoder.html')

def request(request):
    print(request.GET.get('test'))
    return JsonResponse({'test_confirmed': True})
    # return render(request , 'decoder.html')
    
@csrf_exempt
def assemble_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get('code', '')
        

        # Process the code to convert to hex
        hex_output = main(code)  # Implement this function

        return JsonResponse({'hex': hex_output})
    return JsonResponse({'error': 'Invalid request'}, status=400)
