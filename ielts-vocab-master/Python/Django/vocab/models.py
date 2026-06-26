from django.db import models


class CEFRLevel(models.Model):
    code  = models.CharField(max_length=2, unique=True)
    name  = models.CharField(max_length=50)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.code


class Color(models.Model):
    name     = models.CharField(max_length=50)
    bg_hex   = models.CharField(max_length=7)
    text_hex = models.CharField(max_length=7)

    def __str__(self):
        return self.name


class Category(models.Model):
    slug       = models.SlugField(max_length=100, unique=True)
    name       = models.CharField(max_length=100)
    icon       = models.CharField(max_length=10, blank=True)
    cefr_level = models.ForeignKey(
        CEFRLevel, null=True, blank=True, on_delete=models.SET_NULL
    )
    color = models.ForeignKey(
        Color, null=True, blank=True, on_delete=models.SET_NULL
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Word(models.Model):
    word       = models.CharField(max_length=200)
    pos        = models.CharField(max_length=20, blank=True)
    definition = models.TextField()
    synonyms   = models.JSONField(default=list)
    antonyms   = models.JSONField(default=list)
    example    = models.TextField(blank=True)
    gap        = models.TextField(blank=True)
    category   = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='words'
    )
    cefr_level = models.ForeignKey(
        CEFRLevel, null=True, blank=True, on_delete=models.SET_NULL
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.word
