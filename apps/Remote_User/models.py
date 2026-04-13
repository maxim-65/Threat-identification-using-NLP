from django.db import models

# Create your models here.
from django.db.models import CASCADE


class ClientRegister_Model(models.Model):
    username = models.CharField(max_length=30)
    email = models.EmailField(max_length=30)
    password = models.CharField(max_length=128)
    phoneno = models.CharField(max_length=10)
    country = models.CharField(max_length=30)
    state = models.CharField(max_length=30)
    city = models.CharField(max_length=30)
    gender= models.CharField(max_length=30)
    address= models.CharField(max_length=30)


class cyber_threat_identification(models.Model):

    fid= models.CharField(max_length=300)
    tweet_text= models.CharField(max_length=3000)
    timestamp= models.CharField(max_length=300)
    source= models.CharField(max_length=300)
    symbols= models.CharField(max_length=300)
    company_names= models.CharField(max_length=300)
    url= models.CharField(max_length=3000)
    source_ip= models.CharField(max_length=300)
    protocol= models.CharField(max_length=300)
    dest_ip= models.CharField(max_length=300)
    Prediction= models.CharField(max_length=300)

class detection_accuracy(models.Model):

    names = models.CharField(max_length=300)
    ratio = models.CharField(max_length=300)

class detection_ratio(models.Model):

    names = models.CharField(max_length=300)
    ratio = models.CharField(max_length=300)


class prediction_audit(models.Model):
    username = models.CharField(max_length=50)
    fid = models.CharField(max_length=300)
    predicted_label = models.CharField(max_length=300)
    confidence = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)



