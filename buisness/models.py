from django.db import models
# from user.models import Profile
from user.models import User
from django.db import models
# Create your models here.

# class Service(models.Model):
#     service_name=models.CharField(max_length=100,null=True,blank=True)

#     def __str__(self):
#         return self.service_name

# class Short_Images(models.Model):
#     image=models.ImageField(upload_to='buisness_short_images',null=True,blank=True)

from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="IN")

class Buisness(models.Model):
    
    buisness_owner=models.OneToOneField(User,on_delete=models.CASCADE,related_name="buisness_owner")
    # service=models.ManyToManyField(Service,blank=True,null=True)
    buisness_name=models.CharField(max_length=200,null=True,blank=True)
    # short_images=models.ImageField(upload_to='short_buisness_images',blank=True,null=True)
    tennis_court=models.IntegerField(blank=True,null=True)
    address=models.CharField(max_length=200,null=True,blank=True)
    description=models.CharField(max_length=500,null=True,blank=True)
    working_days=models.CharField(max_length=200,null=True,blank=True)
    working_hours=models.CharField(max_length=200,null=True,blank=True)

    non_working_days=models.CharField(max_length=200,null=True,blank=True)
    non_working_hours=models.CharField(max_length=200,null=True,blank=True)

    lat=models.CharField(max_length=50,null=True,blank=True)
    long=models.CharField(max_length=50,null=True,blank=True)
    pin_code=models.CharField(max_length=50,null=True,blank=True)


    def __str__(self):
        return str(self.buisness_name)


    # def save(self,*args,**kwargs):
    #     geolocator=Nominatim(user_agent="geoapiExercises")
    #     location=geolocator.geocode(int(self.pin_code))
    #     self.lat=location.latitude
    #     self.long=location.longitude
    #     super(Buisness,self).save(*args,**kwargs)



class BuisnessImages(models.Model):
    buisness=models.ForeignKey(Buisness,on_delete=models.CASCADE,related_name="buisness_images")
    buisness_images=models.ImageField(upload_to='buisnessimages')
