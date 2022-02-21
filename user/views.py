
from ssl import PROTOCOL_TLSv1_1
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
from django.db.models import Q



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
            },
        ),
    )
    @csrf_exempt
    def post(self, request):
        data = request.data
        data["username"] = data['email']

        if User.objects.filter(email=data["email"]).exists():
            return ResponseBadRequest(
                {
                    "data": {"email": ["Email Already Exist"]},
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
        except:    
            return ResponseBadRequest({
                "msg":'user not found'
            })    

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

class GetAllProfile(APIView):
    """
    Get profile
    """
    permission_classes = [permissions.IsAuthenticated]
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


    @swagger_auto_schema(
            manual_parameters=[city,state]
    )

    @csrf_exempt
    def get(self, request):
        try:
            data=request.GET
            if data.get('city'):     
                city=data.get('city')
            else:
                city=""
            
            if data.get('state'):
                state=data.get('state')
            else:
                state=""    
    
            profile=Profile.objects.all()
        
            if city:
                profile=profile.filter(Q(city__icontains=city))  
            if state:
                profile=profile.filter(Q(state__icontains=state))  

            if profile:
                serializer=GetProfileSerializer(profile,many=True) 
                print(serializer)
                return Response({
                    'data':serializer.data,
                    'status':status.HTTP_200_OK,
                    'msg':'All profiles by given search'
                })                 
            else:
                return Response({'msg':'search not found'})
        except:
            return Response({'msg':'search query does not found'})        

class CreateProfile(APIView):
    """
    Create Profile
    """

    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [authentication.JWTAuthentication]
    parser_classes = (FormParser, MultiPartParser)

    @swagger_auto_schema(
        operation_description="create Profile",
        request_body=ProfileSerializer,
    )
    @csrf_exempt
    def post(self, request):
        serializer = ProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return ResponseOk(
                {
                    "data": serializer.data,
                    "code": status.HTTP_200_OK,
                    "message": "Profile created succesfully",
                }
            )
        else:    
            return ResponseBadRequest(
                {
                    "data": serializer.errors,
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "Profile is not valid",
                }
            )

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
    
    permission_classes=(IsAuthenticated,)
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
                            description='enter the user_invited_id to find the invitations send by host match',
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

                print(host_match)
                team1_score=list(HostMatch.objects.filter(user_id=host_match).annotate(Avg('host_score__team1_player_score')).values_list('host_score__team1_player_score__avg'))
                print(team1_score)

                print("_______")

                team2_score=list(HostMatch.objects.filter(user_id=host_match).annotate(Avg('host_score__team2_player_score')).values_list('host_score__team2_player_score__avg'))
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
                    # print(host_match[1])

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
                        'msg':'MyAttendingCompletedMatches List',
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
                        'msg':'MyAttendingOngoingMatches List',
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
    
    permission_classes=(IsAuthenticated,)
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
    permission_classes = [permissions.IsAuthenticated]
    
    serializer_class=ContactUsSerializer
    def post(self,request,*args,**kwargs):
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        RA=serializer.save()
        return Response({'msg':'ContactUs information saved Successfully','status':200})   


class AboutUsAPI(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self,request,*args,**kwargs):
        return Response({
            'data':{'text':AboutUs.objects.all().values()},
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
