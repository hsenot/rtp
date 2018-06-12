from django.db import models

from aec.models import *


class SessionReference(models.Model):
    parliament_no = models.IntegerField()
    date = models.DateField()
    session_no = models.IntegerField()
    period_no = models.IntegerField()
    CHAMBERS = (
        ('House of Reps', 'House of Reps'),
        ('Senate', 'Senate'),
    )
    chamber = models.CharField(max_length=16, choices=CHAMBERS)

class DebateReference(models.Model):
    session = models.ForeignKey(SessionReference, on_delete=models.CASCADE)
    debate_title = models.CharField(max_length=128)
    debate_page_no = models.IntegerField()
    subdebate1_title = models.CharField(max_length=128)
    subdebate1_page_no = models.IntegerField()
    subdebate2_title = models.CharField(max_length=128)
    subdebate2_page_no = models.IntegerField()

class Person(models.Model):
    name_id = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=128)
    party = models.CharField(max_length=16)
    # Member of Parliament
    electorate = models.ForeignKey(FederalElectorate2016, on_delete=models.CASCADE, null=True)

class Sentence(models.Model):
    debate_ref = models.ForeignKey(DebateReference, on_delete=models.CASCADE)
    spoken_by = models.ForeignKey(Person, on_delete=models.CASCADE)
    time_talk_started = models.TimeField()
    talk_type = models.CharField(max_length=32)
    first_speech = models.BooleanField(default=False)
    # The actual sentence
    the_words = models.TextField()