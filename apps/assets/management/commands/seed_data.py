from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.assets.models import Asset, AssetAssignment
from datetime import date

# This is the data seeder to populate the database with the required initial data load

class Command(BaseCommand):
    help = "Seeds the database with test data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding database...")

        # Clear existing data
        AssetAssignment.objects.all().delete()
        Asset.objects.all().delete()

        # Create test users (if they don't exist)
        users = []
        test_users = [
            {"username": "eprice", "first_name": "Elliot", "last_name": "Price", "is_staff": True},
            {"username": "smorgan", "first_name": "Sarah", "last_name": "Morgan", "is_staff": False},
            {"username": "jcooper", "first_name": "James", "last_name": "Cooper", "is_staff": False},
            {"username": "lchen", "first_name": "Lisa", "last_name": "Chen", "is_staff": True},
        ]
        for data in test_users:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "is_staff": data["is_staff"],
                }
            )
            if created:
                user.set_password("testpass123")
                user.save()
            users.append(user)

        # Create 10 assets
        assets_data = [
            {"asset_name": "dell latitude 5540", "type": "HW", "last_pat_test": date(2026, 1, 10), "end_of_warranty": date(2028, 3, 15), "cost": 1049.99, "status": "A"},
            {"asset_name": "dell latitude 5540", "type": "HW", "last_pat_test": date(2026, 1, 10), "end_of_warranty": date(2028, 3, 15), "cost": 1049.99, "status": "A"},
            {"asset_name": "dell optiplex 7010", "type": "HW", "last_pat_test": date(2025, 11, 5), "end_of_warranty": date(2027, 9, 30), "cost": 749.99, "status": "A"},
            {"asset_name": "dell u2723qe monitor", "type": "PE", "last_pat_test": date(2025, 12, 1), "end_of_warranty": date(2028, 6, 30), "cost": 489.99, "status": "A"},
            {"asset_name": "dell u2723qe monitor", "type": "PE", "last_pat_test": date(2025, 12, 1), "end_of_warranty": date(2028, 6, 30), "cost": 489.99, "status": "A"},
            {"asset_name": "logitech mx keys and mouse combo", "type": "PE", "last_pat_test": date(2026, 2, 15), "end_of_warranty": date(2027, 8, 1), "cost": 119.99, "status": "A"},
            {"asset_name": "ergonomic wrist rest", "type": "PE", "cost": 24.99, "status": "NE", "last_pat_test": None, "end_of_warranty": None},
            {"asset_name": "standing desk", "type": "OF", "cost": 549.99, "status": "A", "last_pat_test": None, "end_of_warranty": date(2030, 1, 1)},
            {"asset_name": "microsoft 365 business licence", "type": "SW", "cost": 264.00, "status": "A", "last_pat_test": None, "end_of_warranty": date(2027, 4, 1)},
            {"asset_name": "jetbrains all products licence", "type": "SW", "cost": 649.00, "status": "A", "last_pat_test": None, "end_of_warranty": date(2027, 3, 20)},
        ]

        assets = []
        for data in assets_data:
            asset = Asset(**data)
            asset.save()
            assets.append(asset)
            self.stdout.write(f"  Created asset: {asset.asset_id}")

        # Create 10 asset assignments
        assignments_data = [
            {"user": users[0], "asset": assets[0], "date_given": date(2025, 4, 1), "date_retrieved": None},
            {"user": users[1], "asset": assets[1], "date_given": date(2025, 4, 1), "date_retrieved": None},
            {"user": users[2], "asset": assets[2], "date_given": date(2025, 5, 12), "date_retrieved": None},
            {"user": users[0], "asset": assets[3], "date_given": date(2025, 4, 1), "date_retrieved": None},
            {"user": users[1], "asset": assets[4], "date_given": date(2025, 4, 1), "date_retrieved": None},
            {"user": users[0], "asset": assets[5], "date_given": date(2025, 4, 15), "date_retrieved": None},
            {"user": users[3], "asset": assets[7], "date_given": date(2025, 6, 1), "date_retrieved": None},
            {"user": users[0], "asset": assets[8], "date_given": date(2025, 4, 1), "date_retrieved": None},
            {"user": users[2], "asset": assets[9], "date_given": date(2025, 5, 12), "date_retrieved": None},
            {"user": users[3], "asset": assets[3], "date_given": date(2025, 1, 15), "date_retrieved": date(2025, 3, 31)},
        ]

        for data in assignments_data:
            assignment = AssetAssignment(**data)
            assignment.save()
            self.stdout.write(f"  Created assignment: {assignment}")

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))