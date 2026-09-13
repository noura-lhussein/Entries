from django.core.management.base import BaseCommand

from dynamic_forms.models import Attribute, MainSection, SubMainSection, Title


class Command(BaseCommand):
    help = 'Seeds the database with dummy test data.'

    def handle(self, *args, **options):
        # Clear existing data out
        MainSection.objects.all().delete()
        Title.objects.all().delete()

        self.stdout.write("Seeding Titles...")
        titles = ['Report Manager', 'Data Entry Specialist', 'Auditor']
        for t in titles:
            Title.objects.create(name=t)

        self.stdout.write("Seeding Sections...")
        # Main Section 1
        ms1 = MainSection.objects.create(name="HR Employee Data")
        SubMainSection.objects.create(
            main_section=ms1, name="Personal Information")
        SubMainSection.objects.create(main_section=ms1, name="Contact Details")

        # Main Section 2
        ms2 = MainSection.objects.create(name="IT Asset Inventory")
        SubMainSection.objects.create(
            main_section=ms2, name="Hardware Assignments")
        SubMainSection.objects.create(
            main_section=ms2, name="Software Licenses")

        self.stdout.write("Seeding Attributes...")
        # Get the titles to link to
        t1 = Title.objects.get(name='Report Manager')
        t2 = Title.objects.get(name='Data Entry Specialist')

        # Pre-seed a couple of attributes just to show them off
        Attribute.objects.create(
            title=t1, label="Full Legal Name", type="text", required=True)
        Attribute.objects.create(
            title=t1, label="Date of Birth", type="date", required=True)

        Attribute.objects.create(
            title=t1, label="Email Address", type="text", required=True)
        Attribute.objects.create(
            title=t1, label="Phone Number", type="number", required=False)

        Attribute.objects.create(
            title=t2, label="Laptop Serial Number", type="text", required=True)
        Attribute.objects.create(
            title=t2, label="Operating System", type="select", required=True)

        self.stdout.write(self.style.SUCCESS(
            "Successfully seeded the database!"))
