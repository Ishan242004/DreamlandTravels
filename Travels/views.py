from .forms import RegisterForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout
from django.utils import timezone
from .models import UserProfile, Package, Booking, Feedback, PackageImage, Payment, ContactMessage
from .forms import PackageForm
from decimal import Decimal
from django.urls import reverse
from django.conf import settings
from django.db.models import Sum
from django.http import JsonResponse
import razorpay
import json
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
import random
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
TAX_AMOUNT = Decimal("180.00")

def is_admin(request):
    return request.session.get("admin", False)

@login_required(login_url="login")
def feedback(request):

    booking_id = request.GET.get("booking")

    if booking_id:
        booking = get_object_or_404(
            Booking,
            id=booking_id,
            user=request.user
        )
    else:
        booking = None

    if request.method == "POST":

        booking = get_object_or_404(
            Booking,
            id=request.POST.get("booking_id"),
            user=request.user
        )

        if hasattr(booking, "feedback"):
            messages.warning(request, "You have already submitted feedback.")
            return redirect("dashboard_history")

        rating = int(request.POST.get("rating") or 5)
        review_text = request.POST.get("review", "")
        default_titles = {
            5: "Excellent Trip!",
            4: "Great Experience",
            3: "Good Trip",
            2: "Below Average",
            1: "Poor Experience"
        }
        title = request.POST.get("title") or default_titles.get(rating, "Trip Review")

        Feedback.objects.create(
            user=request.user,
            booking=booking,
            package=booking.package,
            rating=rating,
            review=review_text,
            title=title,
            is_approved=True
        )

        messages.success(request, "Thank you for your feedback!")

        return redirect("dashboard_history")

    reviews = Feedback.objects.filter(
        is_approved=True
    ).select_related(
        "user",
        "package"
    ).order_by("-created_at")

    return render(request, "feedback.html", {
        "booking": booking,
        "reviews": reviews
    })


def about(request):

    total_travelers = (Booking.objects.filter(status="Paid").aggregate(total=Sum("persons"))["total"] or 0)
    total_destinations = (Package.objects.values("destination").distinct().count())
    context = {"total_travelers": total_travelers,"total_destinations": total_destinations,}

    return render(request, "about.html", context)

from django.db.models import Count

def index(request):
    packages = Package.objects.all()[:3]

    destinations = (
        Package.objects
        .values("destination")
        .annotate(total_tours=Count("id"))
        .order_by("-total_tours")
    )

    destination_cards = []

    for item in destinations:

        first_package = Package.objects.filter(
            destination=item["destination"]
        ).first()

        destination_cards.append({
            "destination": item["destination"],
            "image": first_package.image if first_package else None,
            "total_tours": item["total_tours"],
        })

    total_travelers = (Booking.objects.filter(status="Paid").aggregate(total=Sum("persons"))["total"] or 0)
    total_destinations = (Package.objects.values("destination").distinct().count())
    context = {"total_travelers": total_travelers,"total_destinations": total_destinations,}

    reviews = (
        Feedback.objects
        .filter(is_approved=True)
        .select_related("user", "package")
        .order_by("-created_at")[:3]
    )

    destination_cards = (
    Package.objects
    .annotate(
        total_tours=Count(
            "booking",
            filter=Q(booking__status="Paid")
        )
    )
    .filter(total_tours__gt=0)
    .order_by("-total_tours")[:3]
)

    unique_destinations = Package.objects.values_list('destination', flat=True).distinct().order_by('destination')

    context = {
        "packages": packages,
        "destination_cards": destination_cards,
        "total_travelers": total_travelers,
        "total_destinations": total_destinations,
        "reviews": reviews,
        "unique_destinations": unique_destinations,
    }
    return render(request, "index.html", context)


def add_package(request):
    if not is_admin(request):
        return redirect("admin_login")

    if request.method == "POST":
        package_name = request.POST.get("package_name")
        destination = request.POST.get("destination")
        days = request.POST.get("days")
        nights = request.POST.get("nights")
        price = request.POST.get("price")
        hotel = request.POST.get("hotel_t")
        bus = request.POST.get("bus_t")
        description = request.POST.get("description")
        image = request.FILES.get("image")
        day = request.POST.get("day_w")
        included = request.POST.get("include_f")
        category = request.POST.get("category", "Mountain")
        Package.objects.create(
            package_name=package_name,
            destination=destination,
            days=days,
            nights=nights,
            price=price,
            hotel=hotel,
            bus=bus,
            description=description,
            image=image,
            day=day,
            included=included,
            category=category,
        )

        messages.success(request, "Package Added Successfully.")
        return redirect("add_package")

    return render(request, "add-package.html")



def admin_dashboard(request):
    if not is_admin(request):
        return redirect("admin_login")

    all_bookings = Booking.objects.select_related("user", "package").all()
    paid_bookings = all_bookings.filter(status="Paid")

    context = {
        "total_users": User.objects.filter(is_staff=False).count(),
        "total_packages": Package.objects.count(),
        "total_bookings": all_bookings.count(),
        "pending_bookings": all_bookings.filter(status__in=["Pending", "Pending Payment"]).count(),
        "approved_bookings": paid_bookings.count(),
        "cancelled_bookings": all_bookings.filter(status="Cancelled").count(),
        "total_revenue": paid_bookings.aggregate(total=Sum("amount"))["total"] or 0,
        "recent_bookings": all_bookings.order_by("-booking_date")[:8],
    }

    return render(request, "admin-dashboard.html", context)

from django.contrib.auth import logout
from django.contrib import messages

def admin_login(request):
    if is_admin(request):
        return redirect("admin_dashboard")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        if email == "admin@gmail.com" and password == "admin1":
            request.session["admin"] = True
            messages.success(request, "Admin Login Successful.")
            return redirect("admin_dashboard")
        messages.error(request, "Invalid Admin Email or Password")

    return render(request, "admin-login.html")

def user_logout(request):
    logout(request)
    request.session.flush()
    messages.success(request, "Logout Successful.")

    return redirect("index")

def booking_summary(request, id):
    booking = get_object_or_404(Booking, id=id)

    package = booking.package

    persons = booking.persons
    taxes = TAX_AMOUNT
    subtotal = package.price * persons
    total = subtotal + taxes
    context = {
        "booking": booking,
        "package": package,
        "persons": persons,
        "subtotal": subtotal,
        "taxes": taxes,
        "total": total,
        "booking_created": True,
    }
    return render(request, "booking-summary.html", context)


def booking(request, id):
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to continue your booking.")
        return redirect(f"{reverse('login')}?next={request.path}")

    package = get_object_or_404(Package, id=id)
    profile = UserProfile.objects.get(user=request.user)

    from datetime import date, datetime, timedelta

    # 1. Calculate available travel dates (next 3 weeks / 21 days from today)
    today = date.today()
    three_weeks_later = today + timedelta(days=20)

    # 2. Exclude dates that already have an active booking for this package
    booked_dates = Booking.objects.filter(
        package=package,
        travel_date__range=[today, three_weeks_later]
    ).exclude(status="Cancelled").values_list('travel_date', flat=True)
    booked_dates_set = set(booked_dates)

    available_dates = []
    for i in range(21):
        d = today + timedelta(days=i)
        if d not in booked_dates_set:
            available_dates.append(d)

    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        # Enforce OTP verification protection
        if not request.session.get('booking_otp_verified', False) or request.session.get('booking_otp_verified_email') != email:
            messages.error(request, "Email verification is required to complete the booking. Please verify your email using OTP.")
            return redirect("booking", id=id)

        persons = int(request.POST.get("persons") or 1)
        persons = max(1, persons)
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        travel_date_str = request.POST.get("travel_date")

        if not travel_date_str:
            messages.error(request, "Please select a travel date.")
            return redirect("booking", id=id)

        try:
            selected_date = datetime.strptime(travel_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect("booking", id=id)

        # 3. Secure backend validation to ensure the date is allowed
        if selected_date < today or selected_date > three_weeks_later or selected_date in booked_dates_set:
            messages.error(request, "The selected date is not available. Please choose another date.")
            return redirect("booking", id=id)

        taxes = TAX_AMOUNT
        subtotal = package.price * persons
        total = subtotal + taxes

        booking = Booking.objects.create(
            user=request.user,
            package=package,
            full_name=full_name,
            email=email,
            phone=phone,
            persons=persons,
            amount=total,
            status="Pending Payment",
            travel_date=selected_date,
        )
        # Clear session OTP variables after successful booking creation
        request.session.pop('booking_otp_verified', None)
        request.session.pop('booking_otp_verified_email', None)

        Payment.objects.create(
            booking=booking,
            transaction_id=f"TXN-PENDING-{booking.id}",
            amount=total,
            payment_method="UPI/Card",
            status="Pending"
        )
        messages.success(request, "Booking created successfully.")  
        return redirect("booking_summary", id=booking.id)

    # 4. Existing Booking Check
    booking = Booking.objects.filter(
        user=request.user,
        package=package
    ).last()

    if booking:
        persons = booking.persons
        booking_created = True
    else:
        persons = 1
        booking_created = False
    # 5. Calculate Amount
    taxes = TAX_AMOUNT
    subtotal = package.price * persons
    total = subtotal + taxes
    # 6. Send Data to Template
    context = {
        "package": package,
        "booking": booking,
        "booking_created": booking_created,
        "persons": persons,
        "subtotal": subtotal,
        "taxes": taxes,
        "total": total,
        "profile": profile,
        "min_date": today.strftime('%Y-%m-%d'),
        "max_date": three_weeks_later.strftime('%Y-%m-%d'),
        "booked_dates_json": json.dumps([d.strftime('%Y-%m-%d') for d in booked_dates]),
        "booked_dates_formatted": [d.strftime('%B %d, %Y') for d in booked_dates],
    }
    return render(request, "booking.html", context)


def cancel_booking(request, id):
    booking = get_object_or_404(Booking, id=id)
    if is_admin(request):
        if request.method == "POST":
            booking.status = "Cancelled"
            booking.save()
            messages.success(request, "Booking cancelled successfully.")
            return redirect("index")
        return render(request, "cancel-booking.html", {
            "booking": booking
        })
    if not request.user.is_authenticated:
        return redirect("login")

    if booking.user != request.user:
        messages.error(request, "You cannot cancel this booking.")
        return redirect("dashboard_bookings")

    if request.method == "POST":
        booking.status = "Cancelled"
        booking.save()
        messages.success(request, "Booking cancelled successfully.")
        return redirect("dashboard_bookings")
    return render(request, "cancel-booking.html", {
        "booking": booking
    })

def delete_booking(request, id):

    if not is_admin(request):
        return redirect("admin_login")
    if request.method == "POST":
        booking = get_object_or_404(Booking, id=id)
        booking.delete()
        messages.success(request, "Booking deleted successfully.")

    return redirect("manage_bookings")

@login_required(login_url="login")
def confirmation(request):
    booking_id = request.GET.get("booking_id")
    booking = None
    if booking_id:
        booking = Booking.objects.filter(id=booking_id, user=request.user).select_related("package").first()
    return render(request, "confirmation.html", {"booking": booking})

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        ContactMessage.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message,
            status="Unread"
        )
        messages.success(request, "Your message has been sent successfully!")
        return redirect("contact")

    return render(request, 'contact.html')

def get_dashboard_context(request, active_tab):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    # GET request data
    bookings = Booking.objects.filter(user=request.user).select_related("package").prefetch_related("feedback").order_by("-booking_date")    
    today = timezone.localdate()

    # Calculate stats
    total_bookings = bookings.count()
    upcoming_count = bookings.filter(travel_date__gte=today).exclude(status="Cancelled").count()
    completed_count = bookings.filter(travel_date__lt=today).exclude(status="Cancelled").count()
    total_spent = bookings.filter(status="Paid").aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    total_destinations = Package.objects.values("destination").distinct().count()

    # Fetch messages and admin replies for current user
    contact_messages = ContactMessage.objects.filter(user=request.user).order_by("-created_at")

    return {
        "bookings": bookings,
        "total_bookings": total_bookings,
        "upcoming_count": upcoming_count,
        "completed_count": completed_count,
        "total_spent": total_spent,
        "profile": profile,
        "contact_messages": contact_messages,
        "active_tab": active_tab,
        "today": today,
        "total_destinations": total_destinations,
    }

@login_required(login_url="login")
def dashboard(request):
    return redirect("dashboard_profile")

@login_required(login_url="login")
def dashboard_profile(request):
    context = get_dashboard_context(request, 'profile')
    return render(request, 'dashboard.html', context)

@login_required(login_url="login")
def dashboard_bookings(request):
    context = get_dashboard_context(request, 'bookings')
    return render(request, 'dashboard.html', context)

@login_required(login_url="login")
def dashboard_history(request):
    context = get_dashboard_context(request, 'history')
    return render(request, 'dashboard.html', context)

@login_required(login_url="login")
def dashboard_messages(request):
    context = get_dashboard_context(request, 'messages')
    return render(request, 'dashboard.html', context)

@login_required(login_url="login")
def dashboard_edit_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        date_of_birth = request.POST.get("date_of_birth") or None
        gender = request.POST.get("gender", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        country = request.POST.get("country", "").strip()
        pincode = request.POST.get("pincode", "").strip()
        photo = request.FILES.get("photo")

        # Validation
        if User.objects.filter(username=username).exclude(id=request.user.id).exists():
            messages.error(request, "Username already exists.")
            return redirect("dashboard_edit_profile")
        if User.objects.filter(email=email).exclude(id=request.user.id).exists():
            messages.error(request, "Email already exists.")
            return redirect("dashboard_edit_profile")

        # Update User
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email
        user.save()

        # Update UserProfile
        profile.phone_no = phone
        profile.address = address
        profile.date_of_birth = date_of_birth
        profile.gender = gender
        profile.city = city
        profile.state = state
        profile.country = country
        profile.pincode = pincode
        if photo:
            profile.photo = photo
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("dashboard_profile")

    context = get_dashboard_context(request, 'edit')
    return render(request, 'dashboard.html', context)


# @login_required(login_url="login")
def invoice(request, id):
    booking = get_object_or_404(Booking, id=id)

    if booking.user_id != request.user.id and not is_admin(request):
        messages.error(request, "You don't have access to this invoice.")
        return redirect("dashboard_bookings")

    package = booking.package
    taxes = TAX_AMOUNT
    subtotal = package.price * booking.persons
    total = subtotal + taxes

    context = {
        "booking": booking,
        "package": package,
        "subtotal": subtotal,
        "taxes": taxes,
        "total": total,
    }
    return render(request, "invoice.html", context)

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "You are not registered. Please register first.")
            return redirect("register")
        user = authenticate(
            request,
            username=user.username,
            password=password
        )
        if user is None:
            messages.error(request, "Invalid Email or Password.")
            return redirect("login")
        
        # Direct login without OTP
        auth_login(request, user)
        messages.success(request, "Login Successful.")
        
        next_url = request.GET.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("index")

    return render(request, "login.html")

    

def manage_bookings(request):
    if not is_admin(request):
        return redirect("admin_login")
    bookings = Booking.objects.select_related("user", "package").order_by("-booking_date")
    return render(request, 'manage-bookings.html', {"bookings": bookings})

def manage_packages(request):
    if not is_admin(request):
        return redirect("admin_login")
    packages = Package.objects.all().order_by("-created_at")
    return render(request, 'manage-packages.html', {"packages": packages})

def manage_users(request):
    if not is_admin(request):
        return redirect("admin_login")
    users = User.objects.filter(is_staff=False).select_related("userprofile").order_by("-date_joined")
    return render(request, 'manage-users.html', {"users": users})

import re

def parse_itinerary(itinerary_text):
    if not itinerary_text:
        return []
    
    text = itinerary_text.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    itinerary = []
    current_day = None
    current_desc = []
    
    day_match_pattern = re.compile(r'^\s*Day\s+(\d+)\s*:?\s*(.*)$', re.IGNORECASE)
    
    for line in lines:
        match = day_match_pattern.match(line)
        if match:
            if current_day:
                current_day['description'] = '\n'.join(current_desc).strip()
                itinerary.append(current_day)
            
            day_num = match.group(1)
            title = match.group(2).strip().replace('\ufffd', '–')
            current_day = {
                'day_num': day_num,
                'title': title,
                'description': ''
            }
            current_desc = []
        else:
            if current_day is not None:
                current_desc.append(line)
                
    if current_day:
        current_day['description'] = '\n'.join(current_desc).strip()
        itinerary.append(current_day)
        
    return itinerary

def package_details(request, id):
    package = get_object_or_404(Package, id=id)
    itinerary_list = parse_itinerary(package.day)
    return render(request, "package-details.html", {
        "package": package,
        "itinerary_list": itinerary_list
    })

from django.contrib import messages

MAX_PACKAGE_IMAGES = 5
def package_edit(request, id):
    if not is_admin(request):
        return redirect("admin_login")

    package = get_object_or_404(Package, id=id)

    if request.method == "POST":
        form = PackageForm(request.POST, request.FILES, instance=package)
        if form.is_valid():
            form.save()

            remove_ids = request.POST.getlist("remove_images")
            if remove_ids:
                PackageImage.objects.filter(id__in=remove_ids, package=package).delete()

            new_images = request.FILES.getlist("gallery_images")
            if new_images:
                slots_left = MAX_PACKAGE_IMAGES - package.gallery_images.count()
                if slots_left <= 0:
                    messages.warning(
                        request,
                        f"Maximum {MAX_PACKAGE_IMAGES} images allowed per package. Remove an image before adding more."
                    )
                else:
                    for image_file in new_images[:slots_left]:
                        PackageImage.objects.create(package=package, image=image_file)
                    if len(new_images) > slots_left:
                        messages.warning(
                            request,
                            f"Only {slots_left} image(s) were added. Maximum {MAX_PACKAGE_IMAGES} images allowed per package."
                        )

            messages.success(request, "Package updated successfully.")
            return redirect("package_edit", id=package.id)
        messages.error(request, "Please correct the errors below.")
    else:
        form = PackageForm(instance=package)

    gallery_images = package.gallery_images.all()
    context = {
        "package": package,
        "form": form,
        "gallery_images": gallery_images,
        "max_images": MAX_PACKAGE_IMAGES,
        "slots_left": max(MAX_PACKAGE_IMAGES - gallery_images.count(), 0),
    }
    return render(request, "package-edit.html", context)

def package_delete(request, id):
    if not is_admin(request):
        return redirect("admin_login")

    package = get_object_or_404(Package, id=id)

    if request.method == "POST":
        package.delete()
        messages.success(request, "Package deleted successfully.")
        return redirect("manage_packages")

    return redirect("package_edit", id=package.id)

def packages(request):
    packages = Package.objects.all()

    # Destination / Location search
    destination = request.GET.get('destination', '').strip()
    if destination:
        packages = packages.filter(
            Q(destination__icontains=destination) | 
            Q(package_name__icontains=destination)
        )

    # General search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        packages = packages.filter(
            Q(package_name__icontains=search_query) |
            Q(destination__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Category filter
    category = request.GET.get('category', '').strip()
    if category and category.lower() != 'all':
        packages = packages.filter(category__iexact=category)

    # Budget filter
    budget = request.GET.get('budget', '').strip()
    if budget:
        if budget == 'under_1000':
            packages = packages.filter(price__lt=1000)
        elif budget == '1000_5000':
            packages = packages.filter(price__gte=1000, price__lte=5000)
        elif budget == 'above_5000':
            packages = packages.filter(price__gt=5000)

    # Sorting
    sort_by = request.GET.get('sort', '').strip()
    if sort_by == 'price_asc':
        packages = packages.order_by('price')
    elif sort_by == 'price_desc':
        packages = packages.order_by('-price')
    elif sort_by == 'name_asc':
        packages = packages.order_by('package_name')
    elif sort_by == 'name_desc':
        packages = packages.order_by('-package_name')
    else:
        packages = packages.order_by('-created_at')

    unique_packages = (
        Package.objects
        .values_list("package_name", flat=True)
        .distinct()
        .order_by("package_name")
    )


    context = {
        "packages": packages,
        "destination": destination,
        "search_query": search_query,
        "category": category,
        "budget": budget,
        "sort_by": sort_by,
        "unique_packages": unique_packages,

    }
    return render(request, "packages.html", context)


def payment(request, id):

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    print("KEY:", settings.RAZORPAY_KEY_ID)

    booking = get_object_or_404(Booking, id=id)

    package = booking.package
    persons = booking.persons

    taxes = TAX_AMOUNT
    subtotal = package.price * persons
    total = subtotal + taxes

    amount = int(total * 100)

    print("AMOUNT:", amount)

    razorpay_order = client.order.create({
        "amount": amount,
        "currency": "INR"
    })

    context = {
        "booking": booking,
        "package": package,
        "persons": persons,
        "subtotal": subtotal,
        "taxes": taxes,
        "total": total,
        "total_paise": amount,
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    }

    return render(request, "payment.html", context)

def payment_success(request):

    if request.method == "POST":

        data = json.loads(request.body)

        params = {
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"],
        }

        try:
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            client.utility.verify_payment_signature(params)

            booking = Booking.objects.get(id=data["booking_id"])
            booking.status = "Paid"
            booking.save()

            payment_method = data.get("payment_method", "Credit Card")
            payment, created = Payment.objects.get_or_create(
                booking=booking,
                defaults={
                    'transaction_id': data["razorpay_payment_id"],
                    'amount': booking.amount,
                    'payment_method': payment_method,
                    'status': 'Successful'
                }
            )
            if not created:
                payment.transaction_id = data["razorpay_payment_id"]
                payment.payment_method = payment_method
                payment.status = "Successful"
                payment.created_at = timezone.now()
                payment.save()

            return JsonResponse({"status": "success"})

        except Exception:

            return JsonResponse({"status": "failed"})

    return JsonResponse({"status": "failed"})

def register(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        phone_no = request.POST.get("phone_no")
        address = request.POST.get("address")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("register")

        user = User.objects.create_user(
            username=email,
            first_name=full_name,
            email=email,
            password=password
        )
        UserProfile.objects.create(
            user=user,
            phone_no=phone_no,
            address=address
        )

        # Send confirmation email
        subject = "Registration Successful - Dreamland Travels"
        message_body = (
            f"Dear {full_name},\n\n"
            "Welcome to Dreamland Travels!\n\n"
            "We are thrilled to confirm that your account has been successfully created. "
            "You are now ready to explore our hand-picked luxury tour packages and plan your dream vacation.\n\n"
            "Login Details:\n"
            f"- Username / Email: {email}\n\n"
            "To log in and start booking, please visit: http://127.0.0.1:8000/login/\n\n"
            "Best regards,\n"
            "The Dreamland Travels Team\n"
            "🧭 Wander further into dreamland"
        )
        try:
            send_mail(
                subject=subject,
                message=message_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            # Safe fallback if SMTP fails (registration remains successful)
            pass

        messages.success(request, "Registration Successful.")
        return redirect("login")

    return render(request, "register.html")


def admin_payments(request):
    if not is_admin(request):
        return redirect("admin_login")

    payments = Payment.objects.select_related("booking", "booking__package", "booking__user").all()

    # Search
    search_query = request.GET.get("search", "").strip()
    if search_query:
        payments = payments.filter(
            Q(booking__full_name__icontains=search_query) |
            Q(booking__email__icontains=search_query) |
            Q(booking__phone__icontains=search_query) |
            Q(transaction_id__icontains=search_query) |
            Q(booking__package__package_name__icontains=search_query) |
            Q(booking__id__icontains=search_query)
        )

    # Filters
    status_filter = request.GET.get("status", "")
    if status_filter:
        payments = payments.filter(status=status_filter)

    method_filter = request.GET.get("method", "")
    if method_filter:
        payments = payments.filter(payment_method=method_filter)

    package_filter = request.GET.get("package", "")
    if package_filter:
        payments = payments.filter(booking__package_id=package_filter)

    date_filter = request.GET.get("date", "")
    if date_filter:
        try:
            payments = payments.filter(created_at__date=date_filter)
        except Exception:
            pass

    # Sorting
    sort_by = request.GET.get("sort", "-created_at")
    if sort_by in ["created_at", "-created_at", "amount", "-amount", "booking__id", "-booking__id"]:
        payments = payments.order_by(sort_by)
    else:
        payments = payments.order_by("-created_at")

    # Summary Stats
    total_payments = Payment.objects.count()
    successful_payments = Payment.objects.filter(status="Successful").count()
    pending_payments = Payment.objects.filter(status="Pending").count()
    failed_payments = Payment.objects.filter(status="Failed").count()
    total_revenue = Payment.objects.filter(status="Successful").aggregate(total=Sum("amount"))["total"] or 0

    packages = Package.objects.all().order_by("package_name")

    context = {
        "payments": payments,
        "total_payments": total_payments,
        "successful_payments": successful_payments,
        "pending_payments": pending_payments,
        "failed_payments": failed_payments,
        "total_revenue": total_revenue,
        "packages": packages,
        "search_query": search_query,
        "status_filter": status_filter,
        "method_filter": method_filter,
        "package_filter": package_filter,
        "date_filter": date_filter,
        "sort_by": sort_by,
        "active_tab": "payments",
    }
    return render(request, "admin-payments.html", context)


def admin_contact_messages(request):
    if not is_admin(request):
        return redirect("admin_login")

    messages_list = ContactMessage.objects.all()

    # Search
    search_query = request.GET.get("search", "").strip()
    if search_query:
        messages_list = messages_list.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(message__icontains=search_query)
        )

    # Filters
    status_filter = request.GET.get("status", "")
    if status_filter:
        messages_list = messages_list.filter(status=status_filter)

    # Sort
    sort_by = request.GET.get("sort", "-created_at")
    if sort_by in ["created_at", "-created_at"]:
        messages_list = messages_list.order_by(sort_by)
    else:
        messages_list = messages_list.order_by("-created_at")

    # Counts
    total_messages = ContactMessage.objects.count()
    unread_count = ContactMessage.objects.filter(status="Unread").count()
    read_count = ContactMessage.objects.filter(status="Read").count()
    replied_count = ContactMessage.objects.filter(status="Replied").count()

    context = {
        "messages_list": messages_list,
        "total_messages": total_messages,
        "unread_count": unread_count,
        "read_count": read_count,
        "replied_count": replied_count,
        "search_query": search_query,
        "status_filter": status_filter,
        "sort_by": sort_by,
        "active_tab": "contact_messages",
    }
    return render(request, "admin-contact-messages.html", context)


def mark_message_read(request, id):
    if not is_admin(request):
        return redirect("admin_login")
    msg = get_object_or_404(ContactMessage, id=id)
    msg.status = "Read"
    msg.save()
    messages.success(request, "Message marked as read.")
    return redirect("admin_contact_messages")


def mark_message_replied(request, id):
    if not is_admin(request):
        return redirect("admin_login")
    msg = get_object_or_404(ContactMessage, id=id)
    msg.status = "Replied"
    msg.save()
    messages.success(request, "Message marked as replied.")
    return redirect("admin_contact_messages")


def delete_message(request, id):
    if not is_admin(request):
        return redirect("admin_login")
    msg = get_object_or_404(ContactMessage, id=id)
    msg.delete()
    messages.success(request, "Message deleted successfully.")
    return redirect("admin_contact_messages")


def admin_reply_message(request, id):
    if not is_admin(request):
        return redirect("admin_login")
    if request.method == "POST":
        msg = get_object_or_404(ContactMessage, id=id)
        reply_text = request.POST.get("reply_message", "").strip()
        if reply_text:
            msg.reply_message = reply_text
            msg.status = "Replied"
            msg.replied_at = timezone.now()
            msg.save()
            messages.success(request, f"Reply successfully sent to {msg.name}.")
        else:
            messages.error(request, "Reply message cannot be empty.")
    return redirect("admin_contact_messages")


def admin_feedback(request):
    if not is_admin(request):
        return redirect("admin_login")

    feedbacks = Feedback.objects.select_related("user", "package", "booking").all()

    # Search
    search_query = request.GET.get("search", "").strip()
    if search_query:
        feedbacks = feedbacks.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(package__package_name__icontains=search_query) |
            Q(package__destination__icontains=search_query) |
            Q(review__icontains=search_query) |
            Q(title__icontains=search_query)
        )

    # Filters
    package_filter = request.GET.get("package", "")
    if package_filter:
        feedbacks = feedbacks.filter(package_id=package_filter)

    rating_filter = request.GET.get("rating", "")
    if rating_filter:
        feedbacks = feedbacks.filter(rating=rating_filter)

    # Sorting
    sort_by = request.GET.get("sort", "-created_at")
    if sort_by in ["created_at", "-created_at", "rating", "-rating"]:
        feedbacks = feedbacks.order_by(sort_by)
    else:
        feedbacks = feedbacks.order_by("-created_at")

    # Counts
    total_reviews = Feedback.objects.count()
    five_star_reviews = Feedback.objects.filter(rating=5).count()
    pending_reviews = Feedback.objects.filter(is_approved=False).count()
    avg_rating = Feedback.objects.aggregate(avg=Sum("rating"))["avg"]
    if total_reviews > 0 and avg_rating is not None:
        avg_rating = round(avg_rating / total_reviews, 1)
    else:
        avg_rating = 0.0

    packages = Package.objects.all().order_by("package_name")

    context = {
        "feedbacks": feedbacks,
        "total_reviews": total_reviews,
        "five_star_reviews": five_star_reviews,
        "pending_reviews": pending_reviews,
        "avg_rating": avg_rating,
        "packages": packages,
        "search_query": search_query,
        "package_filter": package_filter,
        "rating_filter": rating_filter,
        "sort_by": sort_by,
        "active_tab": "feedback",
    }
    return render(request, "admin-feedback.html", context)


def delete_feedback(request, id):
    if not is_admin(request):
        return redirect("admin_login")
    fb = get_object_or_404(Feedback, id=id)
    fb.delete()
    messages.success(request, "Feedback deleted successfully.")
    return redirect("admin_feedback")


def admin_profile(request):
    if not is_admin(request):
        return redirect("admin_login")
        
    admin_username = request.session.get("admin_username")
    admin_user = None
    if admin_username:
        try:
            admin_user = User.objects.get(username=admin_username)
        except User.DoesNotExist:
            pass
            
    if not admin_user:
        admin_user = User.objects.filter(is_superuser=True).first()
        
    context = {
        "admin_user": admin_user,
        "active_tab": "admin_profile",
    }
    return render(request, "admin-profile.html", context)

def booking_send_otp(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed."}, status=405)
    
    try:
        content_type = request.META.get("CONTENT_TYPE", "")
        if "application/json" in content_type:
            data = json.loads(request.body)
            email = data.get("email", "").strip()
        else:
            email = request.POST.get("email", "").strip()
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid request format."}, status=400)
        
    if not email:
        return JsonResponse({"success": False, "error": "Email address is required."}, status=400)
        
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({"success": False, "error": "Please enter a valid email address."}, status=400)
        
    # Generate OTP
    otp = str(random.randint(100000, 999999))
    
    # Save in session
    request.session['booking_otp'] = otp
    request.session['booking_otp_email'] = email
    request.session['booking_otp_expiry'] = (timezone.now() + timedelta(minutes=5)).isoformat()
    request.session['booking_otp_attempts'] = 0
    request.session['booking_otp_verified'] = False
    
    # Send Email
    try:
        send_mail(
            subject="Dreamland Travels - Booking Verification OTP",
            message=f"""Hello,

Your verification OTP for booking your trip with Dreamland Travels is:

{otp}

This OTP is valid for 5 minutes. If you did not request this booking, please ignore this email.

Best regards,
Dreamland Travels Team""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Failed to send email: {str(e)}"}, status=500)
        
    return JsonResponse({"success": True, "message": "OTP sent successfully! Please check your email."})


def booking_verify_otp(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed."}, status=405)
        
    try:
        content_type = request.META.get("CONTENT_TYPE", "")
        if "application/json" in content_type:
            data = json.loads(request.body)
            email = data.get("email", "").strip()
            otp = data.get("otp", "").strip()
        else:
            email = request.POST.get("email", "").strip()
            otp = request.POST.get("otp", "").strip()
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid request format."}, status=400)
        
    if not email or not otp:
        return JsonResponse({"success": False, "error": "Email and OTP are both required."}, status=400)
        
    session_otp = request.session.get('booking_otp')
    session_email = request.session.get('booking_otp_email')
    session_expiry_str = request.session.get('booking_otp_expiry')
    attempts = request.session.get('booking_otp_attempts', 0)
    
    if not session_otp or not session_email or session_email != email:
        return JsonResponse({"success": False, "error": "No active OTP request found for this email. Please request a new OTP."}, status=400)
        
    if attempts >= 3:
        # OTP is locked
        request.session.pop('booking_otp', None)
        request.session.pop('booking_otp_email', None)
        request.session.pop('booking_otp_expiry', None)
        return JsonResponse({"success": False, "error": "Too many failed attempts. This OTP has been invalidated. Please request a new OTP."}, status=400)
        
    if session_expiry_str:
        try:
            expiry = timezone.datetime.fromisoformat(session_expiry_str)
            if timezone.now() > expiry:
                request.session.pop('booking_otp', None)
                request.session.pop('booking_otp_email', None)
                request.session.pop('booking_otp_expiry', None)
                return JsonResponse({"success": False, "error": "OTP has expired. Please request a new OTP."}, status=400)
        except Exception:
            pass
            
    if otp == session_otp:
        # Success
        request.session['booking_otp_verified'] = True
        request.session['booking_otp_verified_email'] = email
        request.session.pop('booking_otp', None) # invalidate OTP so it cannot be reused
        request.session.pop('booking_otp_expiry', None)
        return JsonResponse({"success": True, "message": "OTP verified successfully!"})
    else:
        # Failed attempt
        attempts += 1
        request.session['booking_otp_attempts'] = attempts
        remaining = 3 - attempts
        if remaining <= 0:
            request.session.pop('booking_otp', None)
            request.session.pop('booking_otp_email', None)
            request.session.pop('booking_otp_expiry', None)
            return JsonResponse({"success": False, "error": "Too many failed attempts. This OTP has been invalidated. Please request a new OTP."}, status=400)
        else:
            return JsonResponse({"success": False, "error": f"Invalid OTP. {remaining} attempt(s) remaining."}, status=400)


from django.contrib.auth.password_validation import validate_password

def password_reset_send_otp(request):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Method not allowed."},
            status=405
        )

    try:
        content_type = request.META.get("CONTENT_TYPE", "")
        if "application/json" in content_type:
            data = json.loads(request.body)
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            confirm_password = data.get("confirm_password", "")
        else:
            email = request.POST.get("email", "").strip().lower()
            password = request.POST.get("password", "")
            confirm_password = request.POST.get("confirm_password", "")
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse(
            {"success": False, "error": "Invalid request format."},
            status=400
        )

    # Required fields
    if not email or not password or not confirm_password:
        return JsonResponse(
            {"success": False, "error": "All fields are required."},
            status=400
        )
    # Validate email
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse(
            {
                "success": False,
                "error": "Please enter a valid email address."
            },
            status=400
        )
    # Check password match
    if password != confirm_password:
        return JsonResponse(
            {
                "success": False,
                "error": "Passwords do not match."
            },
            status=400
        )
    # Check user first
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return JsonResponse(
            {
                "success": False,
                "error": "No account is registered with this email address."
            },
            status=404
        )
    # Validate password strength
    try:
        validate_password(password, user)
    except ValidationError as e:
        return JsonResponse(
            {
                "success": False,
                "error": " ".join(e.messages)
            },
            status=400
        )
    # Generate secure 6-digit OTP
    otp = str(random.SystemRandom().randint(100000, 999999))
    # Save OTP details in session
    request.session["reset_otp"] = otp
    request.session["reset_otp_email"] = email
    request.session["reset_otp_expiry"] = (
        timezone.now() + timedelta(minutes=10)
    ).isoformat()
    request.session["reset_otp_attempts"] = 0
    request.session.modified = True
    # Send OTP email
    try:
        send_mail(
            subject="Dreamland Travels - Password Reset OTP",
            message=(
                "Hello,\n\n"
                "Your Dreamland Travels password reset OTP is:\n\n"
                f"{otp}\n\n"
                "This OTP will expire in 10 minutes.\n\n"
                "If you did not request a password reset, "
                "please ignore this email.\n\n"
                "Regards,\n"
                "Dreamland Travels"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        # Remove OTP if email failed
        request.session.pop("reset_otp", None)
        request.session.pop("reset_otp_email", None)
        request.session.pop("reset_otp_expiry", None)
        request.session.pop("reset_otp_attempts", None)
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Unable to send OTP email. "
                    "Please check the email configuration."
                )
            },
            status=500
        )
    return JsonResponse(
        {
            "success": True,
            "message": "OTP has been sent to your registered email address."
        }
    )

def password_reset_verify(request):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Method not allowed."},
            status=405
        )
    try:
        content_type = request.META.get("CONTENT_TYPE", "")
        if "application/json" in content_type:
            data = json.loads(request.body)
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            confirm_password = data.get("confirm_password", "")
            otp = data.get("otp", "").strip()
        else:
            email = request.POST.get("email", "").strip().lower()
            password = request.POST.get("password", "")
            confirm_password = request.POST.get("confirm_password", "")
            otp = request.POST.get("otp", "").strip()
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse(
            {"success": False, "error": "Invalid request format."},
            status=400
        )

    # Required fields
    if not email or not password or not confirm_password or not otp:
        return JsonResponse(
            {
                "success": False,
                "error": "All fields are required."
            },
            status=400
        )
    # OTP must be exactly 6 digits
    if not otp.isdigit() or len(otp) != 6:
        return JsonResponse(
            {
                "success": False,
                "error": "Please enter a valid 6-digit OTP."
            },
            status=400
        )
    # Get session values
    session_otp = request.session.get("reset_otp")
    session_email = request.session.get("reset_otp_email")
    session_expiry_str = request.session.get("reset_otp_expiry")
    attempts = request.session.get("reset_otp_attempts", 0)
    # Check OTP session
    if not session_otp or not session_email:
        return JsonResponse(
            {
                "success": False,
                "error": "OTP session expired. Please request a new OTP."
            },
            status=400
        )
    # Check email
    if session_email.lower() != email.lower():
        return JsonResponse(
            {
                "success": False,
                "error": "This OTP does not belong to this email address."
            },
            status=400
        )
    # Maximum attempts
    if attempts >= 3:
        request.session.pop("reset_otp", None)
        request.session.pop("reset_otp_email", None)
        request.session.pop("reset_otp_expiry", None)
        request.session.pop("reset_otp_attempts", None)
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "Too many failed attempts. "
                    "Please request a new OTP."
                )
            },
            status=400
        )
    # Check OTP expiry
    if session_expiry_str:
        try:
            expiry = timezone.datetime.fromisoformat(
                session_expiry_str
            )
            if timezone.now() > expiry:
                request.session.pop("reset_otp", None)
                request.session.pop("reset_otp_email", None)
                request.session.pop("reset_otp_expiry", None)
                request.session.pop("reset_otp_attempts", None)
                return JsonResponse(
                    {
                        "success": False,
                        "error": (
                            "OTP has expired. "
                            "Please request a new OTP."
                        )
                    },
                    status=400
                )
        except (ValueError, TypeError):
            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid OTP session. Please request a new OTP."
                },
                status=400
            )
    # Check OTP
    if otp != session_otp:
        attempts += 1
        request.session["reset_otp_attempts"] = attempts
        request.session.modified = True
        remaining = 3 - attempts
        if remaining <= 0:
            request.session.pop("reset_otp", None)
            request.session.pop("reset_otp_email", None)
            request.session.pop("reset_otp_expiry", None)
            request.session.pop("reset_otp_attempts", None)
            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "Too many failed attempts. "
                        "Please request a new OTP."
                    )
                },
                status=400
            )
        return JsonResponse(
            {
                "success": False,
                "error": (
                    f"Invalid OTP. "
                    f"{remaining} attempt(s) remaining."
                )
            },
            status=400
        )

    # Check password match
    if password != confirm_password:
        return JsonResponse(
            {
                "success": False,
                "error": "Passwords do not match."
            },
            status=400
        )

    # Get user
    user = User.objects.filter(
        email__iexact=email
    ).first()
    if not user:
        return JsonResponse(
            {
                "success": False,
                "error": "User account was not found."
            },
            status=404
        )
    # Set new password
    user.set_password(password)
    user.save(update_fields=["password"])
    # Clear OTP session completely
    request.session.pop("reset_otp", None)
    request.session.pop("reset_otp_email", None)
    request.session.pop("reset_otp_expiry", None)
    request.session.pop("reset_otp_attempts", None)
    request.session.modified = True
    messages.success(
        request,
        "Your password has been reset successfully. "
        "Please login with your new password."
    )
    return JsonResponse(
        {
            "success": True,
            "message": "Password reset successfully.",
            "redirect_url": reverse("login")
        }
    )


def admin_user_edit(request, id):
    if not is_admin(request):
        return redirect("admin_login")
    user = get_object_or_404(User, id=id)
    profile, created = UserProfile.objects.get_or_create(user=user)
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        
        if not username:
            messages.error(request, "Username is required.")
            return redirect("manage_users")
        
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, f"Username '{username}' is already taken.")
            return redirect("manage_users")
            
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, f"Email '{email}' is already registered.")
            return redirect("manage_users")
            
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email
        user.save()
        
        profile.phone_no = request.POST.get("phone_no", "").strip()
        profile.address = request.POST.get("address", "").strip()
        
        dob = request.POST.get("date_of_birth", "").strip()
        if dob:
            profile.date_of_birth = dob
        else:
            profile.date_of_birth = None
            
        profile.gender = request.POST.get("gender", "").strip()
        profile.city = request.POST.get("city", "").strip()
        profile.state = request.POST.get("state", "").strip()
        profile.country = request.POST.get("country", "").strip()
        profile.pincode = request.POST.get("pincode", "").strip()
        
        if "photo" in request.FILES:
            profile.photo = request.FILES["photo"]
            
        profile.save()
        messages.success(request, "User profile updated successfully.")
        
    return redirect("manage_users")


def admin_user_delete(request, id):
    if not is_admin(request):
        return redirect("admin_login")
    if request.method == "POST":
        user = get_object_or_404(User, id=id)
        if user.is_staff:
            messages.error(request, "Staff users cannot be deleted from this interface.")
        else:
            user.delete()
            messages.success(request, "User deleted successfully.")
    return redirect("manage_users")


def admin_payment_delete(request, id):
    if not is_admin(request):
        return redirect("admin_login")
    if request.method == "POST":
        payment = get_object_or_404(Payment, id=id)
        payment.delete()
        messages.success(request, "Payment deleted successfully.")
    return redirect("admin_payments")