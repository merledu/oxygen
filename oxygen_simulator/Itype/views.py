from django.shortcuts import render

# Create your views here.
def editor(request):
    print("xx")
    return render(request,'index.html')

def datapath(request):
    print("data")
    return render(request , 'datapath.html')

def decoder(request):
    return render(request , 'decoder.html')

