from django.db import models

# Create your models here.
class Municipality(models.Model): 
    name = models.CharField(max_length=200, unique=True)
    mid = models.IntegerField(unique=True, null=True)
    change = models.ManyToManyField('self', symmetrical=False, through='Changes', through_fields=('old','new'))

class Changes(models.Model):
    old = models.ForeignKey(Municipality, related_name='municipality_old')
    new = models.ForeignKey(Municipality, related_name='municipality_new')
    percent = models.FloatField()
    year = models.IntegerField()

class Population(models.Model):
    municipality = models.ForeignKey(Municipality)
    year = models.IntegerField()
    val = models.IntegerField(null=True)

    class Meta:
        unique_together = ('municipality', 'year')

class GenderPop(models.Model):
	municipality = models.ForeignKey(Municipality)	
	ageclass = models.IntegerField() #0 for 0-4, 1 for 5-9 etc.
	val_m = models.IntegerField()
	val_f = models.IntegerField()
	year = models.IntegerField()

	class Meta:
		unique_together = ('municipality', 'year', 'ageclass')
