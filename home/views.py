from django.http import HttpResponse
from django.shortcuts import render
from goods.models import Product


def index(request):
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')