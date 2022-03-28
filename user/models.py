import datetime
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.timezone import now
import django
# from buisness.models import Buisness
# from app import choices

# Create your models here.

hostmatch_selectmode_catchoice=(
    ('public','public'),
    ('private','private')
)
hostmatch_status_catchoice=(
    ('Initiated','Initiated'),
    ('Completed','Completed'),
    ('Cancel','cancel')
)
hostinvitation_status_catchoice=(
    ('Sent','Sent'),
    ('Decline','Decline'),
    ('Attend','Attend')
)
TOKEN_TYPE_CHOICES = (
    ("verification", "Email Verification"),
    ("pwd_reset", "Password Reset"),
)
role = (
    ("user", "user"),
    ("buisness", "buisness"),
)


STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected')
)

class AppUserManager(UserManager):
    def get_by_natural_key(self, username):
        return self.get(email__iexact=username)

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
      
        return self._create_user(email, password, **extra_fields)

    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create a Super Admin. Not to be used by any API. Only used for django-admin command.
        :param email:
        :param password:
        :param extra_fields:
        :return:
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('username', email)

        try:
            user_type=UserType.objects.get(role="superuser")
        except:
            user_type=UserType.objects.create(role="superuser")
        extra_fields.setdefault('user_type', user_type)
        # try:
        #     buisness=Buisness.objects.get(buisness_name="Buisness")
        # except:
        #     buisness=Buisness.objects.create(buisness_name="Buisness")    

        user = self._create_user(email, password, **extra_fields)
        return user

class UserType(models.Model):
    role=models.CharField(max_length=100,blank=True,null=True)
    # slug=AutoslugField(populate_from=["role"])
   
    def __str__(self):
        return self.role


class User(AbstractUser):
    first_name = models.CharField(
        max_length=200, default=None, null=True, blank=True
    )
    last_name = models.CharField(
        max_length=200, default=None, null=True, blank=True
    )
    # user_type=models.CharField(max_length=100,choices=role,blank=True,null=True)
    user_type=models.ForeignKey(UserType,on_delete=models.CASCADE,related_name='user_type',null=True,blank=True)
    # user_buisness=models.ForeignKey(Buisness,on_delete=models.CASCADE,blank=True,null=True)
    email=models.EmailField(unique=True,null=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    manager = AppUserManager()

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['first_name']

    def __str__(self):
        return self.username        

class Token(models.Model):
    token = models.CharField(max_length=300)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    token_type = models.CharField(
        max_length=20, choices=TOKEN_TYPE_CHOICES
    )
    created_on = models.DateTimeField(default=now, null=True, blank=True)
    expired_on = models.DateTimeField(default=now, null=True, blank=True)

from django.core.validators import MaxValueValidator, MinValueValidator
class Profile(models.Model):
    user_id=models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile",blank=True,null=True)
    profile_image = models.ImageField(upload_to ='media',null=True,blank=True)
    city=models.CharField(max_length=100,blank=True,null=True)
    state=models.CharField(max_length=100,blank=True,null=True)
    country=models.CharField(max_length=100,blank=True,null=True)
    rating=models.CharField(max_length=100,blank=True,null=True)
    zip_code=models.CharField(max_length=100,blank=True,null=True)
    cpf_number=models.CharField(max_length=100,unique=True,blank=True,null=True)
    contact_number=models.CharField(max_length=15,null=True,blank=True)
    location=models.CharField(max_length=250,null=True,blank=True)
    hostmatch=models.CharField(max_length=100,null=True,blank=True,default=0)
    matchplayed=models.IntegerField(blank=True,null=True,default=0)
    matchwon=models.IntegerField(blank=True,null=True,default=0)
    date_added=models.DateTimeField(default=django.utils.timezone.now)
    lat=models.CharField(max_length=50,null=True,blank=True)
    long=models.CharField(max_length=50,null=True,blank=True)
    
    # status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="Pending")
    
    # def save():
        
    def __str__(self):
        return self.user_id.first_name
    
from geopy.geocoders import Nominatim
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models import PointField
from django.contrib.gis.db import models as giomodels
from location_field.models.plain import PlainLocationField

class HostMatch(models.Model):
    profile_id=models.ForeignKey(Profile,on_delete=models.CASCADE,related_name="hostmatch_profile")
    title=models.CharField(max_length=100,blank=True,null=True)
    date=models.DateField(blank=True,null=True)
    time=models.TimeField(blank=True,null=True)
    # point = giomodels.PointField(srid=4326,null=True,blank=True)
    location = PlainLocationField(based_fields=['city'], zoom=7,blank=True,null=True)
    # location=models.CharField(max_length=200,null=True,blank=True)
    select_mode=models.CharField(max_length=100,blank=True,null=True,choices=hostmatch_selectmode_catchoice)
    status=models.CharField(max_length=200,blank=True,null=True,choices=hostmatch_status_catchoice)
    pincode=models.CharField(max_length=100,null=True,blank=True)
    lat=models.CharField(max_length=100,null=True,blank=True)
    long=models.CharField(max_length=100,null=True,blank=True)
    date_added=models.DateTimeField(default=django.utils.timezone.now)

    def save(self,*args,**kwargs):
        geolocator = Nominatim(user_agent="IN")
        location=geolocator.geocode(self.pincode)
        self.lat=location.latitude
        self.long=location.longitude
        super(HostMatch,self).save(*args,**kwargs)

    def __str__(self):
        return self.profile_id.user_id.first_name

class HostInvitation(models.Model):
    hostmatch_id=models.ForeignKey(HostMatch,on_delete=models.CASCADE,related_name='hostmatch')
    user_invited=models.ManyToManyField(Profile,related_name='user_invited_profile')
    status=models.CharField(max_length=200,choices=hostinvitation_status_catchoice,null=True,blank=True)
    date_added=models.DateTimeField(default=django.utils.timezone.now)

    def __str__(self):
        return self.user_invited.user_id.first_name


class FriendRequest(models.Model):
    sender = models.ForeignKey(Profile,related_name='sender',on_delete=models.CASCADE)  # who sends friend request
    receiver = models.ForeignKey(Profile,related_name='receiver',on_delete=models.CASCADE)      #Receives the request
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="Pending")
    date_added=models.DateTimeField(default=django.utils.timezone.now)

    class Meta:
        unique_together = (('sender', 'receiver',))
        ordering = ["-date_added"]

    def __str__(self):
        return f"{self.sender} follows {self.receiver}" 

class Team1Players(models.Model):
    host_match=models.ForeignKey(HostMatch,on_delete=models.CASCADE,related_name='host_player_1')
    player=models.ForeignKey(Profile,on_delete=models.CASCADE)
    date_added=models.DateTimeField(default=django.utils.timezone.now)

class Team2Players(models.Model):
    host_match=models.ForeignKey(HostMatch,on_delete=models.CASCADE,related_name='host_player_2')
    player=models.ForeignKey(Profile,on_delete=models.CASCADE)
    date_added=models.DateTimeField(default=django.utils.timezone.now)

from django.db.models.functions import Greatest
class TeamScore(models.Model):
    host_match=models.ForeignKey(HostMatch,on_delete=models.CASCADE,related_name='host_score')
    # host_invited=models.ForeignKey(HostInvitation,on_delete=models.CASCADE,null=True,blank=True)
    round=models.IntegerField()
    team1_player_score=models.IntegerField()
    team2_player_score=models.IntegerField()
    date_added=models.DateTimeField(default=django.utils.timezone.now)

#     def save(self):
#         self.result = TeamScore.objects.annotate(res=Greatest('team1_player_score', 'team2_player_score'))
#         return super(TeamScore, self).save()

    def __str__(self):
        return self.host_match.user_id.user_id.first_name    

class PlayersRating(models.Model):
    # host_match=models.ForeignKey(HostMatch,on_delete=models.CASCADE)
    player=models.ForeignKey(Profile,on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5,validators=[MaxValueValidator(5),MinValueValidator(0)])
    date_added=models.DateTimeField(default=django.utils.timezone.now)

class Notification(models.Model):
    User_id=models.ForeignKey(User,on_delete=models.CASCADE,related_name='user10')
    Status=models.BooleanField(default=True)
  
class ContactUs(models.Model):
    user_id=models.OneToOneField(User,on_delete=models.CASCADE,related_name="contact_us")
    first_name=models.CharField(max_length=100,null=True,blank=True)
    subject=models.CharField(max_length=100,null=True,blank=True)
    message=models.CharField(max_length=100,null=True,blank=True)
    email_address=models.EmailField(max_length=254)

    def __str__(self):
        return self.first_name

class AboutUs(models.Model):
    user_id=models.OneToOneField(User,on_delete=models.CASCADE,related_name="aboutus")
    about=models.CharField(max_length=100,blank=True,null=True)
    date_added=models.DateTimeField(default=django.utils.timezone.now)  

    def __str__(self):
        return self.about     

    class Meta:
        ordering = ('-id',)

class PrivacyPolicy(models.Model):
    policy=models.CharField(max_length=100,blank=True,null=True)
    date_added=models.DateTimeField(default=django.utils.timezone.now)  

    def __str__(self):
        return self.policy 

class TermsCondition(models.Model):
    user_id=models.OneToOneField(User,on_delete=models.CASCADE,null=True)
    terms=models.CharField(max_length=100,blank=True,null=True)
    date_added=models.DateTimeField(default=django.utils.timezone.now)  

    def __str__(self):
        return self.terms 


        
