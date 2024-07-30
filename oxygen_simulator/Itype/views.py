import json
import os
from pathlib import Path
from django.http import JsonResponse
from django.shortcuts import render
from .interperator import main
from .interperator import checkpsudo
from .Datapath import *
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
@csrf_exempt
def editor(request):
    print("xx")
    return render(request,'index.html')

# def datapath(request):
#     print("data")
#     return render(request , 'datapath.html')

# def decoder(request):
#     return render(request , 'decoder.html')

# def request(request):
#     print(request.GET.get('test'))
#     return JsonResponse({'test_confirmed': True})
#     # return render(request , 'decoder.html')
    


@csrf_exempt
def assemble_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get('code', '')
        

        
        hex_output = main(code)
        sudo_or_base  = checkpsudo(code)
        execution = RISCVSimulator()
        
        registers = execution.run(hex_output)
        memory = execution.memory
        
        

        return JsonResponse({'hex': hex_output ,
                             'is_sudo' : sudo_or_base,
                             'registers': registers,
                             'memory': memory}, )
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_memory_values(request, address):
    execution = RISCVSimulator()
    
    memory_values = execution.memory
    return JsonResponse(memory_values, safe=False)