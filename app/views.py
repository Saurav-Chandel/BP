from django.shortcuts import redirect

# Create your views here.

def home(request):
    context = {}
    return redirect("/swagger/")