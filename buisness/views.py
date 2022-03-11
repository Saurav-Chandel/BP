from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from .serializers import *
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from app.response import ResponseBadRequest, ResponseNotFound, ResponseOk
from django.db.models import Q
from rest_framework import filters, permissions, serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import FormParser, MultiPartParser
import os

# Create your views here.
from rest_framework import viewsets

class BuisnessViewSet(viewsets.ModelViewSet):
    serializer_class = BuisnessSerializer
    parser_classes = (MultiPartParser, FormParser,)
    queryset=Buisness.objects.all()

    def list(self, request):
        b=Buisness.objects.all()
        serializer=BuisnessSerializer(b,many=True)
        if request.data.get('search'):
            s=b.filter(Q(buisness_name__icontains=request.data.get('search')))
            if s:
               serializer=BuisnessSerializer(s,many=True)
               return Response({"data":serializer.data})
        return Response({"data":serializer.data})


class BuisnessImagesviewSet(viewsets.ModelViewSet):
    serializer_class = BuisnessImagesSerializer
    parser_classes = (MultiPartParser, FormParser,)
    queryset=BuisnessImages.objects.all()

    




# class GetAllBuisness(APIView):
#     """
#     Get All Buisness
#     """
#     permission_classes=(IsAuthenticated,)

#     city = openapi.Parameter('city',
#                             in_=openapi.IN_QUERY,
#                             description='Search by city',
#                             type=openapi.TYPE_STRING,
#                             )
#     state = openapi.Parameter('state',
#                             in_=openapi.IN_QUERY,
#                             description='Search by state',
#                             type=openapi.TYPE_STRING,
#                             )   
#     @swagger_auto_schema(
#             manual_parameters=[city,state]
#     )                        

#     @csrf_exempt
#     def get(self, request):
#         try:
#             data=request.GET
#             if data.get('city'):     
#                 city=data.get('city')
#             else:
#                 city=""
            
#             if data.get('state'):
#                 state=data.get('state')
#             else:
#                 state=""    
    
#             buisness=Buisness.objects.all()
#             if city:
#                 buisness=buisness.filter(Q(profile__city__icontains=city))  
#             if state:
#                 buisness=buisness.filter(Q(profile__state__icontains=state))      
#             if buisness:
#                 serializer=BuisnessSerializer(buisness,many=True)  
#                 return Response({
#                     'data':serializer.data,
#                     'status':status.HTTP_200_OK,
#                     'msg':'All Buisness by given search'
#                 })                 
#             else:
#                 return Response({'msg':'search not found'})
#         except:
#             return Response({'msg':'search query does not found'})


# # def modify_input_for_multiple_files(buisness_owner, Buisness_image):
# #     dict = {}
# #     dict['buisness_owner'] = buisness_owner
# #     dict['buisness_images'] = Buisness_image
# #     return dict

# # import json
# class CreateBuisness(APIView):
#     """
#     Create Buisness
#     """
    
#     # permission_classes=(IsAuthenticated,)
#     parser_classes = (FormParser, MultiPartParser)
#     serializer_class=BuisnessSerializer

#     @swagger_auto_schema(
#         operation_description="create Buisness",
#         request_body=BuisnessSerializer,
#     )
    
#     @csrf_exempt
#     def post(self, request):
#         print(request.data)
#         serializer=BuisnessSerializer(data=request.data)
#         print("SSSSSSSSSSSSSS")
#         if serializer.is_valid():
#            print("VVVVVVVVVVVVVVVVVVVV")
#            serializer.save()
#            return Response({"data":serializer.data,
#                             "status":status.HTTP_200_OK,
#                             "message":"Buisness created successfully"})
#         return Response({"data":serializer.errors,
#                         "status":status.HTTP_400_BAD_REQUEST,
#                         "message":"Buisness does not found"})                    
   
            

# #   print(request.FILES.getlist('buisness_images'))
# #         serializer_class = BuisnessSerializer(data=request.data)
# #         if 'buisness_images' not in request.FILES or not serializer_class.is_valid():
# #             return Response(status=status.HTTP_400_BAD_REQUEST)
# #         else:
# #             files=request.FILES.getlist('buisness_images')
# #             for f in files:
# #                handle_uploaded_file(f)
# #             return Response(status=status.HTTP_201_CREATED)

# # def handle_uploaded_file(f):
# #     with open(f.name, 'wb+') as destination:
# #         for chunk in f.chunks():
# #             destination.write(chunk)


from django.core.files.storage import FileSystemStorage
from datetime import datetime
from rest_framework import generics

class CreateBuisnessGeneric(generics.GenericAPIView):
    # permission_classes=(IsAuthenticated,)
    serializer_class=BuisnessSerializer
    def post(self,request,*args,**kwargs):
        
        serializer=self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        RA=serializer.save()
        files=[]
        if len(request.FILES.getlist('buisness_images'))>0:
            files=request.FILES.getlist('buisness_images')
            print(files)
            Pstring=[]
            for i in range(len(files)):
                fs = FileSystemStorage()
                ppn=str(datetime.now())+'.jpg'
                print(ppn)
                filename = fs.save(ppn, files[i])
                uploaded_file_url = fs.url(filename)
                Pstring.append(uploaded_file_url)
            b=Buisness.objects.filter(buisness_owner=request.POST['buisness_owner'])   
            print(b) 
            Buisness.objects.filter(buisness_owner=request.POST['buisness_owner']).update(buisness_image=Pstring)
        
        profile=Buisness.objects.filter(buisness_owner=request.POST['buisness_owner']).values()[0]  
        profile['buisness_images']=filter(None,str(profile['buisness_images']).replace('[','').replace(']','').replace('\'','').replace(" ","").split(','))      
        return Response({
        'data':{'Profile':"profile"},
        'msg':'Business saved Successfully',
        'status':200
        })


# class GetBuisness(APIView):
#     """
#     Get Buisness by pk
#     """
#     permission_classes=(IsAuthenticated,)
    
#     csrf_exempt
#     def get_object(self, pk):
#         try:
#             return Buisness.objects.get(pk=pk)
#         except Buisness.DoesNotExist:
#             raise ResponseNotFound()

#     def get(self, request, pk):
#         try:
#             buisness = self.get_object(pk)
#             serializer = BuisnessSerializer(buisness)
#             return ResponseOk(
#                 {
#                     "data": serializer.data,
#                     "code": status.HTTP_200_OK,
#                     "message": "get Buisness successfully",
#                 }
#             )
#         except:
#             return ResponseBadRequest(
#                 {
#                     "data": None,
#                     "code": status.HTTP_400_BAD_REQUEST,
#                     "message": "Buisness Does Not Exist",
#                 }
#             )


# class UpdateBuisness(APIView):
#     """
#     Update Buisness
#     """
#     permission_classes=(IsAuthenticated,)
#     parser_classes = (FormParser, MultiPartParser)


#     def get_object(self, pk):
#         try:
#             return Buisness.objects.get(pk=pk)
#         except Buisness.DoesNotExist:
#             raise ResponseNotFound()

#     @swagger_auto_schema(
#         operation_description="update Buisness",
#         request_body=BuisnessSerializer,
#     )
#     @csrf_exempt
#     def put(self, request, pk):
#         try:
#             buisness = self.get_object(pk)
#             serializer = BuisnessSerializer(buisness, data=request.data)
#             if serializer.is_valid():
#                 serializer.save()
#                 return ResponseOk(
#                     {
#                         "data": serializer.data,
#                         "code": status.HTTP_200_OK,
#                         "message": "Buisness updated successfully",
#                     }
#                 )
#             else:
#                 return ResponseBadRequest(
#                     {
#                         "data": serializer.errors,
#                         "code": status.HTTP_400_BAD_REQUEST,
#                         "message": "Buisness Not valid",
#                     }
#                 )
#         except:
#             return ResponseBadRequest(
#                 {
#                     "data": None,
#                     "code": status.HTTP_400_BAD_REQUEST,
#                     "message": "Buisness Does Not Exist",
#                 }
#             )


# class DeleteBuisness(APIView):
#     """
#     Delete Buisness
#     """
#     permission_classes=(IsAuthenticated,)

#     @csrf_exempt
#     def get_object(self, pk):
#         try:
#             return Buisness.objects.get(pk=pk)
#         except Buisness.DoesNotExist:
#             raise ResponseNotFound()

#     def delete(self, request, pk):
#         try:
#             buisness = self.get_object(pk)
#             buisness.delete()
#             return ResponseOk(
#                 {
#                     "data": None,
#                     "code": status.HTTP_200_OK,
#                     "message": "Buisness deleted Successfully",
#                 }
#             )
#         except:
#             return ResponseBadRequest(
#                 {
#                     "data": None,
#                     "code": status.HTTP_400_BAD_REQUEST,
#                     "message": "Buisness Does Not Exist",
#                 }
#             )


# class GetAllService(APIView):
#     """
#     Get All Service
#     """
#     permission_classes=(IsAuthenticated,)

#     city = openapi.Parameter('city',
#                             in_=openapi.IN_QUERY,
#                             description='Search by city',
#                             type=openapi.TYPE_STRING,
#                             )
#     state = openapi.Parameter('state',
#                             in_=openapi.IN_QUERY,
#                             description='Search by state',
#                             type=openapi.TYPE_STRING,
#                             )   
#     @swagger_auto_schema(
#             manual_parameters=[city,state]
#     )                        

#     @csrf_exempt
#     def get(self, request):
#         try:
#             data=request.GET
#             if data.get('city'):     
#                 city=data.get('city')
#             else:
#                 city=""
            
#             if data.get('state'):
#                 state=data.get('state')
#             else:
#                 state=""    
    
#             buisness=Buisness.objects.all()
#             if city:
#                 buisness=buisness.filter(Q(profile__city__icontains=city))  
#             if state:
#                 buisness=buisness.filter(Q(profile__state__icontains=state))      
#             if buisness:
#                 serializer=BuisnessSerializer(buisness,many=True)  
#                 return Response({
#                     'data':serializer.data,
#                     'status':status.HTTP_200_OK,
#                     'msg':'All Buisness by given search'
#                 })                 
#             else:
#                 return Response({'msg':'search not found'})
#         except:
#             return Response({'msg':'search query does not found'})



# class CreateService(APIView):
#     """
#     Create Service
#     """
    
#     permission_classes=(IsAuthenticated,)
#     parser_classes = (FormParser, MultiPartParser)


#     @swagger_auto_schema(
#         operation_description="create Service",
#         request_body=ServiceSerializer,
#     )
#     @csrf_exempt
#     def post(self, request):
#         serializer = ServiceSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return ResponseOk(
#                 {
#                     "data": serializer.data,
#                     "code": status.HTTP_200_OK,
#                     "message": "Service created succesfully",
#                 }
#             )
            
#         else:    
            
#             return ResponseBadRequest(
#                 {
#                     "data": serializer.errors,
#                     "code": status.HTTP_400_BAD_REQUEST,
#                     "message": "Service is not valid",
#                 }
#             )



# class GetService(APIView):
#     """
#     Get Service by pk
#     """
#     permission_classes=(IsAuthenticated,)
    
#     csrf_exempt
#     def get_object(self, pk):
#         try:
#             return Service.objects.get(pk=pk)
#         except Service.DoesNotExist:
#             raise ResponseNotFound()

#     def get(self, request, pk):
#         try:
#             service = self.get_object(pk)
#             serializer = ServiceSerializer(service)
#             return ResponseOk(
#                 {
#                     "data": serializer.data,
#                     "code": status.HTTP_200_OK,
#                     "message": "get Service successfully",
#                 }
#             )
#         except:
#             return ResponseBadRequest(
#                 {
#                     "data": None,
#                     "code": status.HTTP_400_BAD_REQUEST,
#                     "message": "Service Does Not Exist",
#                 }
#             )


# class UpdateService(APIView):
#     """
#     Update Service
#     """
#     permission_classes=(IsAuthenticated,)
#     parser_classes = (FormParser, MultiPartParser)


#     def get_object(self, pk):
#         try:
#             return Service.objects.get(pk=pk)
#         except Service.DoesNotExist:
#             raise ResponseNotFound()

#     @swagger_auto_schema(
#         operation_description="update Service",
#         request_body=ServiceSerializer,
#     )
#     @csrf_exempt
#     def put(self, request, pk):
#         try:
#             service = self.get_object(pk)
#             serializer = ServiceSerializer(service, data=request.data)
#             if serializer.is_valid():
#                 serializer.save()
#                 return ResponseOk(
#                     {
#                         "data": serializer.data,
#                         "code": status.HTTP_200_OK,
#                         "message": "Service updated successfully",
#                     }
#                 )
#             else:
#                 return ResponseBadRequest(
#                     {
#                         "data": serializer.errors,
#                         "code": status.HTTP_400_BAD_REQUEST,
#                         "message": "Service Not valid",
#                     }
#                 )
#         except:
#             return ResponseBadRequest(
#                 {
#                     "data": None,
#                     "code": status.HTTP_400_BAD_REQUEST,
#                     "message": "Service Does Not Exist",
#                 }
#             )


# class DeleteService(APIView):
#     """
#     Delete Service
#     """
#     permission_classes=(IsAuthenticated,)

#     @csrf_exempt
#     def get_object(self, pk):
#         try:
#             return Service.objects.get(pk=pk)
#         except Service.DoesNotExist:
#             raise ResponseNotFound()

#     def delete(self, request, pk):
#         try:
#             service = self.get_object(pk)
#             service.delete()
#             return ResponseOk(
#                 {
#                     "data": None,
#                     "code": status.HTTP_200_OK,
#                     "message": "Service deleted Successfully",
#                 }
#             )
#         except:
#             return ResponseBadRequest(
#                 {
#                     "data": None,
#                     "code": status.HTTP_400_BAD_REQUEST,
#                     "message": "Service Does Not Exist",
#                 }
#             )