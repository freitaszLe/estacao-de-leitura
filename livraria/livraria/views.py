from django.http import HttpResponse
from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def menu(request):
    return render(request, 'menu.html')

def alugar(request):
    return render(request, 'alugar.html')

def about(request):
    return render(request, 'about.html')

def book(request):
    return render(request, 'book.html')