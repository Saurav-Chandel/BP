
from rest_framework import serializers
from .models import *
from user.serializers import *



class ServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model=Service
        fields="__all__"  

class BuisnessSerializer(serializers.ModelSerializer):
    profile=ProfileSerializer(read_only=True)
    class Meta:
        model=Buisness
        fields="__all__"  