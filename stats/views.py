import json
from django.http import JsonResponse
from django.shortcuts import render
import globals
from Temp import stats as st

def gen_stats(request):
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get('code', '')
        globals.code = code
        total_ins, jump_ins, data_transfer_ins, alu_ins, i_ins, m_ins, s_ins, f_ins, c_ins= st.get_instruction_stats(code)
        print('total ins :  ', total_ins)
        return JsonResponse({'total_ins': total_ins, 
                             'jump_ins': jump_ins,
                             'data_transfer_ins': data_transfer_ins,
                             'alu_ins': alu_ins,
                             'i_ins': i_ins,
                             'm_ins': m_ins,
                             's_ins': s_ins,
                             'f_ins': f_ins,
                             'c_ins': c_ins}
                            )
    else:
        
        return JsonResponse({'error': 'Invalid request'}, status=400) 
