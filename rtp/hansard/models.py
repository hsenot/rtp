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

    class Meta:
        unique_together = (
            ('parliament_no', 'date', 'session_no', 'period_no', 'chamber')
        )

class DebateReference(models.Model):
    session = models.ForeignKey(SessionReference, on_delete=models.CASCADE)
    debate_title = models.CharField(max_length=255)
    debate_page_no = models.IntegerField()
    subdebate1_title = models.CharField(max_length=2048, null=True)
    subdebate1_page_no = models.IntegerField(null=True)
    subdebate2_title = models.CharField(max_length=2048, null=True)
    subdebate2_page_no = models.IntegerField(null=True)

    class Meta:
        unique_together = (
            ('session', 'debate_title', 'debate_page_no', 'subdebate1_title', 'subdebate1_page_no', 'subdebate2_title', 'subdebate2_page_no')
        )

class Person(models.Model):
    name_id = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=128)
    party = models.CharField(max_length=16)
    # Member of Parliament
    electorate = models.ForeignKey(FederalElectorate2016, on_delete=models.CASCADE, null=True)

class Sentence(models.Model):
    debate_ref = models.ForeignKey(DebateReference, on_delete=models.CASCADE)
    spoken_by = models.ForeignKey(Person, on_delete=models.CASCADE)
    time_talk_started = models.TimeField(null=True)
    talk_type = models.CharField(max_length=32)
    first_speech = models.BooleanField(default=False)
    # The actual sentence
    the_words = models.TextField()