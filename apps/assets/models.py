from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Asset(models.Model):
    class AssetType(models.TextChoices):
        HARDWARE = 'HW', 'Hardware'
        SOFTWARE = 'SW', 'Software'
        PERIPHERAL = 'PE', 'Peripheral'
        OFFICE = 'OF', 'Office'

    class Status(models.TextChoices):
        ACTIVE = 'A', 'Active'
        INACTIVE = 'I', 'Inactive'
        TO_DISPOSAL = 'TD', 'Disposal'
        ON_ORDER = 'O', 'On Order'
        NEEDED = 'NE', 'Needed'

    asset_name = models.CharField(max_length=100)
    asset_id = models.CharField(max_length=50, unique=True, blank=True)
    type = models.CharField(max_length=2, choices=AssetType)
    last_pat_test = models.DateField(blank=True, null=True)
    end_of_warranty = models.DateField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=2, choices=Status)

    def save(self, *args, **kwargs):
        self.asset_name = self.asset_name.lower()
        if not self.asset_id:
            existing_count = Asset.objects.filter(
                type=self.type,
                asset_name=self.asset_name
            ).count()
            self.asset_id = f"{self.type}-{self.asset_name}-{existing_count + 1:02d}"
        super().save(*args, **kwargs)

    def display_name(self):
        return self.asset_name.title()

    def __str__(self):
        return f"{self.asset_id} - {self.display_name()}"

class AssetAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    date_given = models.DateField()
    date_retrieved = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.asset.asset_name +  " - " + self.user.get_full_name()
