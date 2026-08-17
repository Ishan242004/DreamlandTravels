from django.contrib import admin
from .models import UserProfile, Package, Booking, Feedback, Payment, ContactMessage


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("package_name", "destination", "price", "days", "nights", "created_at")
    search_fields = ("package_name", "destination")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "package", "persons", "amount", "status", "booking_date")
    list_filter = ("status",)
    search_fields = ("full_name", "email")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_no")

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("user","package","rating","is_approved","created_at")
    list_filter = ("is_approved","rating",)
    search_fields = ("user__username","package__package_name",)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "booking", "amount", "payment_method", "status", "created_at")
    list_filter = ("status", "payment_method")
    search_fields = ("transaction_id", "booking__full_name", "booking__email")

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "subject", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "email", "subject", "message")