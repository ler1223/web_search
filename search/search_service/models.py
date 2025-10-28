from django.db import models


# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=1000)
    main_category = models.CharField(max_length=1000)
    sub_category = models.CharField(max_length=1000)
    image = models.CharField(max_length=1000)
    link = models.CharField(max_length=1000)
    ratings = models.FloatField()
    count_ratings = models.FloatField()
    discount_price = models.FloatField()
    actual_price = models.FloatField()

    def __str__(self):
        return self.name
