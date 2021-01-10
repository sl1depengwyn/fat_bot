
from django.urls import reverse
from django.db.models import *
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models as models
import json

CHOICES = (
    ('low', 'низкий (1-3 дня в неделю)'),
    ('middle','средний (3-5 дней в неделю)'),
    ('high', 'высокий (6-7 дней в неделю)'),
)

class FormsDiets(models.Model):

    # Fields
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_updated = models.DateTimeField(auto_now=True, editable=False)
    form_version = models.CharField(max_length=30, default='oldv1')
    olddietfile = models.CharField(max_length=255, blank=True, default='')
    email = models.CharField(max_length=255, blank=True, default='')
    dietgoal = models.CharField(max_length=30)
    gender = models.CharField(max_length=1, blank=False)
    age = models.SmallIntegerField()
    currentWeight = models.SmallIntegerField()
    desiredWeight = models.SmallIntegerField()
    height = models.SmallIntegerField(null=True, blank=True, default=0)
    drugs = models.TextField(max_length=1000, blank=True, default='')
    forbiddenFood = models.TextField(max_length=1000, blank=True, default='')
    ration = models.TextField(max_length=2000, blank=True, default='')
    breastFeeding = models.CharField(max_length=1)
    pregnant = models.CharField(max_length=1)
    saturation_speed = models.SmallIntegerField(default=10)
    activity = models.CharField(max_length=50, null=True, choices=CHOICES, default='low', blank=True)
    diet_text = models.TextField(max_length=1000000, blank=True, default='')
    
    diet_raw_text = models.TextField(max_length=1000000, blank=True, default='')
    
    disease = models.TextField(max_length=1000, null=True, blank=True, default='')
    calories = models.IntegerField(null=True, blank=True, default=0)
    
    mass_time = models.TextField(max_length=1000, null=True, blank=True, default='')
    date_to_goal = models.TextField(max_length=1000, null=True, blank=True, default='')
    factors = models.TextField(max_length=1000, null=True, blank=True, default='')
    episodes_of_something = models.TextField(max_length=1000, null=True, blank=True, default='')
    physical_activity = models.TextField(max_length=1000, null=True, blank=True, default='')
    do_you_want_special_fitfood = models.TextField(max_length=1000, null=True, blank=True, default='')
    time_of_phis_training = models.TextField(max_length=1000, null=True, blank=True, default='')
    pref_products = models.TextField(max_length=1000, null=True, blank=True, default='')
    calculated_diet_id = models.CharField(max_length=50, null=True, blank=True, default='')
    manually_calculated_diet_id = models.CharField(max_length=50, null=True, blank=True, default='')
    def __str__(self):
        return self.olddietfile


    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return u'%s' % self.pk

    def get_absolute_url(self):
        return reverse('dietForm_formsdiets_detail', args=(self.pk,))


    def get_update_url(self):
        return reverse('dietForm_formsdiets_update', args=(self.pk,))


class CalculatorProductsData(models.Model):

    # Fields
    name = models.CharField(max_length=255)
    proteins = models.FloatField(default=0)
    fats = models.FloatField(default=0)
    carbohydrates = models.FloatField(default=0)
    calories = models.FloatField(default=0)


    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

    class Meta:
        ordering = ('-pk',)

    def __unicode__(self):
        return u'%s' % self.pk

    def get_absolute_url(self):
        return reverse('dietForm_calculatorproductsdata_detail', args=(self.pk,))


    def get_update_url(self):
        return reverse('dietForm_calculatorproductsdata_update', args=(self.pk,))


class UserActions(models.Model):

    email = models.CharField(max_length=50)
    action = models.CharField(max_length=550)
    value = models.TextField()
    attributes = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email
