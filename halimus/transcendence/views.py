from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpRequest
from .forms import UserForm
from .models import User

def register_page(request):
    return render(request,'index.html')

def register_user(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('halis2')
        else:
            print(form.errors)
    
    users = User.objects.all()
    return render(request,'index.html',{'users':users})