from django.contrib import admin
from .models import *
# Register your models here.

class UserAdmin(admin.ModelAdmin):
    list_display = ('id','first_name', 'last_name', 'email','is_active',
    'is_superuser','is_staff',)

class HostInvitationAdmin(admin.ModelAdmin):
    list_display = ('id','status',)

class Team1PlayerAdmin(admin.ModelAdmin):
    list_display = ('id','host_match','player') 

class Team2PlayerAdmin(admin.ModelAdmin):
    list_display = ('id','host_match','player')   

class TeamScoreAdmin(admin.ModelAdmin):
    list_display = ('id','host_match','round','team1_player_score','team2_player_score')            

class HostInvitationInline(admin.TabularInline):
    model = HostInvitation
    extra=1
   
class Team1PlayerInline(admin.TabularInline):
    model = Team1Players
    extra=1

class Team2PlayerInline(admin.TabularInline):
    model = Team2Players    
    extra=1

class TeamScoreInline(admin.TabularInline):
    model = TeamScore 
    extra=1

class HostMatchAdmin(admin.ModelAdmin):
   
    list_display = ('id','user_id', 'title', 'date','time',
    'location','select_mode','status')

    inlines=[HostInvitationInline,Team1PlayerInline,Team2PlayerInline,TeamScoreInline,]


class HostMatchInline(admin.TabularInline):
    model = HostMatch
    extra=1
   

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id','profile_image', 'city', 'state','zip_code',
    'cpf_number','contact_number','location','matchhost','matchplayed','matchwon')

    inlines=[HostMatchInline,HostInvitationInline,]

    




admin.site.register(User,UserAdmin)
admin.site.register(Profile,ProfileAdmin)
admin.site.register(HostMatch,HostMatchAdmin)
admin.site.register(HostInvitation,HostInvitationAdmin)

admin.site.register(Team1Players,Team1PlayerAdmin)
admin.site.register(Team2Players,Team2PlayerAdmin)
admin.site.register(TeamScore,TeamScoreAdmin)
admin.site.register(ContactUs)
admin.site.register(AboutUs)
admin.site.register(PrivacyPolicy)
admin.site.register(TermsCondition)




