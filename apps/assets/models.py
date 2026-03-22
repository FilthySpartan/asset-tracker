from django.db import models
from django.contrib.auth.models import User


class Asset(models.Model):
    """Represents a piece of IT or office equipment tracked by the organisation."""

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
    # Auto-generated on first save, unique identifier using type prefix and name (e.g. HW-dell laptop-01)
    asset_id = models.CharField(max_length=50, unique=True, blank=True)
    type = models.CharField(max_length=2, choices=AssetType)
    # Optional because software and office assets don't require PAT testing
    last_pat_test = models.DateField(blank=True, null=True)
    # Optional because some assets may not have a warranty
    end_of_warranty = models.DateField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=2, choices=Status)

    def save(self, *args, **kwargs):
        # Normalise asset name to lowercase for consistent storage and duplicate detection
        self.asset_name = self.asset_name.lower()
        # Generate asset_id only on first save to prevent it changing on update
        if not self.asset_id:
            existing_count = Asset.objects.filter(
                type=self.type,
                asset_name=self.asset_name
            ).count()
            # Format: TYPE-name-XX where XX is a zero-padded sequential number
            self.asset_id = f"{self.type}-{self.asset_name}-{existing_count + 1:02d}"
        super().save(*args, **kwargs)

    def display_name(self):
        """Returns the asset name in title case for display purposes."""
        return self.asset_name.title()

    def current_assignment(self):
        """Returns the active assignment for this asset, or None if unassigned."""
        return self.assetassignment_set.filter(date_retrieved__isnull=True).first()

    def __str__(self):
        return f"{self.asset_id} - {self.display_name()}"


class AssetAssignment(models.Model):
    """
    Links a User to an Asset with date tracking.
    A null date_retrieved indicates the asset is currently assigned.
    Historical records are preserved when assets are reassigned.
    """

    # PROTECT prevents deletion of users or assets that have assignment history
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    date_given = models.DateField()
    # Null when the asset is currently held by the user
    date_retrieved = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.asset.asset_name + " - " + self.user.get_full_name()