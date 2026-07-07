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


class GrammarTopic(models.Model):
    STAGES = [
        ('beginner', 'Basic'),
        ('independent', 'Intermediate'),
        ('expert', 'Advanced'),
    ]
    slug       = models.SlugField(max_length=100, unique=True)
    title      = models.CharField(max_length=200)
    tag        = models.CharField(max_length=50)
    cefr_label = models.CharField(max_length=10)
    blurb      = models.CharField(max_length=300)
    stage      = models.CharField(max_length=12, choices=STAGES)
    order      = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class GrammarLessonBlock(models.Model):
    TYPES = [
        ('intro', 'Intro'),
        ('rule', 'Rule'),
        ('table', 'Table'),
        ('examples', 'Examples'),
        ('tip', 'Tip'),
    ]
    topic = models.ForeignKey(GrammarTopic, on_delete=models.CASCADE, related_name='blocks')
    type  = models.CharField(max_length=10, choices=TYPES)
    title = models.CharField(max_length=200, blank=True)
    body  = models.TextField(blank=True)
    data  = models.JSONField(default=dict, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.topic.slug} · {self.type} #{self.order}'


class GrammarQuestion(models.Model):
    QTYPES = [
        ('mcq', 'Multiple choice'),
        ('gap', 'Fill the gap'),
        ('transform', 'Transformation'),
    ]
    topic   = models.ForeignKey(GrammarTopic, on_delete=models.CASCADE, related_name='questions')
    qtype   = models.CharField(max_length=10, choices=QTYPES)
    prompt  = models.TextField()
    options = models.JSONField(default=list, blank=True)
    answers = models.JSONField(default=list)
    why     = models.TextField()
    order   = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.topic.slug} · {self.qtype} #{self.order}'
