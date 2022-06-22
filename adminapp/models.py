from django.db import models
from user.models import Profile,User
# Create your models here.


class Report(models.Model):
    profile=models.ForeignKey(Profile,on_delete=models.CASCADE,null=True,blank=True)
    image=models.ImageField(upload_to='report_image',blank=True,null=True)
    feedback=models.TextField(max_length=300,null=True,blank=True)
