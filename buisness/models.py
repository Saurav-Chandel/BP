from django.db import models
from user.models import Profile
# Create your models here.

class Service(models.Model):
    service_name=models.CharField(max_length=100,null=True,blank=True)

    def __str__(self):
        return self.service_name

class Buisness(models.Model):
    profile=models.ForeignKey(Profile,on_delete=models.CASCADE)
    service=models.ForeignKey(Service,on_delete=models.CASCADE)
    buisness_name=models.CharField(max_length=200,null=True,blank=True)
    buisness_image=models.ImageField(upload_to='buisness_image',null=True,blank=True)
    address=models.CharField(max_length=200,null=True,blank=True)
    description=models.CharField(max_length=500,null=True,blank=True)
    buisness_hours=models.CharField(max_length=200,null=True,blank=True)

    def __str__(self):
        return self.buisness_name