import json
import os
from pathlib import Path
from django.http import JsonResponse
from django.shortcuts import render
from .interperator import main
from .interperator import checkpsudo
from .Datapath import *
from .Datapath_single import *
from django.views.decorators.csrf import csrf_exempt

execution = RISCVSimulatorSingle()

# Create your views here.
@csrf_exempt
def editor(request):
    print("xx")
    return render(request,'index.html')

@csrf_exempt
def assemble_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        
        code = data.get('code', '')
 
        hex_output = main(code)
        sudo_or_base  = checkpsudo(code)
        return JsonResponse({'hex': hex_output ,
                             'is_sudo' : sudo_or_base,
                             }, )
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def step_code(request):
    if request.method == "POST":
        print("check")
        data = json.loads(request.body)
        
        instruction = data.get('instruction', '')
        pc = data.get('pc', '')
        
        memory = data.get('memory', '')
        register = data.get('register', '')
 
        execution.pc = pc
        if (pc != 0):
            execution.memory = memory
            execution.registers = register
            
        register=execution.run(instruction)
        memory = execution.memory
        pc = execution.pc
        print(pc)
        
        return JsonResponse({'memory': memory ,
                             'register' : register,
                             'pc': pc,}, )
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def run_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        
        code = data.get('code', '')
 
        hex_output = main(code)
        sudo_or_base  = checkpsudo(code)
        execution2 = RISCVSimulator()
        
        registers = execution2.run(hex_output)
        memory = execution2.memory
        return JsonResponse({'hex': hex_output ,
                             'is_sudo' : sudo_or_base,
                             'registers': registers,
                             'memory': memory}, )
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def reset(request):
    if request.method == "POST":
        execution.memory={}
        execution.registers=[0]*32
        execution.pc=0
        execution.instruction_memory = {}
        execution.f_registers = [0.0] * 32 
        
        return JsonResponse({
                             'register': execution.registers,
                             'memory': execution.memory,
                             'pc':execution.pc}, )
    return JsonResponse({'error': 'Invalid request'}, status=400)