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



@login_required(redirect_field_name='next', login_url='/')
def dashboard(request):
    data=Profile.objects.all()
    return render(request,'dashboard.html',{'data':data})

@login_required(redirect_field_name='next', login_url='/')
def buisness_management(request):
    data=Buisness.objects.all()
    return render(request,'buisness_management.html',{'data':data})    

@login_required(redirect_field_name='next', login_url='/')
def report_management(request):
    data=Report.objects.all()
    return render(request,'report_management.html',{'data':data})    

def suspend(request):
    if request.method == "GET":
        btn=request.GET.get('mybtn')
        Suspend=Suspend_User.objects.get(profile__user_id__.is_active==False)


@login_required(redirect_field_name='next', login_url='/')
def user_management(request):
    data=Profile.objects.all()
    return render(request,'user_management.html',{'data':data}) 


# @login_required(redirect_field_name='next', login_url='/')
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
