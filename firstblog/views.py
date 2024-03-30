from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import ListView, TemplateView
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .models import Post
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.shortcuts import render


class BlogListView(ListView):
    model = Post
    template_name = 'blog/home.html'

class PostView(View):
    """"вывод записей"""

    def get(self, request):
        posts = Post.objects.all()
        return render(request, 'blog/home.html', {'post_list': posts})

class AboutPageView(TemplateView):
    template_name = 'blog/about.html'

class InputPageView(TemplateView):
    template_name = 'blog/imput.html'
def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        user = User.objects.create_user(username=username, password=password, email=email)
        if request.POST.get('status') == 'admin':
            user.groups.add(Group.objects.get(name='clients'))
            return redirect('admin:index')
        else:
            user.groups.add(Group.objects.get(name='Авторы'))
            return redirect('home')  # Перенаправление на административную панель
    return render(request, 'register.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')  # Перенаправление на административную панель
    return render(request, 'login.html')

def logout(request):
    auth_logout(request)
    return redirect('home')

def post_list(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, 1)  # Показывать по 1 записи на странице

    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return render(request, 'blog/home.html', {'page_obj': page_obj})