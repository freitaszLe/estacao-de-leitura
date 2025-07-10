from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def menu(request):
    return render(request, 'comprar.html')

def alugar(request):
    return render(request, 'alugar.html')

