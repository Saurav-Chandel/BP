from django.shortcuts import render
from django.shortcuts import render , redirect , HttpResponseRedirect,HttpResponse
from django.views import  View
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, get_user_model,login
from django.contrib.auth.hashers import  check_password
# from rest_framework import filters, permissions, serializers, status, viewsets
from .models import *
from user.models import User,Profile


def Login(request):
    dictValues={}
    dictValues['error'] = None
    if request.method=='POST':
        Email=request.POST.get('email')
        Password=request.POST.get('password')
        try:
            u=User.objects.get(email=Email,is_superuser=True)
            if u.check_password(Password):
                login(request,u)
             
                return HttpResponseRedirect('/adminapp/dashboard/')
            else:
                dictValues['error'] = 'Invalid username/password combination'
        except:
            dictValues['error'] = 'You are not an admin.'
    return render(request,'login.html',dictValues)



@login_required(redirect_field_name='next', login_url='/adminapp/login/')
def dashboard(request):
    data=Profile.objects.all()
    return render(request,'dashboard.html',{'data':data})

@login_required(redirect_field_name='next', login_url='/adminapp/login/')
def buisness_management(request):
    data=Buisness.objects.all()
    return render(request,'buisness_management.html',{'data':data})    

@login_required(redirect_field_name='next', login_url='/adminapp/login/')
def report_management(request):
    data=Report.objects.all()
    return render(request,'report_management.html',{'data':data})    

def suspend(request):
    if request.method == 'GET':
        btn=request.GET.get('mybtn')
        Suspend=User.objects.filter(id=btn,is_active=True).values('is_active').update(is_active=False)
        return render(request,'dashboard.html')


@login_required(redirect_field_name='next', login_url='/adminapp/login/')
def user_management(request):
    data=Profile.objects.all()
    return render(request,'user_management.html',{'data':data}) 

from app.SendinSES import *
from user.models import *
class forgot_password(View):
    def get(self,request):
        return render(request,'forgot_password.html') 

    def post(self,request):
        user_email=request.POST.get('email')
        email_body="link is send to your email for forgot your password"
        user=User.objects.get(email=user_email)
        if user:
           send_reset_password_mail(request,user_email,email_body)

        return render(request,'forgot_password.html') 


# @login_required(redirect_field_name='next', login_url='/adminapp/login/')
class  Change_Password(View):
    def get(self,request):
        return render(request,'change_password.html') 

    def post(self,request):    
        old=request.POST.get('old_password')
        print(old)
        new=request.POST.get('new_password')
        print(new)
        # user=User.objects.get(id=user_id)
        u=User.objects.get(password=old)
        print(u)
        if u.checkpassword(old):
            u.set_password(new)
            u.save()
            return HttpResponse('your password is changed')
        return HttpResponse("password did not match")

        # user=User.objects.get(id=user_id)
        # if user.check_password(old_password):
        #     user=User.objects.get(id=user_id)
        #     user.set_password(new_password)
        #     user.save()
        #     return Response({'msg':'your password is changed'})
        # return Response({'msg':'password did not match'})    

    # data=Profile.objects.all()
    # print(data)
    


from django.contrib import auth

def logout(request):
    auth.logout(request)
    return redirect('login')
