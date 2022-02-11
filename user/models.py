import datetime

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.timezone import now
import django
# from app import choices

# Create your models here.
TOKEN_TYPE_CHOICES = (
    ("verification", "Email Verification"),
    ("pwd_reset", "Password Reset"),
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

        user = self._create_user(email, password, **extra_fields)
        return user


class User(AbstractUser):
    first_name = models.CharField(
        max_length=200, default=None, null=True, blank=True
    )
    last_name = models.CharField(
        max_length=200, default=None, null=True, blank=True
    )
    email=models.EmailField(unique=True,null=False)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    manager = AppUserManager()

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


class Profile(models.Model):
    user_id=models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile",null=True,blank=True)
    profile_image = models.ImageField(upload_to ='media',null=True,blank=True)
    city=models.CharField(max_length=100,blank=True,null=True)
    state=models.CharField(max_length=100,blank=True,null=True)
    zip_code=models.CharField(max_length=100,blank=True,null=True)
    cpf_number=models.CharField(max_length=100,unique=True)
    contact_number=models.CharField(max_length=15,null=True,blank=True)
    location=models.CharField(max_length=250,null=True,blank=True)
    matchhost=models.IntegerField(blank=True,null=True,default=0)
    matchplayed=models.IntegerField(blank=True,null=True,default=0)
    matchwon=models.IntegerField(blank=True,null=True,default=0)
    date_added=models.DateTimeField(default=django.utils.timezone.now)


    def __str__(self):
        return self.user_id.first_name

class HostMatch(models.Model):
    user_id=models.ForeignKey(Profile,on_delete=models.CASCADE)
    title=models.CharField(max_length=100,blank=True,null=True)
    date=models.DateField()
    time=models.TimeField()
    location=models.CharField(max_length=200,null=True,blank=True)
    public='public'
    private='private'
    CategoryChoices=[(public,'public'),
                     (private,'private')]

    Initiated='Initiated'
    Completed='Completed'
    InCompleted='InCompleted'    
    StatusChoices=[(Initiated,'Initiated'),
                   (Completed,'Completed'),
                   (InCompleted,'InCompleted')]
            
    select_mode=models.CharField(max_length=100,blank=True,null=True,choices=CategoryChoices)
    status=models.CharField(max_length=200,blank=True,null=True,choices=StatusChoices)
    date_added=models.DateTimeField(default=django.utils.timezone.now)

    def __str__(self):
        return self.user_id.user_id.first_name

class HostInvitation(models.Model):
    hostmatch_id=models.ForeignKey(HostMatch,on_delete=models.CASCADE,related_name='hostmatch')
    user_invited=models.ForeignKey(Profile,on_delete=models.CASCADE,null=True,blank=True,related_name='profile')

    Sent='Sent'
    Decline='Decline'
    Attend='Attend'
    CategoryChoices=[(Sent,'Sent'),
                     (Decline,'Decline'),
                     (Attend,'Attend')]
    status=models.CharField(max_length=200,choices=CategoryChoices,null=True,blank=True)
    date_added=models.DateTimeField(default=django.utils.timezone.now)

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
    round=models.IntegerField()
    team1_player_score=models.IntegerField()
    team2_player_score=models.IntegerField()
    date_added=models.DateTimeField(default=django.utils.timezone.now)
    # result=models.CharField(max_length=100,null=True,blank=True)

    def save(self):
        self.result = TeamScore.objects.annotate(res=Greatest('team1_player_score', 'team2_player_score')
)
        return super(TeamScore, self).save()

    def __str__(self):
        return self.host_match.user_id.user_id.first_name    

class PlayersRating(models.Model):
    host_match=models.ForeignKey(HostMatch,on_delete=models.CASCADE)
    player=models.ForeignKey(Profile,on_delete=models.CASCADE)
    rating=models.IntegerField(blank=True,null=True)
    date_added=models.DateTimeField(default=django.utils.timezone.now)







class ContactUs(models.Model):
    user_id=models.OneToOneField(User,on_delete=models.CASCADE,related_name="contact_us")
    first_name=models.CharField(max_length=100,null=True,blank=True)
    subject=models.CharField(max_length=100,null=True,blank=True)
    message=models.CharField(max_length=100,null=True,blank=True)
    email_address=models.EmailField(max_length=254)

    def __str__(self):
        return self.first_name


class AboutUs(models.Model):
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
    terms=models.CharField(max_length=100,blank=True,null=True)
    date_added=models.DateTimeField(default=django.utils.timezone.now)  

    def __str__(self):
        return self.terms 


