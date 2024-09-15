import asyncio
from django.http import JsonResponse
from .simulator import Simulator  # type: ignore # Import the Simulator class

# Global variable to keep track of the Simulator instance
simulator = None

async def assemble(request):
    global simulator
    if simulator is None:
        simulator = Simulator()  # Create a new instance of the Simulator

    await simulator.start()  # This will terminate any existing process and start a new one
    return JsonResponse({'status': 'Simulator started'})

async def step(request):
    global simulator
    if simulator is None:
        return JsonResponse({'output': "Simulator not started"})

    result = await simulator.step()
    return JsonResponse({'output': result})

async def get_registers(request):
    global simulator
    if simulator is None:
        return JsonResponse({'output': "Simulator not started"})

    result = await simulator.get_registers()
    return JsonResponse({'output': result})