from django.db import models
from user.models import Profile,User
# Create your models here.


class Report(models.Model):
    profile=models.ForeignKey(Profile,on_delete=models.CASCADE,null=True,blank=True)
    image=models.ImageField(upload_to='report_image',blank=True,null=True)
    feedback=models.TextField(max_length=300,null=True,blank=True)



class Buisness(models.Model):
    name=models.CharField(max_length=100,null=True,blank=True)
    image=models.ImageField(upload_to='buisness_image',blank=True,null=True)
    address=models.CharField(max_length=100,blank=True,null=True)

    def __str__(self):
       return self.name

class Suspend_User(models.Model):
    user=models.ForeignKey(Profile,on_delete=models.CASCADE)
    is_suspended=models.BooleanField(default=False)


    def __str__(self):
        return self.user.user_id.first_name

 

