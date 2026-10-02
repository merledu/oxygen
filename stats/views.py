import json
from django.http import JsonResponse
from Temp import stats as st


def gen_stats(request):
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get('code', '')
        total_ins, jump_ins, data_transfer_ins, alu_ins, i_ins, m_ins, s_ins, f_ins, c_ins = st.get_instruction_stats(code)
        return JsonResponse({
            'total_ins': total_ins,
            'total_cycles': total_ins,   # CPI=1 approximation
            'jump_ins': jump_ins,
            'data_transfer_ins': data_transfer_ins,
            'alu_ins': alu_ins,
            'i_ins': i_ins,
            'm_ins': m_ins,
            's_ins': s_ins,
            'f_ins': f_ins,
            'c_ins': c_ins,
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)
