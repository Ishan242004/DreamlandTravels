from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_no = models.CharField(max_length=15)
    address = models.TextField()
    photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.first_name

class Package(models.Model):
    package_name = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to="packages/")
    created_at = models.DateTimeField(auto_now_add=True)
    days = models.IntegerField()
    nights = models.IntegerField()
    hotel = models.CharField(max_length=200)
    bus = models.CharField(max_length=200)
    day = models.TextField()
    included = models.TextField()
    category = models.CharField(max_length=100, default='Mountain', choices=[
        ('Beach', 'Beach'),
        ('Mountain', 'Mountain'),
        ('Honeymoon', 'Honeymoon'),
        ('Cultural', 'Cultural'),
    ])

    def __str__(self):
        return self.package_name


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    persons = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20,default="Pending")
    travel_date = models.DateField(null=True, blank=True)
    # return_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} - {self.package.package_name}"

class Destination(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=100)
    image = models.ImageField(upload_to="destinations/")
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class Feedback(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="feedbacks")
    booking = models.OneToOneField(Booking,on_delete=models.CASCADE,related_name="feedback",null=True,blank=True)
    package = models.ForeignKey(Package,on_delete=models.CASCADE,related_name="feedbacks")
    rating = models.PositiveSmallIntegerField()
    review = models.TextField()
    title = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.first_name} - {self.package.package_name}"

class PackageImage(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ImageField(upload_to="packages/gallery/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.package.package_name} - Image {self.id}"


class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="payments")
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default="Credit Card")
    status = models.CharField(max_length=20, default="Successful")  # Successful, Pending, Failed
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.transaction_id} for Booking {self.booking.id}"


class ContactMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="contact_messages")
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    reply_message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default="Unread")  # Unread, Read, Replied
    created_at = models.DateTimeField(auto_now_add=True)
    replied_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.subject}"