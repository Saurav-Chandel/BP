
from django.shortcuts import redirect, render
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, permissions, serializers, status, viewsets
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from .serializers import *
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from app.response import ResponseBadRequest, ResponseNotFound, ResponseOk
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import (
    DjangoUnicodeDecodeError,
    smart_bytes,
    smart_str,
)
from rest_framework_simplejwt import authentication
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from django.http import Http404, HttpResponsePermanentRedirect
from django.contrib.auth import login, authenticate
from app.SendinSES import *
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse 
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q,F



# Create your views here.

class SignUpView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        operation_description="User Sign up API",
        operation_summary="User Sign up API",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "first_name": openapi.Schema(type=openapi.TYPE_STRING),
                "email": openapi.Schema(type=openapi.TYPE_STRING),
                "password": openapi.Schema(type=openapi.TYPE_STRING),
                'user_type':openapi.Schema(type=openapi.TYPE_INTEGER , description="enter user_type_id"),
            },
        ),
    )

    @csrf_exempt
    def post(self, request):
        data = request.data
        username=str(data.get('email')) + "_" + str(data.get("user_type"))
        data["username"] = username

        if User.objects.filter(email=data["email"]).exists():
            return ResponseBadRequest(
                {
                    "data": {"email": "Email Already Exist"},
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Serializer error",
                }
            )
        serializer = UserSignupSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return ResponseOk(
                {
                    "data": serializer.data,
                    "code": status.HTTP_200_OK,
                    "message": "User created successfully",
                }
            )
        else:
            return ResponseBadRequest(
                {
                    "data": serializer.errors,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Serializer error",
                }
            )

class LoginView(APIView):
    """
    login user api
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        operation_description="User login API",
        operation_summary="User login API",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING),
                "password": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )

    @csrf_exempt
    def post(self, request):
        data = request.data
        email = data.get("email")
        password = data.get("password")
        username = data['email']

        try:
            user_object = User.objects.get(email=email)
        except User.DoesNotExist:
            return ResponseBadRequest(
                {
                    "data": "User not found",
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Serializer error",
                }
            )
        try:
            user_object=User.objects.get(username__iexact=username)
            if not user_object.is_active:
                return ResponseBadRequest(
                    {
                        "code":status.HTTP_400_BAD_REQUEST,
                        "message":"you are suspened user"
                    }
                )   
            else:
                return ResponseBadRequest({
                "msg":'user not found'
            })

        except:    
            if user_object.check_password(password):
                print("password match")
                token = RefreshToken.for_user(user_object)
                print(token)
                if not Token.objects.filter(
                    token_type="access_token", user_id=user_object.id
                ).exists():
                    Token.objects.create(
                        user_id=user_object.id,
                        token=str(token.access_token),
                        token_type="access_token",
                    )
                else:
                    Token.objects.filter(
                        user_id=user_object.id, token_type="access_token"
                    ).update(token=str(token.access_token))
                serializer = UserSerializer(user_object)
    
                return Response(
                    {
                        "data": serializer.data,
                        "access_token": str(token.access_token),
                        "refresh_token": str(token),
                        "code": status.HTTP_200_OK,
                        "message": "Login SuccessFully",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return ResponseBadRequest(
                    {
                        "data": "wrong credentials",
                        "code": status.HTTP_400_BAD_REQUEST,
                        "message": "Serializer error",
                    }
                )          
    

class RequestPasswordResetEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Password reset email",
        operation_summary="Password reset email",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING),
                "redirect_url": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="enter redirect url example: https://www.google.com",
                ),
            },
        ),
    )
    @csrf_exempt
    def post(self, request):

        data = request.data
        email = data.get("email")
        redirect_url = data.get("redirect_url")

        if User.objects.filter(
            email=email
        ).exists():
            user = User.objects.get(
                email=email
            )

            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            current_site = get_current_site(request=request).domain
            relativeLink = reverse(
                "user:forgot-password-confirm",
                kwargs={"uidb64": uidb64, "token": token},
            )
    
            absurl = (
                "http://"
                + current_site
                + relativeLink
                +"?redirect_url="
                + redirect_url
            )
            print(absurl)
            email_body = (
                "Hello, \n Use link below to reset your password  \n" + absurl
            )
        
            send_reset_password_mail(request, user.email, email_body)
            return Response(
                {"success": "We have sent you a link to reset your password"},
                status=status.HTTP_200_OK,
            )
        else:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "User Does Not Exist",
                }
            )

class PasswordTokenCheckAPIView(APIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [permissions.AllowAny]

    @csrf_exempt
    def get(self, request, uidb64, token):

        redirect_url = request.GET.get("redirect_url")

        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return HttpResponsePermanentRedirect(
                    redirect_url + "?token_valid=False"
                )
  
            if redirect_url and len(redirect_url) > 3:
                return HttpResponsePermanentRedirect(
                    redirect_url
                    + "?token_valid=True&uidb64="
                    + uidb64
                    + "&token="
                    + token
                )
            else:
                return HttpResponsePermanentRedirect(
                    redirect_url + "?token_valid=False"
                )

        except DjangoUnicodeDecodeError as identifier:

            try:
                if not PasswordResetTokenGenerator().check_token(user):
                    return HttpResponsePermanentRedirect(
                        redirect_url + "?token_valid=False"
                    )

            except UnboundLocalError as e:
                return Response(
                    {"error": "Token is not valid, please request a new one"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

class SetNewPasswordAPIView(APIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        operation_description="Set new password",
        operation_summary="Set new password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "password": openapi.Schema(type=openapi.TYPE_STRING),
                "token": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="token",
                ),
                "uidb64": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="uidb64",
                ),
            },
        ),
    )
    @csrf_exempt
    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"success": True, "message": "Password reset success"},
            status=status.HTTP_200_OK,
        )
from django.db.models import Count
class GetAllProfile(APIView):
    """
    Get profile
    """
    # permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.JWTAuthentication]

    city = openapi.Parameter('city',
                            in_=openapi.IN_QUERY,
                            description='Search by city',
                            type=openapi.TYPE_STRING,
                            )
    state = openapi.Parameter('state',
                            in_=openapi.IN_QUERY,
                            description='Search by state',
                            type=openapi.TYPE_STRING,
                            )   
    country = openapi.Parameter('country',
                            in_=openapi.IN_QUERY,
                            description='Search by country',
                            type=openapi.TYPE_STRING,
                            )    
    profile_id = openapi.Parameter('profile_id',
                            in_=openapi.IN_QUERY,
                            description='enter profile_id',
                            type=openapi.TYPE_INTEGER,
                            )                                                                       


    @swagger_auto_schema(
            manual_parameters=[city,state,country,profile_id]
    )

    @csrf_exempt
    def get(self, request):
        try:
            data=request.GET
           
            if data.get('city'):     
                city=data.get('city')
            else:
                city=""
            print(city)    
            
            if data.get('state'):
                state=data.get('state')
            else:
                state=""    
            print(state)   

            if data.get('country'):
                country=data.get('country')
            else:
                country="" 

            if data.get('profile_id'):
                profile_id=data.get('profile_id')
            else:
                profile_id=""  
            print(profile_id)
    
            profile=Profile.objects.all()

            # calculate total_host_match by annotate function pass related_name😎😎
            # host_match_count=Profile.objects.filter(id=1).annotate(host_match=Count('hostmatch_profile'))
            # q=host_match_count.values('host_match')
            # print(q) 

            # if profile_id:
            #     #this is loc is calculate the rating and give a better respone to front end team.
            #     rat=PlayersRating.objects.filter(player=profile_id).aggregate(rating=Avg('rating'))
            #     for elem in rat.values():
            #         print(elem)
            #         p1=Profile.objects.filter(id=profile_id).update(rating=elem)
                
            #     #calculate total_host_match by annotate function.😎😎

            #     # host_match_count=Profile.objects.filter(id=profile_id).annotate(host_match=Count('hostmatch_profile'))
            #     # print(host_match_count.values('host_match'))
            #     # p=Profile.objects.filter(id=profile_id).update(hostmatch=host_match_count.values_list('host_match'))

            #     #another way to calculate host_match through queries.😎😎
            #     h=HostMatch.objects.filter(profile_id=profile_id).values('profile_id')
            #     p=Profile.objects.filter(id__in=h).update(hostmatch=h.count())
            
            if city:
                profile=profile.filter(Q(city__icontains=city))  
                print(profile)
            if state:
                profile=profile.filter(Q(state__icontains=state)) 

            if country:
                profile=profile.filter(Q(country__icontains=country))     

            if profile:
                serializer=GetProfileSerializer(profile,many=True) 
               
                return Response({
                    'data':serializer.data,
                    'status':status.HTTP_200_OK,
                    'msg':'All profiles by given search'
                })                 
            else:
                return Response({'msg':'search not found'})
        except:
            return Response({'msg':'search query does not found'})        

# class CreateProfile(APIView):
#     """
#     Create Profile
#     """

#     permission_classes = [permissions.IsAuthenticated]
#     authentication_classes = [authentication.JWTAuthentication]
#     parser_classes = (FormParser, MultiPartParser)

#     @swagger_auto_schema(
#         operation_description="create Profile",
#         request_body=ProfileSerializer,
#     )

#     @csrf_exempt
#     def post(self, request):
#         serializer = ProfileSerializer(data=request.data)
#         if serializer.is_valid():
#             user_obj=serializer.save()
            
#             user_obj=User.objects.filter(id=user_obj.id)[0]
#             user_serializer=UserSerializer(user_obj)
#             print(user_serializer)

#             return ResponseOk(
#                 {
#                     "data": user_serializer.data,
#                     # "user_id":GetProfileSerializer(),
#                     "code": status.HTTP_200_OK,
#                     "message": "Profile created succesfully",
#                 }
#             )
#         else:    
#             return ResponseBadRequest(
#                 {
#                     "data": serializer.errors,
#                     "code": status.HTTP_400_BAD_REQUEST,
#                     "message": "Profile is not valid",
#                 }
#             )

class UpdateProfile(APIView):
    """
    Update Profile
    """

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.JWTAuthentication]
    parser_classes = (FormParser, MultiPartParser)

    def get_object(self, pk):
        try:
            return Profile.objects.get(pk=pk)
        except Profile.DoesNotExist:
            raise ResponseNotFound()

    @swagger_auto_schema(
        operation_description="update Profile",
        request_body=ProfileSerializer,
    )
    @csrf_exempt
    def put(self,request,pk):
        try:
            profile=self.get_object(pk)
            serializer=ProfileSerializer(profile,data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseOk(
                    {
                        "data":serializer.data,
                        "code":status.HTTP_200_OK,
                        "message":"Profile updated successfully"
                    }
                )
            else:
                return ResponseBadRequest(
                    {
                        "data":serializer.errors,
                        "code":status.HTTP_400_BAD_REQUEST,
                        "message":"Profile Not Valid"
                    }
                )  
        except:
            return  ResponseBadRequest(
                {
                    "data":None,
                    "code":status.HTTP_400_BAD_REQUEST,
                    "message":"Profile Does Not exists."
                }
            )          

class GetProfile(APIView):
    """
    Get Profile by id
    """

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.JWTAuthentication]

    def get_object(self, pk):
        try:
            return Profile.objects.get(pk=pk)
        except Profile.DoesNotExist:
            raise ResponseNotFound()

   
    def get(self,request,pk):
        try:
            profile=self.get_object(pk)
            rat=PlayersRating.objects.filter(player=pk).aggregate(rating=Avg('rating'))
            for elem in rat.values():
                print(elem)
            p1=Profile.objects.filter(id=pk).update(rating=elem)
            
            #calculate total_host_match by annotate function.😎😎
            # host_match_count=Profile.objects.filter(id=profile_id).annotate(host_match=Count('hostmatch_profile'))
            # print(host_match_count.values('host_match'))
            # p=Profile.objects.filter(id=profile_id).update(hostmatch=host_match_count.values_list('host_match'))
            
            #another way to calculate host_match through queries.😎😎
            h=HostMatch.objects.filter(profile_id=pk).values('profile_id')
            p=Profile.objects.filter(id__in=h).update(hostmatch=h.count())
            print(h.count())

            serializer=GetProfileSerializer(profile)
            return ResponseOk(
                {
                    "data":serializer.data,
                    "code":status.HTTP_200_OK,
                    "message":"Get Profile successfully"
                }
            )
           
        except:
            return  ResponseBadRequest(
                {
                    "data":None,
                    "code":status.HTTP_400_BAD_REQUEST,
                    "message":"Profile Does Not exists."
                }
            )    

class DeleteProfile(APIView):
    """
    Delete Profile
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.JWTAuthentication]


    @csrf_exempt
    def get_object(self, pk):
        try:
            return Profile.objects.get(pk=pk)
        except Profile.DoesNotExist:
            raise ResponseNotFound()

    def delete(self, request, pk):
        try:
            profile = self.get_object(pk)
            profile.delete()
            return ResponseOk(
                {
                    "data": None,
                    "code": status.HTTP_200_OK,
                    "message": "Profile deleted Successfully",
                }
            )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Profile Does Not Exist",
                }
            )
            
from django.db.models.functions import Greatest
from django.db.models import Avg
from datetime import datetime
class GetAllHostMatch(APIView):
    """
    Get All HostMatch
    """
    # permission_classes=(IsAuthenticated,)

    search = openapi.Parameter('search',
                            in_=openapi.IN_QUERY,
                            description='Search by location',
                            type=openapi.TYPE_STRING,
                            )
    date = openapi.Parameter('date',
                            in_=openapi.IN_QUERY,
                            description='Search by date',
                            type=openapi.TYPE_STRING,
                            )      

    user_id = openapi.Parameter('user_id',
                            in_=openapi.IN_QUERY,
                            description='enter user_id',
                            type=openapi.TYPE_INTEGER,
                            )  

    hosted_completed = openapi.Parameter('complete',
                            in_=openapi.IN_QUERY,
                            description='pass true if you want to get a list of match is completed',
                            type=openapi.TYPE_BOOLEAN,
                            )  
    hosted_ongoing = openapi.Parameter('ongoing',
                            in_=openapi.IN_QUERY,
                            description='pass true if you want to get a list of match is ongoing',
                            type=openapi.TYPE_BOOLEAN,
                            )   

    host_match = openapi.Parameter('host_match',
                            in_=openapi.IN_QUERY,
                            description='find the TeamScore host_match_id',
                            type=openapi.TYPE_STRING,
                            )                                                                                                                                     

    @swagger_auto_schema(
            manual_parameters=[search,date,hosted_completed,hosted_ongoing,user_id,host_match]
    )

    @csrf_exempt
    def get(self, request):
        try:
            data=request.GET
            if data.get("search"):
                query=data.get('search')
            else:
                query=""   

            if data.get("date"):
                date=data.get('date')
            else:
                date=""

            if data.get("user_id"):
                user=data.get('user_id')
            else:
                user=""    
             
            if data.get("complete"):
                completed=data.get('complete')
            else:
                completed=""   

            if data.get("ongoing"):
                ongoing=data.get('ongoing')
            else:
                ongoing="" 

            if data.get("host_match"):
                host=data.get('host_match')
            else:
                host=""       

            host_match=HostMatch.objects.all()
            print(host_match)

            # if user:
            #     a=HostMatch.objects.filter(profile_id=user).values('profile_id')
            #     print(a)
            #     b=Profile.objects.filter(id__in=a).update(hostmatch=a.count())
            #     print(b)
            
               
            if host:
                host_match=host_match.filter(user_id=host)
                print(host_match)
                print("_______")
                team1_score=list(HostMatch.objects.filter(user_id=host).annotate(Avg('host_score__team1_player_score')).values_list('host_score__team1_player_score__avg'))
                print(team1_score)
                    
                print("_______")

                team2_score=list(HostMatch.objects.filter(user_id=host).annotate(Avg('host_score__team2_player_score')).values_list('host_score__team2_player_score__avg'))
                print(team2_score)

                print("_____")

                if team1_score>team2_score:
                    host_invited=HostInvitation.objects.filter(hostmatch_id=host)
                    print(host_invited[0])

                    print("player 1 wins")

                if team1_score<team2_score:
                    host_invited=HostInvitation.objects.filter(hostmatch_id=host)
                    print(host_invited[1])
                    
                    print("player 2 wins")    


                # max_score=HostMatch.objects.filter(user_id=host).annotate(res=Greatest(Avg('host_score__team1_player_score'),(Avg('host_score__team2_player_score')))).values()
                # print(max_score)
                # print("____")
            
        
            if query:
                host_match=host_match.filter(Q(location__icontains=query))

            if date:
                host_match=host_match.filter(Q(date__icontains=date)) 

            if completed:
                date = datetime.today()
                # time = datetime.now().time() 
                host_match=host_match.filter(user_id=user,date__lte=date)

            if ongoing:
                date = datetime.today()
                # time = datetime.now().time() 
                host_match=host_match.filter(user_id=user,date__gte=date)
            
            if host_match:
                serializer=GetHostMatchSerializer(host_match,many=True)
                return ResponseOk(
                    {
                        "data": serializer.data,
                        "code": status.HTTP_200_OK,
                        "message": "HostMatch list",
                    }
                )
            else:
                return Response({'msg':'search not found'})    
        except:
            return Response({'msg':'search query does not found'})


class CreateHostMatch(APIView):
    """
    Create HostMatch
    """
    
    # permission_classes=(IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser)


    @swagger_auto_schema(
        operation_description="create HostMatch",
        request_body=HostMatchSerializer,
    )
    @csrf_exempt
    def post(self, request):
        serializer = HostMatchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # add=Profile.objects.filter(user_id=request.data['user_id']).update(hostmatch=hostmatch+1)
            return ResponseOk(
                {
                    "data": serializer.data,
                    "code": status.HTTP_200_OK,
                    "message": "HostMatch created succesfully",
                }
            )
            
        else:    
            
            return ResponseBadRequest(
                {
                    "data": serializer.errors,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "HostMatch is not valid",
                }
            )



class GetHostMatch(APIView):
    """
    Get HostMatch by pk
    """
    permission_classes=(IsAuthenticated,)
    


    csrf_exempt
    def get_object(self, pk):
        try:
            return HostMatch.objects.get(pk=pk)
        except HostMatch.DoesNotExist:
            raise ResponseNotFound()

    def get(self, request, pk):
        try:
            host_match = self.get_object(pk)
            serializer = GetHostMatchSerializer(host_match)
            return ResponseOk(
                {
                    "data": serializer.data,
                    "code": status.HTTP_200_OK,
                    "message": "get HostMatch successfully",
                }
            )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "HostMatch Does Not Exist",
                }
            )


class UpdateHostMatch(APIView):
    """
    Update HostMatch
    """
    permission_classes=(IsAuthenticated,)

    parser_classes = (FormParser, MultiPartParser)


    def get_object(self, pk):
        try:
            return HostMatch.objects.get(pk=pk)
        except HostMatch.DoesNotExist:
            raise ResponseNotFound()

    @swagger_auto_schema(
        operation_description="update HostMatch",
        request_body=HostMatchSerializer,
    )
    @csrf_exempt
    def put(self, request, pk):
        try:
            host_match = self.get_object(pk)
            serializer = HostMatchSerializer(host_match, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseOk(
                    {
                        "data": serializer.data,
                        "code": status.HTTP_200_OK,
                        "message": "HostMatch updated successfully",
                    }
                )
            else:
                return ResponseBadRequest(
                    {
                        "data": serializer.errors,
                        "code": status.HTTP_400_BAD_REQUEST,
                        "message": "HostMatch Not valid",
                    }
                )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "HostMatch Does Not Exist",
                }
            )

class DeleteHostMatch(APIView):
    """
    Delete HostMatch
    """
    permission_classes=(IsAuthenticated,)

    @csrf_exempt
    def get_object(self, pk):
        try:
            return HostMatch.objects.get(pk=pk)
        except HostMatch.DoesNotExist:
            raise ResponseNotFound()

    def delete(self, request, pk):
        try:
            host_match = self.get_object(pk)
            host_match.delete()
            return ResponseOk(
                {
                    "data": None,
                    "code": status.HTTP_200_OK,
                    "message": "HostMatch deleted Successfully",
                }
            )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "HostMatch Does Not Exist",
                }
            )

class GetAllHostInvitation(APIView):
    """
    Get All HostInvitation
    """
    # permission_classes=(IsAuthenticated,)
    host_match = openapi.Parameter('host_match',
                            in_=openapi.IN_QUERY,
                            description='find the invited_users who status is Attends by host_match_id',
                            type=openapi.TYPE_STRING,
                            )  

    user_invited = openapi.Parameter('user_invited',
                            in_=openapi.IN_QUERY,
                            description='find the invitations send by host match by the user_invited_id  ',
                            type=openapi.TYPE_STRING,
                            )   

    attend_completed = openapi.Parameter('complete',
                            in_=openapi.IN_QUERY,
                            description='pass true if you want to get a list of match is completed and attended also',
                            type=openapi.TYPE_BOOLEAN,
                            )

    atttend_ongoing = openapi.Parameter('ongoing',
                            in_=openapi.IN_QUERY,
                            description='pass true if you want to get a list of match is ongoing and attended also',
                            type=openapi.TYPE_BOOLEAN,
                            )                          
                          
    @swagger_auto_schema(
            manual_parameters=[host_match,user_invited,attend_completed,atttend_ongoing]
    )

    @csrf_exempt
    def get(self, request):
        try:
            data=request.GET
            if data.get('user_invited'):     
                user_invited=data.get('user_invited')
            else:
                user_invited=""

            if data.get('host_match'):     
                host_match=data.get('host_match')
            else:
                host_match="" 
            print(host_match)       

            if data.get("complete"):
                completed=data.get('complete')
            else:
                completed=""   

            if data.get("ongoing"):
                ongoing=data.get('ongoing')
            else:
                ongoing=""        

            host_invitation=HostInvitation.objects.all()
        
            if host_match:
                host_invitation=host_invitation.filter(hostmatch_id=host_match,status='Attend')
                print(host_invitation)

                team1_score=list(HostMatch.objects.filter(profile_id=host_match).annotate(Avg('host_score__team1_player_score')).values_list('host_score__team1_player_score__avg'))
                print(team1_score)
                print("_______")
             
                team2_score=list(HostMatch.objects.filter(profile_id=host_match).annotate(Avg('host_score__team2_player_score')).values_list('host_score__team2_player_score__avg'))
                print(team2_score)
                
                print("_____")

                if team1_score>team2_score:
                    print(host_invitation[0])
                    # print(host_invitation.count())
                    print("player 1 wins")
                    # print(host_match[0])

                if team1_score<team2_score:
                    print(host_invitation[1])
                    # print(host_invitation.count())
                    print("player 2 wins")
                    print(host_match[1])
              
            if user_invited:
                host_invitation=host_invitation.filter(user_invited=user_invited)
                if completed:
                    date = datetime.today()
                    # time = datetime.now().time() 
                    host_invitation=HostInvitation.objects.filter(user_invited=user_invited,status='Attend').values('hostmatch_id')
                    print(host_invitation)
                    host_match=HostMatch.objects.filter(id__in=host_invitation,date__lte=date).values()
                    print(host_match)

                    #total match played by player.
                    match_played=HostInvitation.objects.filter(user_invited=user_invited,status='Attend').values()

                    #update the value of matchplayed in profile table.
                    Profile.objects.filter(user_id=user_invited).update(matchplayed=match_played.count())

                    return Response({
                        'match_played':match_played.count(),
                        'data':host_match,
                        'msg':'My Attending or Completed Matches List',
                        'status':200
                            })
                if ongoing:
                    date = datetime.today()
                    # time = datetime.now().time() 
                    host_invitation=HostInvitation.objects.filter(user_invited=user_invited,status='Attend').values('hostmatch_id')
                    host_match=HostMatch.objects.filter(id__in=host_invitation,date__gte=date).values()
                    print(host_match)
                    return Response({
                        'data':host_match,
                        'msg':'My Attending or Ongoing Matches List',
                        'status':200
                            })
            
            if host_invitation:
        
                serializer=HostInvitationSerializer(host_invitation,many=True)
                return ResponseOk(
                    {
                        "data": serializer.data,
                        "code": status.HTTP_200_OK,
                        "message": "HostInvitation list",
                    }
                )
            else:
                return Response({'msg':'hostinvitation does not found'})
        except:
            return Response({'msg':'hostinvitation1 does not found'})    


class CreateHostInvitation(APIView):
    """
    Create HostInvitation
    """
    
    # permission_classes=(IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser)

    @swagger_auto_schema(
        operation_description="create HostInvitation",
        request_body=HostInvitationSerializer,
    )
    @csrf_exempt
    def post(self, request):
        serializer = HostInvitationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ResponseOk(
                {
                    "data": serializer.data,
                    "code": status.HTTP_200_OK,
                    "message": "HostInvitation created succesfully",
                }
            )
            
        else:    
            
            return ResponseBadRequest(
                {
                    "data": serializer.errors,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "HostInvitation is not valid",
                }
            )

class GetHostInvitation(APIView):
    """
    Get HostInvitation by pk
    """
    permission_classes=(IsAuthenticated,)
    
    csrf_exempt
    def get_object(self, pk):
        try:
            return HostInvitation.objects.get(pk=pk)
        except HostInvitation.DoesNotExist:
            raise ResponseNotFound()

    def get(self, request, pk):
        try:
            host_invitation = self.get_object(pk)
            serializer = HostInvitationSerializer(host_invitation)
            return ResponseOk(
                {
                    "data": serializer.data,
                    "code": status.HTTP_200_OK,
                    "message": "get HostInvitation successfully",
                }
            )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "HostInvitation Does Not Exist",
                }
            )

class UpdateHostInvitation(APIView):
    """
    Update HostInvitation
    """
    permission_classes=(IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser)


    def get_object(self, pk):
        try:
            return HostInvitation.objects.get(pk=pk)
        except HostInvitation.DoesNotExist:
            raise ResponseNotFound()

    @swagger_auto_schema(
        operation_description="update HostInvitation",
        request_body=HostInvitationSerializer,
    )
    @csrf_exempt
    def put(self, request, pk):
        try:
            host_invitation = self.get_object(pk)
            serializer = HostInvitationSerializer(host_invitation, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseOk(
                    {
                        "data": serializer.data,
                        "code": status.HTTP_200_OK,
                        "message": "HostInvitation updated successfully",
                    }
                )
            else:
                return ResponseBadRequest(
                    {
                        "data": serializer.errors,
                        "code": status.HTTP_400_BAD_REQUEST,
                        "message": "HostInvitation Not valid",
                    }
                )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "HostInvitation Does Not Exist",
                }
            )


class DeleteHostInvitation(APIView):
    """
    Delete HostInvitation
    """
    permission_classes=(IsAuthenticated,)

    @csrf_exempt
    def get_object(self, pk):
        try:
            return HostInvitation.objects.get(pk=pk)
        except HostInvitation.DoesNotExist:
            raise ResponseNotFound()

    def delete(self, request, pk):
        try:
            host_invitation = self.get_object(pk)
            host_invitation.delete()
            return ResponseOk(
                {
                    "data": None,
                    "code": status.HTTP_200_OK,
                    "message": "HostInvitation deleted Successfully",
                }
            )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "HostInvitation Does Not Exist",
                }
            )


#Team Score API's
class GetAllTeamScore(APIView):
    """
    Get All TeamScore
    """
    # permission_classes=(IsAuthenticated,)

    host_match = openapi.Parameter('host_match',
                            in_=openapi.IN_QUERY,
                            description='enter host_match id',
                            type=openapi.TYPE_STRING,
                            )
    total_score = openapi.Parameter('total_score',
                            in_=openapi.IN_QUERY,
                            description='maximum score of match',
                            type=openapi.TYPE_STRING,
                            )   
    @swagger_auto_schema(
            manual_parameters=[host_match,total_score]
    )                        

    @csrf_exempt
    def get(self, request):
        try:
            dictV=dict()
            data=request.GET
            if data.get('host_match'):     
                host_match=data.get('host_match')
            else:
                host_match=""

            if data.get('total_score'):
                total_score=data.get('total_score')
            else:
                total_score=""    

            team_score=TeamScore.objects.all()
          
            if not host_match:
                # result=TeamScore.objects.annotate(res=Greatest('team1_player_score','team2_player_score')).values()
                # print(result)
                dictV['msg']="enter a hostmatch_id to get a final result"


            if host_match:
                team_score=team_score.filter(host_match=host_match)
                p1_result=team_score.annotate(Avg('team1_player_score'))
                print(vars(p1_result[0]))
                p2_result=team_score.annotate(Avg('team2_player_score'))
                print(vars(p2_result[0]))


                # team_score=team_score.filter(host_match=host_match)
                # print(team_score)
                # p1_result=team_score.filter(host_match=host_match,team1_player_score=total_score)
                # print(p1_result)
                # p2_result=team_score.filter(host_match=host_match,team2_player_score=total_score)
                # print(p2_result)

                # if len(p1_result)>len(p2_result):
                #     dictV['final_result']="player1 wins"
                    
                # if len(p1_result)<len(p2_result):
                #     dictV['final_result']="player2 wins"

            if team_score:
                serializer=TeamScoreSerializer(team_score,many=True)  
        
                return Response({
                    'data':serializer.data,
                    "winner":dictV,
                    'status':status.HTTP_200_OK,
                    'msg':'list of Team_Score'
                })                 
            else:
                return Response({'msg':'hostmatch does not found'})
                
        except:
            return Response({"Team_Score does not find"})


class CreateTeamScore(APIView):
    """
    Create TeamScore
    """
    
    permission_classes=(IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser)

    @swagger_auto_schema(
        operation_description="create TeamScore",
        request_body=TeamScoreSerializer,
    )
    @csrf_exempt
    def post(self, request):
        serializer = TeamScoreSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ResponseOk(
                {
                    "data": serializer.data,
                    "code": status.HTTP_200_OK,
                    "message": "Team_Score recorded Successfully",
                }
            )
            
        else:    
            
            return ResponseBadRequest(
                {
                    "data": serializer.errors,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Team_Score is not valid",
                }
            )
from django.db.models import Count
from django.db.models.functions import Greatest
class GetTeamScore(APIView):
    """
    Get TeamScore by pk
    """
    # permission_classes=(IsAuthenticated,)  
    
    host_match = openapi.Parameter('host_match',
                            in_=openapi.IN_QUERY,
                            description='enter host_match id',
                            type=openapi.TYPE_STRING,
                            )
    total_score = openapi.Parameter('total_score',
                            in_=openapi.IN_QUERY,
                            description='maximum score of match',
                            type=openapi.TYPE_STRING,
                            )   
    @swagger_auto_schema(
            manual_parameters=[host_match,total_score]
    )                   

    @csrf_exempt
    def get_object(self, pk):
        try:
            return TeamScore.objects.get(pk=pk)
        except TeamScore.DoesNotExist:
            raise ResponseNotFound()

    def get(self, request, pk):
        try:
            team_score = self.get_object(pk)
            player1=team_score.team1_player_score
            player2=team_score.team2_player_score
            dictV=dict()
            if player1>player2:
                dictV['result_']="player1 wins"
                dictV['result']="player2 lose"
            else:   
                dictV['result_']="player2 wins"
                dictV['result']="player1 loss"
    
            # print(vars(team_score))

            # round=TeamScore.objects.annotate(c=Count('round')) 
            # len_round=len(round)
            # print(len_round)
            # print(round)
            
            # for i in range(0,len_round):
            #     round=TeamScore.objects.annotate(c=Count('round')) 
            #     score=round.annotate(res=Greatest('team1_player_score','team2_player_score'))
            #     print(vars(score[0]))

                # print("__________")
                # print(vars(round[i]))
                  
            # print(vars(round[0]))

            serializer = TeamScoreSerializer(team_score)
            return ResponseOk(
                {
                    "data": serializer.data,
                    "result":dictV,
                    "code": status.HTTP_200_OK,
                    "message": "get TeamScore successfully",
                }
            )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "TeamScore Does Not Exist",
                }
            )


class UpdateTeamScore(APIView):
    """
    Update TeamScore
    """
    permission_classes=(IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser)


    def get_object(self, pk):
        try:
            return TeamScore.objects.get(pk=pk)
        except TeamScore.DoesNotExist:
            raise ResponseNotFound()

    @swagger_auto_schema(
        operation_description="update TeamScore",
        request_body=TeamScoreSerializer,
    )
    @csrf_exempt
    def put(self, request, pk):
        try:
            team_score = self.get_object(pk)
            serializer = TeamScoreSerializer(team_score, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseOk(
                    {
                        "data": serializer.data,
                        "code": status.HTTP_200_OK,
                        "message": "TeamScore updated successfully",
                    }
                )
            else:
                return ResponseBadRequest(
                    {
                        "data": serializer.errors,
                        "code": status.HTTP_400_BAD_REQUEST,
                        "message": "TeamScore Not valid",
                    }
                )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "TeamScore Does Not Exist",
                }
            )


class DeleteTeamScore(APIView):
    """
    Delete TeamScore
    """
    permission_classes=(IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser)


    @csrf_exempt
    def get_object(self, pk):
        try:
            return TeamScore.objects.get(pk=pk)
        except TeamScore.DoesNotExist:
            raise ResponseNotFound()

    def delete(self, request, pk):
        try:
            team_score = self.get_object(pk)
            team_score.delete()
            return ResponseOk(
                {
                    "data": None,
                    "code": status.HTTP_200_OK,
                    "message": "TeamScore deleted Successfully",
                }
            )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "TeamScore Does Not Exist",
                }
            )

# class CreateProfileAPI(generics.GenericAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class=ProfileSerializer

#     def post(self,request,*args,**kwargs):
#         serializer=self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         RA=serializer.save()
#         return Response({'msg':'User information saved Successfully','status':200})

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class ResetPasswordAppAPI(generics.GenericAPIView):
    # permission_class=(IsAuthenticated,)
    def post(self, request, *args, **kwargs):
        user_id=request.data['user_id']
        u=User.objects.get(id=user_id)
        pwd=str(request.data['password'])
        u.set_password(pwd)
        u.save()
        return Response({"msg":'Password Updated.',"status":200})

class ContactUsAPI(generics.GenericAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    serializer_class=ContactUsSerializer
    def post(self,request,*args,**kwargs):
        user_id=request.data.get('user_id')
        if user_id:
            serializer=ContactUsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"data":serializer.data,
                                "status":status.HTTP_200_OK,
                                "msg":"contact us created successfully"})
            return Response({"msg":"User_id is already exists"})    

        return Response({"msg":"Enter a user _id"})   

class getContactUsAPI(generics.GenericAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    serializer_class=ContactUsSerializer
    def get(self,request,*args,**kwargs):
        contact_us=ContactUs.objects.all()
        serializer=ContactUsSerializer(contact_us,many=True)
        return Response({"data":serializer.data,
                        "status":status.HTTP_200_OK,
                         "msg":"get list of contact us "})        

class AboutUsAPI(generics.GenericAPIView):
    # permission_classes = [permissions.IsAuthenticated]
    def get(self,request,*args,**kwargs):

        about_us=AboutUs.objects.all()
        serializer=AboutUsSerializer(about_us,many=True)
       
        return Response({
            'data':serializer.data,
            'msg':'About Us',
            'status':200
        })      
    

class PrivacyPolicyAPI(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self,request,*args,**kwargs):
        return Response({
            'data':{'text':PrivacyPolicy.objects.all().values()},
            'msg':'Privacy Policy',
            'status':200
        })            


class TermsConditionAPI(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self,request,*args,**kwargs):
        return Response({
            'data':{'text':TermsCondition.objects.all().values()},
            'msg':'Terms Condition',
            'status':200
        })


class CreateNotification(APIView):
    """
    Create Notification
    """
    # permission_classes=(IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser)

    def get_object(self, pk):
        try:
            return Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            raise ResponseNotFound()

    @swagger_auto_schema(
        operation_description="create Notification",
        request_body=NotificationSerializer,
    )
    @csrf_exempt
    def put(self,request,pk):
        try:
            notification = self.get_object(pk)
            print(notification)
            serializer = NotificationSerializer(notification, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseOk(
                    {
                        "data": serializer.data,
                        "code": status.HTTP_200_OK,
                        "message": "Notification updated successfully",
                    }
                )
            else:
                return ResponseBadRequest(
                    {
                        "data": serializer.errors,
                        "code": status.HTTP_400_BAD_REQUEST,
                        "message": "Notification Not valid",
                    }
                )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Notification Does Not Exist",
                }
            )


class NotificationsAPI(generics.GenericAPIView):
    # permission_classes = (IsAuthenticated,)
    def post(self, request, *args, **kwargs):
        n=Notification.objects.filter(User_id=request.POST['User_id'])
        n.update(Status=request.POST['Status'])
        return Response({
        "data":{"Notifications": n.values('Status','User_id')[0:]},
        "msg":'Notifications Updated successfully.',
        "status":200
        })


import pandas as pd
#Ashima mam code
class Home(generics.GenericAPIView):
    
    # permission_classes=(IsAuthenticated,)
    def post(self,request,*args,**kwargs):
        filters={k: v for k, v in request.data.items() if (v and (k=='city' or k=='State' or k=='Country'))}    # this is used for filtering purpose.
        np=Profile.objects.filter().values()
        Business=Buisness.objects.all().values()
        

        # i dont know why this line of code is added.

        # if not request.POST.get('city',False):
        #     filters['city']=Profile.objects.filter(user_id=request.POST['User']).values()[0]['city']
        # if not request.POST.get('State',False):
        #     filters['State']=Profile.objects.filter(user_id=request.POST['User']).values()[0]['state']

        a=1
        if a==1:
            #update the longitude and latitude of user every time depends on their current changing location.(received as a input)
            profile=Profile.objects.filter(user_id=request.POST['User']).update(lat=request.POST['latitude'],long=request.POST['longitude'])
            lat= float(request.POST['latitude']) #profile['latitude']
            lon= float(request.POST['longitude']) #profile['longitude']
            city = request.POST.get('city', False)    

            if lat or lon: 

                # return all receivers id whoose u already sends a request .
                f1=FriendRequest.objects.filter(sender=request.POST['User']).values_list('receiver')# i send the friend request to others.
                print(f1)
                # if f1:
                #     for i in f1:
                #         a=i['receiver']
                # else:
                #     a='0'
                   
                #return all senders id who is already sends me a friend request. 
                f2=FriendRequest.objects.filter(receiver=request.POST['User']).values_list('sender')  # friend requests recieved by me.
                print(f2)
                # if f2:
                #     for i in f2:
                #         b=i['sender']
                # else:
                #     b='0'     
                friends=list(f1)+list(f2)
                print(friends)
                
                #exclude the user who is already send or receives a friend request.🧨🧨🧨
                p=Profile.objects.filter().exclude(user_id__in=friends).values('id','user_id')
                print(p)
                
                # exclude the given user on the basis of his lat and long, we have to calculate the dstance of other users. 
                all_l=Profile.objects.filter().exclude(user_id=request.POST['User']).exclude(user_id__in=friends).values('id','user_id','city','lat','long','profile_image','hostmatch','matchplayed','matchwon','rating',email_1=F('user_id__email'))  
                print(all_l)
                
                # Searches on the bais of city.😎😎😎
                if city:
                   filter_profile_on_the_basis_of_city=all_l.filter(Q(city__icontains=city))
                   buisness=Buisness.objects.all()
                   return Response({'data':{'NearbyPlayers':filter_profile_on_the_basis_of_city.values(),'Business':buisness.values()},'msg':"near by users & buisness on the basis of city"})
                
                #another way to use filter.🧨🧨🧨
                # all_l=Profile.objects.filter(**filters).exclude(user_id=request.POST['User']).exclude(user_id__in=friends).values('id','user_id','city','lat','long','profile_image','hostmatch','matchplayed','matchwon','rating',email_1=F('user_id__email'))  

                distanc=[]
                for i in all_l:
                      lat2=i['lat']  #get the lat of first user and then 2nd according to loop.
                      lon2=i['long']  #get the long of first user and then 2nd according to loop.
                      if lat2 or lon2:
                        from math import sin, cos, sqrt, atan2, radians
                        lat1 = radians(float(lat))
                        lon1 = radians(float(lon))
                        R = 6373.0
                        lat2=radians(float(lat2))
                        lon2=radians(float(lon2))
                        dlon = lon2 - lon1
                        dlat = lat2 - lat1
                        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
                        c = 2 * atan2(sqrt(a), sqrt(1 - a))
                        distanc.append(R * c)
                        
                        #long way to add email field in response 👌👌
                        p=Profile.objects.filter().exclude(user_id=request.POST['User']).values('user_id').exclude(user_id__in=friends)
                        u=User.objects.filter(id__in=p).values('email')
                        email=[]
                        for i in u:
                            e=i['email']
                            email.append(e)    
                        else:
                            pass
                      else:
                        distanc.append(2*6.28*6500)

                df = pd.DataFrame(list(all_l)) ## this will save 50% memory
                df = df.where(pd.notnull(df), None)
                df['distance']=distanc
                # df['email']=email
                df=df[df['distance']<50]
                df=df.sort_values('distance')
                # df=df.drop(['distance'], axis=1)
                df=df.to_dict('records')
                np=df
                
                all_l=Buisness.objects.all().values()
                distanc=[]
                for i in all_l:
                    lat2=i['lat']
                    lon2=i['long']
                    if lat2 or lon2:
                        from math import sin, cos, sqrt, atan2, radians
                        lat1 = radians(lat)
                        lon1 = radians(lon)
                        R = 6373.0
                        lat2=radians(float(lat2))
                        lon2=radians(float(lon2))
                        dlon = lon2 - lon1
                        dlat = lat2 - lat1
                        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
                        c = 2 * atan2(sqrt(a), sqrt(1 - a))
                        distanc.append(R * c)  

                        #add email field in repsonse
                        b=Buisness.objects.all().values('user_id')
                        u=User.objects.filter(id__in=b).values('email')
                        # print(u)
                        email=[]
                        for i in u:
                            e=i['email']
                            email.append(e)
                        else:
                            pass    
                    else:
                        distanc.append(2*6.28*6500)
                
                df = pd.DataFrame(list(all_l)) ## this will save 50% memory👌👌
                df = df.where(pd.notnull(df), None)
                
                df['distance']=distanc
                df['email']=email
                df=df[df['distance']<50]
                df=df.sort_values('distance')
                # df=df.drop(['distance'], axis=1)
                df=df.to_dict('records') 
                Business=df
                return Response({'data':{'NearbyPlayers':np,'Business':Business},'msg':'Home with sort','status':200})
                
           
            return Response({'data':{'NearbyPlayers':np,'Business':Business},'msg':'Home','status':200})


# def send_friend_request(self,request):
#     from_user=request.user
#     to_user=Profile.objects.get(id=request.POST('profile_id'))
#     friend_request,created=FriendRequest.objects.get_or_create(from_user=from_user,to_user=to_user)
#     if created:
#         return Response('friend request send')
#     else:
#         return Response('friend request was already sent') 


# def accept_friend_request(self,request):
from django.db.models import Q,F,Case, Value, When, FloatField
class GetAllFriendRequest(APIView):
    """
    Get All Friend_Request
    """
    receiver_id = openapi.Parameter('receiver_id',
                            in_=openapi.IN_QUERY,
                            description='enter receiver_id to find the list of friend requests send by other users.',
                            type=openapi.TYPE_INTEGER,
                            )  

    sender_id = openapi.Parameter('sender_id',
                            in_=openapi.IN_QUERY,
                            description='enter sender_id to find the list of friend requests that i send to others.',
                            type=openapi.TYPE_INTEGER,
                            )                          

    friends_accpted=openapi.Parameter('friends_accpted',
                            in_=openapi.IN_QUERY,
                            description='pass true if you want to get a list of friends who accepts my friend requests',
                            type=openapi.TYPE_BOOLEAN,
                            )
    @swagger_auto_schema(
            manual_parameters=[receiver_id,friends_accpted,sender_id]
    )                        
                    
    @csrf_exempt
    def get(self, request):
        try:
            data=request.GET
            if data.get("receiver_id"):
                receiver=data.get('receiver_id')
            else:
                receiver="" 

            if data.get("sender_id"):
                sender=data.get('sender_id')
            else:
                sender=""     

            if data.get("friends_accpted"):
                friends=data.get('friends_accpted')
            else:
                friends=''   
            print(friends)       
        
            friend_request=FriendRequest.objects.all()

            #list of those frnds whoose request is accepted by me.
            if receiver and friends:
                friend_request=friend_request.filter(receiver=receiver,status="Accepted").values('id','sender','receiver','status',profile_image=F('sender_id__profile_image'),first_name=F('sender_id__user_id__first_name'),email=F('sender_id__user_id__email'))    
                dictV=dict()
                dictV=friend_request
                return Response({
                    'data':dictV,
                    'msg':'All list of those friends whoose request is accepted by me',
                    'status':200
                 })

            #Other users sends me a frnd request.    
            if receiver:
                friend_request=friend_request.filter(receiver=receiver,status="Pending").values('id','sender','receiver','status',profile_image=F('sender_id__profile_image'),first_name=F('sender_id__user_id__first_name'),email=F('sender_id__user_id__email'))
                dictV=dict()
                dictV=friend_request
                return Response({
                    'data':dictV,
                    'msg':'All list of friend request that other users sends to me and status is Accepted',
                    'status':200
                 })

            # I sends a friend requests to other users.
            if sender:
                friend_request=friend_request.filter(sender=sender,status="Pending").values('id','sender','receiver','status',profile_image=F('sender_id__profile_image'),first_name=F('sender_id__user_id__first_name'),email=F('sender_id__user_id__email'))    
                dictV=dict()
                dictV=friend_request
                return Response({
                    'data':dictV,
                    'msg':'All list of friend request that i send to other users and status is Pending',
                    'status':200
                 })

            
            if friend_request:     
                serializer=GetFriendRequestSerializer(friend_request,many=True) 
                return Response({
                    'data':serializer.data,
                    'status':status.HTTP_200_OK,
                    'msg':'list of all friend requests'
                    })                 
            else:
                return Response({'msg':'search not found'})     
        except:
            return Response({"friend requests does not find"})


class CreateFriendRequest(APIView):
    """
    Create Friend_Request
    """
    # permission_classes=(IsAuthenticated,)
    # parser_classes = (FormParser, MultiPartParser)

    @swagger_auto_schema(
        operation_description="send friend request",
        operation_summary="send friend request",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "sender": openapi.Schema(type=openapi.TYPE_INTEGER),
                "receiver": openapi.Schema(type=openapi.TYPE_INTEGER),
                "status": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )
    @csrf_exempt
    def post(self, request):
        serializer = FriendRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ResponseOk(
                {
                    "data": serializer.data,
                    "code": status.HTTP_200_OK,
                    "message": "Friend Request sends Successfully",
                }
            )
            
        else:    
            
            return ResponseBadRequest(
                {
                    "data": serializer.errors,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Friend Request is not valid",
                }
            )

class GetFriendRequest(APIView):
    """
    Get Friend Request by pk
    """
    # permission_classes=(IsAuthenticated,)  
    
    @csrf_exempt
    def get_object(self, pk):
        try:
            return FriendRequest.objects.get(pk=pk)
        except FriendRequest.DoesNotExist:
            raise ResponseNotFound()

    def get(self, request, pk):
        try:
            friend_request = self.get_object(pk)
         
            serializer = FriendRequestSerializer(friend_request)
            return ResponseOk(
                {
                    "data": serializer.data,
                    "code": status.HTTP_200_OK,
                    "message": "get friend-request successfully",
                }
            )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "friend_request Does Not Exist",
                }
            )

class UpdateFriendRequest(APIView):
    """
    Update friend_request
    """
    # permission_classes=(IsAuthenticated,)
    # parser_classes = (FormParser, MultiPartParser)
    
    def get_object(self, pk):
        try:
            return FriendRequest.objects.get(pk=pk)
        except FriendRequest.DoesNotExist:
            raise ResponseNotFound()
            
    @swagger_auto_schema(
        operation_description="update friend request",
        operation_summary="update friend request",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "sender": openapi.Schema(type=openapi.TYPE_INTEGER),
                "receiver": openapi.Schema(type=openapi.TYPE_INTEGER),
                "status": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )     
          
    @csrf_exempt
    def put(self, request, pk):
        try:
           
            friend_request = self.get_object(pk)
            serializer = FriendRequestSerializer(friend_request,data=request.data)
            if serializer.is_valid():
                serializer.save()
                return ResponseOk(
                    {
                        "data": serializer.data,
                        "code": status.HTTP_200_OK,
                        "message": "Friend_Request accepted or declined successfully",
                    }
                )
            else:
                return ResponseBadRequest(
                    {
                        "data": serializer.errors,
                        "code": status.HTTP_400_BAD_REQUEST,
                        "message": "Friend_Request Not valid",
                    }
                )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Friend_Request Does Not Exist",
                }
            )

class DeleteFriendRequest(APIView):
    """
    Delete Friend_Request
    """
    # permission_classes=(IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser)

    @csrf_exempt
    def get_object(self, pk):
        try:
            return FriendRequest.objects.get(pk=pk)
        except FriendRequest.DoesNotExist:
            raise ResponseNotFound()

    def delete(self, request, pk):
        try:
            friend_request = self.get_object(pk)
            friend_request.delete()
            return ResponseOk(
                {
                    "data": None,
                    "code": status.HTTP_200_OK,
                    "message": "Friend_Request deleted Successfully",
                }
            )
        except:
            return ResponseBadRequest(
                {
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Friend_Request Does Not Exist",
                }
            )


#postman API's for friend request

class Invitations(APIView):
    def post(self,request):
        data=request.data
        friend_request=FriendRequest.objects.filter(receiver=request.data['receiver'],status="Pending").values('id','sender','receiver','status',profile_image=F('sender_id__profile_image'),first_name=F('sender_id__user_id__first_name'),email=F('sender_id__user_id__email'),host_match=F('sender_id__hostmatch'),match_played=F('sender_id__matchplayed'),match_wom=F('sender_id__matchplayed'),rating=F('sender_id__rating'),city=F('sender_id__city'),state=F('sender_id__state'),zip_code=F('sender_id__zip_code'))  
        dictV=dict()
        dictV=friend_request
        return Response({
            'data':dictV,
            'msg':'All list of those friends who sends me a friend request',
            'status':200
         })


class MyFriends_Accepted(APIView):
    def post(self,request):
        friend_request_accepted=FriendRequest.objects.filter(receiver=request.data['receiver'],status="Accepted").values('id','sender','receiver','status',profile_image=F('sender_id__profile_image'),first_name=F('sender_id__user_id__first_name'),email=F('sender_id__user_id__email'))   
        return Response({
            'friend_request_accepted':friend_request_accepted,
            'msg':'All list of those friends who sends me a friend request and i accepted the request',
            'status':200
         })


class Friend_Request_Send(APIView):
    def post(self,request):
        friend_request_send=FriendRequest.objects.filter(sender=request.data['sender'],status="Pending").values('id','sender','receiver','status',profile_image=F('sender_id__profile_image'),first_name=F('sender_id__user_id__first_name'),email=F('sender_id__user_id__email'))      
        return Response({
            'friend_request_send':friend_request_send,
            'msg':'All list of friend request that i send to other users and status is Pending',
            'status':200
         })         


class Accept_Request(APIView):
    def post(self,request):
        update_status=FriendRequest.objects.filter(id=request.data['id']).update(status='Accepted') 
        p=Profile.objects.filter(id=request.POST['id']).update(status='Accepted')
        data=FriendRequest.objects.filter(id=request.data['id'])
        
        return Response({
            'data':data.values(),
            'msg':'Accept the friend request and status is Accepted',
            'status':200
         })      

class Decline_Friend_Request(APIView):
    def post(self,request):
        update_status=FriendRequest.objects.filter(id=request.data['id']).delete()
       
        return Response({
            'update_status':update_status,
            'msg':'Declined the friend request',
            'status':200
         })            