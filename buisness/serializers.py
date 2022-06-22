
from rest_framework import serializers
from .models import *
from user.serializers import *
from rest_framework.response import Response
from rest_framework.validators import UniqueTogetherValidator

class BuisnessImagesSerializer(serializers.ModelSerializer):

    class Meta:
        model=BuisnessImages
        fields="__all__"  

class BuisnessSerializer(serializers.ModelSerializer):
    # buisness_images=BuisnessImagesSerializer(many=True,required=False)

    # buisness_owner=UserSerializer1(read_only=True)
    # buisness_imagess = serializers.ListField(child=serializers.ImageField(allow_empty_file=True))
    # images = serializers.ListField(child=serializers.ImageField(allow_empty_file=True))

    class Meta:
        model=Buisness
        fields=('id','user_id','buisness_name','cpf_number','location','tennis_court','address','description','lat','long','buisness_images',)

    # def create(self,validated_data):
    #     buisness_owner=validated_data.get('buisness_owner')
    #     buisness_user=buisness_owner.user_type.role

    #     if buisness_user=='Buisness User':
    #         create_buisness=Buisness.objects.create(**validated_data)
    
    #         try:
    #             # try to get and save images (if any)
    #             images_data = dict((self.context['request'].FILES).lists()).get('buisness_images', None)
    #             print(images_data)
    #             for img in images_data:
    #                 print(img)
    #                 print(type(img))
    #                 BuisnessImages.objects.create(buisness=create_buisness,buisness_images=img)
    #         except:
    #             # if no images are available - create using default image
    #             BuisnessImages.objects.create(buisness=create_buisness)
    #         return create_buisness 
    #     else:
    #         raise serializers.ValidationError("Not a buisness user") 

    def clear_existing_images(self, instance):

        for post_image in instance.buisness_images.all():
            post_image.buisness_images.delete()
            post_image.delete()        

    def update(self,instance,validated_data):
        print(validated_data)   #data which we get through input fileds by user
        print(instance)   # instance means the object we want to update.  
        images = dict((self.context['request'].FILES).lists()).get('buisness_images', None)

        # images = validated_data.pop('images', None)
        print(images)
        if images:
            self.clear_existing_images(instance)   #uncomment this if you want to clear existing images.
            post_image_model_instance = [BuisnessImages(buisness=instance, buisness_images=img) for img in images]
            BuisnessImages.objects.bulk_create(
                post_image_model_instance
            )

        return super().update(instance, validated_data) 

class BuisnessHourSerializer(serializers.ModelSerializer):
    class Meta:
        model=BuisnessHours
        fields="__all__"  

        #through django inbuilt validation
        
        # validators = [
        # UniqueTogetherValidator(
        #    queryset=BuisnessHours.objects.all(),
        #    fields=['day']
        #  )
        # ]


        

    



        