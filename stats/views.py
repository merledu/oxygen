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
        dic = st.get_instruction_stats(code)
        return JsonResponse({'stats': dic },)
    else:
        
        return JsonResponse({'error': 'Invalid request'}, status=400)
