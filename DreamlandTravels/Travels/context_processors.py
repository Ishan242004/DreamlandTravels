from .models import Package

def popular_packages(request):
    packages = Package.objects.all()[:4]

    return {
        "footer_packages": packages
    }