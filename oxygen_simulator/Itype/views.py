import json
import os
from pathlib import Path
from django.http import JsonResponse
from django.shortcuts import render
from .interperator import main
from .interperator import checkpsudo
from .Datapath import *
from django.views.decorators.csrf import csrf_exempt

execution = RISCVSimulator()

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

def step_instruction(request):
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get('code', '')
        pc = data.get('pc', 0)
        registers = data.get('registers', {})
        memory = data.get('memory', {})

        # Initialize the simulator
        execution = RISCVSimulator()
        execution.pc = pc
        execution.registers = registers
        execution.memory = memory

        # Split the code into instructions
        instructions = [line for line in code.split('\n') if line.strip()]
        # Execute the current instruction
        current_instruction = instructions[pc]
        hex_output = main(current_instruction)
        execution.run(hex_output)

        # Return the updated state
        return JsonResponse({
            'pc': execution.pc + 1,
            'registers': execution.registers,
            'memory': execution.memory
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)