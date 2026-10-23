import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from Travels.models import Package, Booking, UserProfile, Payment

class TravelsE2ETestCase(TestCase):
    def setUp(self):
        # Create user profile
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@gmail.com',
            password='Testpassword123!',
            first_name='Test',
            last_name='User'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            phone_no='9999999999'
        )
        
        # Create packages
        self.p1 = Package.objects.create(
            package_name='Manali Snow Adventure Package',
            destination='Manali',
            price=2500.00,
            description='Test Manali description',
            image='packages/test1.jpg',
            days=5,
            nights=4,
            hotel='3 Star Hotel',
            bus='AC Bus',
            day='Day 1: Arrival at Manali\nRelax at the hotel.\nDay 2: Solang Valley\nSightseeing and skiing.',
            included='Breakfast, Transfers',
            category='Mountain'
        )
        self.p2 = Package.objects.create(
            package_name='Kerala Paradise Holiday Package',
            destination='Kerala',
            price=800.00,
            description='Test Kerala description',
            image='packages/test2.jpg',
            days=4,
            nights=3,
            hotel='Resort',
            bus='Private Car',
            day='Day 1: Kochi arrival\nDay 2: Alleppey Houseboat',
            included='Breakfast, Cruise',
            category='Beach'
        )
        
        self.client = Client()

    def test_direct_login(self):
        # Verify direct login redirects to home page without OTP
        response = self.client.post(reverse('login'), {
            'email': 'testuser@gmail.com',
            'password': 'Testpassword123!'
        })
        self.assertEqual(response.status_code, 302)
        # Check redirect to index
        self.assertRedirects(response, reverse('index'))
        
        # Verify user is logged in
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.id)

    def test_homepage_search_redirection(self):
        # Test form submission from homepage to packages page
        response = self.client.get(reverse('packages'), {
            'destination': 'Manali',
            'category': 'Mountain',
            'budget': '1000_5000'
        })
        self.assertEqual(response.status_code, 200)
        # Check filtered package is in context
        packages = response.context['packages']
        self.assertEqual(len(packages), 1)
        self.assertEqual(packages[0].package_name, 'Manali Snow Adventure Package')

    def test_packages_sorting_and_filtering(self):
        # Filter: category=Beach
        response = self.client.get(reverse('packages'), {
            'category': 'Beach'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['packages']), 1)
        self.assertEqual(response.context['packages'][0].category, 'Beach')
        
        # Sort: price_asc
        response = self.client.get(reverse('packages'), {
            'sort': 'price_asc'
        })
        pkgs = list(response.context['packages'])
        self.assertEqual(pkgs[0].price, 800.00)
        self.assertEqual(pkgs[1].price, 2500.00)
        
        # Sort: price_desc
        response = self.client.get(reverse('packages'), {
            'sort': 'price_desc'
        })
        pkgs = list(response.context['packages'])
        self.assertEqual(pkgs[0].price, 2500.00)
        self.assertEqual(pkgs[1].price, 800.00)

    def test_itinerary_parsing(self):
        # Test detail view itinerary parser
        response = self.client.get(reverse('package_details', args=[self.p1.id]))
        self.assertEqual(response.status_code, 200)
        itinerary = response.context['itinerary_list']
        self.assertEqual(len(itinerary), 2)
        self.assertEqual(itinerary[0]['day_num'], '1')
        self.assertEqual(itinerary[0]['title'], 'Arrival at Manali')
        self.assertEqual(itinerary[0]['description'], 'Relax at the hotel.')
        self.assertEqual(itinerary[1]['day_num'], '2')
        self.assertEqual(itinerary[1]['title'], 'Solang Valley')
        self.assertEqual(itinerary[1]['description'], 'Sightseeing and skiing.')

    def test_booking_otp_flow(self):
        # Log in the user first
        self.client.login(username='testuser', password='Testpassword123!')
        
        # 1. Send OTP
        response = self.client.post(reverse('booking_send_otp'), {
            'email': 'testuser@gmail.com'
        })
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.content)
        self.assertTrue(res_data['success'])
        
        # Retrieve OTP from session
        session_otp = self.client.session.get('booking_otp')
        self.assertIsNotNone(session_otp)
        self.assertEqual(self.client.session.get('booking_otp_email'), 'testuser@gmail.com')
        
        # 2. Try verifying with wrong OTP
        response = self.client.post(reverse('booking_verify_otp'), {
            'email': 'testuser@gmail.com',
            'otp': '000000'
        })
        self.assertEqual(response.status_code, 400)
        res_data = json.loads(response.content)
        self.assertFalse(res_data['success'])
        self.assertIn('Invalid OTP', res_data['error'])
        
        # 3. Verify with correct OTP
        response = self.client.post(reverse('booking_verify_otp'), {
            'email': 'testuser@gmail.com',
            'otp': session_otp
        })
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.content)
        self.assertTrue(res_data['success'])
        
        # Verify verified session flags
        self.assertTrue(self.client.session.get('booking_otp_verified'))
        self.assertEqual(self.client.session.get('booking_otp_verified_email'), 'testuser@gmail.com')

    def test_booking_creation_protection(self):
        from datetime import date, timedelta
        valid_date_str = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')

        self.client.login(username='testuser', password='Testpassword123!')
        
        # Attempt to create booking without verified OTP
        response = self.client.post(reverse('booking', args=[self.p1.id]), {
            'persons': 2,
            'full_name': 'Test User',
            'email': 'testuser@gmail.com',
            'phone': '9999999999',
            'travel_date': valid_date_str
        })
        # Should redirect back to booking page with error message due to lack of OTP validation
        self.assertEqual(response.status_code, 302)
        # Check no Booking is created
        self.assertEqual(Booking.objects.count(), 0)
        
        # Now simulate verified OTP in session
        session = self.client.session
        session['booking_otp_verified'] = True
        session['booking_otp_verified_email'] = 'testuser@gmail.com'
        session.save()
        
        # Attempt again
        response = self.client.post(reverse('booking', args=[self.p1.id]), {
            'persons': 2,
            'full_name': 'Test User',
            'email': 'testuser@gmail.com',
            'phone': '9999999999',
            'travel_date': valid_date_str
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify Booking is created successfully
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.first()
        self.assertEqual(booking.full_name, 'Test User')
        self.assertEqual(booking.persons, 2)
        self.assertEqual(booking.amount, self.p1.price * 2 + 180)

    def test_admin_profile_page(self):
        # Setup admin session
        session = self.client.session
        session['admin'] = True
        session.save()

        # Create admin user
        admin = User.objects.create_superuser(
            username='admin01',
            email='admin@gmail.com',
            password='adminpassword'
        )

        # Access admin profile page
        response = self.client.get(reverse('admin_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "System Superuser")
        self.assertContains(response, "Logout")
        self.assertContains(response, "Admin Dashboard")

    def test_contact_messages_reply_system(self):
        from Travels.models import ContactMessage

        # 1. Guest contact message (not logged in)
        response = self.client.post(reverse('contact'), {
            'name': 'Guest Sender',
            'email': 'guest@example.com',
            'phone': '1234567890',
            'subject': 'Inquiry about Tours',
            'message': 'Hello, I have a question.'
        })
        self.assertEqual(response.status_code, 302)
        guest_msg = ContactMessage.objects.get(name='Guest Sender')
        self.assertIsNone(guest_msg.user)

        # 2. Authenticated user contact message
        self.client.login(username='testuser', password='Testpassword123!')
        response = self.client.post(reverse('contact'), {
            'name': 'Test User',
            'email': 'testuser@gmail.com',
            'phone': '9999999999',
            'subject': 'Booking Issue',
            'message': 'Hello, I have a issue with booking.'
        })
        self.assertEqual(response.status_code, 302)
        user_msg = ContactMessage.objects.get(subject='Booking Issue')
        self.assertEqual(user_msg.user, self.user)

        # 3. Admin reply to user message
        session = self.client.session
        session['admin'] = True
        session.save()

        reply_text = "Your booking issue has been resolved. Thanks!"
        response = self.client.post(reverse('admin_reply_message', args=[user_msg.id]), {
            'reply_message': reply_text
        })
        self.assertEqual(response.status_code, 302)

        # Check in DB
        user_msg.refresh_from_db()
        self.assertEqual(user_msg.status, 'Replied')
        self.assertEqual(user_msg.reply_message, reply_text)
        self.assertIsNotNone(user_msg.replied_at)

        # 4. User views dashboard (only shows replies for user's account)
        self.client.logout()
        session = self.client.session
        session.pop('admin', None)
        session.save()

        self.client.login(username='testuser', password='Testpassword123!')

        # 4a. Default dashboard view (tab=profile) should redirect to myprofile
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('dashboard_profile'))

        response = self.client.get(reverse('dashboard_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(reply_text, response.content.decode('utf-8'))

        # 4b. Messages tab view (tab=messages) SHOULD contain reply text
        response = self.client.get(reverse('dashboard_messages'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('contact_messages', response.context)
        messages_in_ctx = list(response.context['contact_messages'])
        self.assertEqual(len(messages_in_ctx), 1)
        self.assertEqual(messages_in_ctx[0].reply_message, reply_text)
        self.assertContains(response, reply_text)

        # 5. Message privacy: another user logs in and shouldn't see user_msg reply
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@gmail.com',
            password='Testpassword123!',
            first_name='Other'
        )
        self.client.logout()
        self.client.login(username='otheruser', password='Testpassword123!')
        response = self.client.get(reverse('dashboard_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(reply_text, response.content.decode('utf-8'))


class ForgotPasswordTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@gmail.com',  # note that username is set to email in registration
            email='testuser@gmail.com',
            password='Oldpassword123!',
            first_name='Test',
            last_name='User'
        )
        self.client = Client()

    def test_send_otp_success_existing_user(self):
        from django.core import mail
        mail.outbox = [] # Clear outbox
        
        response = self.client.post(reverse('password_reset_send_otp'), {
            'email': 'testuser@gmail.com',
            'password': 'Newpassword123!',
            'confirm_password': 'Newpassword123!'
        })
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.content)
        self.assertTrue(res_data['success'])
        self.assertEqual(res_data['message'], "OTP has been sent to your registered email address.")
        
        # Verify OTP saved in session
        self.assertIsNotNone(self.client.session.get('reset_otp'))
        self.assertEqual(self.client.session.get('reset_otp_email'), 'testuser@gmail.com')
        self.assertEqual(self.client.session.get('reset_otp_attempts'), 0)
        
        # Verify email is sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.client.session.get('reset_otp'), mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ['testuser@gmail.com'])

    def test_send_otp_success_non_existing_user(self):
        from django.core import mail
        mail.outbox = [] # Clear outbox
        
        response = self.client.post(reverse('password_reset_send_otp'), {
            'email': 'nonexistent@gmail.com',
            'password': 'Newpassword123!',
            'confirm_password': 'Newpassword123!'
        })
        self.assertEqual(response.status_code, 404)
        res_data = json.loads(response.content)
        self.assertFalse(res_data['success'])
        self.assertEqual(res_data['error'], "No account is registered with this email address.")
        
        # Verify email is NOT sent
        self.assertEqual(len(mail.outbox), 0)

    def test_send_otp_validation_errors(self):
        # 1. Invalid email format
        response = self.client.post(reverse('password_reset_send_otp'), {
            'email': 'invalid-email',
            'password': 'Newpassword123!',
            'confirm_password': 'Newpassword123!'
        })
        self.assertEqual(response.status_code, 400)
        res_data = json.loads(response.content)
        self.assertFalse(res_data['success'])
        self.assertIn('valid email address', res_data['error'])

        # 2. Passwords mismatch
        response = self.client.post(reverse('password_reset_send_otp'), {
            'email': 'testuser@gmail.com',
            'password': 'Newpassword123!',
            'confirm_password': 'DifferentPassword123!'
        })
        self.assertEqual(response.status_code, 400)
        res_data = json.loads(response.content)
        self.assertFalse(res_data['success'])
        self.assertEqual(res_data['error'], 'Passwords do not match.')

        # 3. Weak password (too short)
        response = self.client.post(reverse('password_reset_send_otp'), {
            'email': 'testuser@gmail.com',
            'password': '123',
            'confirm_password': '123'
        })
        self.assertEqual(response.status_code, 400)
        res_data = json.loads(response.content)
        self.assertFalse(res_data['success'])
        self.assertIn('too short', res_data['error'].lower())

    def test_verify_otp_success(self):
        # Set up active OTP in session
        session = self.client.session
        session['reset_otp'] = '123456'
        session['reset_otp_email'] = 'testuser@gmail.com'
        session['reset_otp_expiry'] = (timezone.now() + timedelta(minutes=10)).isoformat()
        session['reset_otp_attempts'] = 0
        session.save()

        response = self.client.post(reverse('password_reset_verify'), {
            'email': 'testuser@gmail.com',
            'password': 'Newpassword123!',
            'confirm_password': 'Newpassword123!',
            'otp': '123456'
        })
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.content)
        self.assertTrue(res_data['success'])
        self.assertEqual(res_data['redirect_url'], reverse('login'))

        # Verify password updated in DB
        from django.contrib.auth import authenticate
        user = authenticate(username='testuser@gmail.com', password='Newpassword123!')
        self.assertIsNotNone(user)

        # Verify session cleared
        self.assertNotIn('reset_otp', self.client.session)
        self.assertNotIn('reset_otp_email', self.client.session)

    def test_verify_otp_invalid_attempts_lockout(self):
        # Set up active OTP in session
        session = self.client.session
        session['reset_otp'] = '123456'
        session['reset_otp_email'] = 'testuser@gmail.com'
        session['reset_otp_expiry'] = (timezone.now() + timedelta(minutes=10)).isoformat()
        session['reset_otp_attempts'] = 0
        session.save()

        # Attempt 1
        response = self.client.post(reverse('password_reset_verify'), {
            'email': 'testuser@gmail.com',
            'password': 'Newpassword123!',
            'confirm_password': 'Newpassword123!',
            'otp': '999999'
        })
        self.assertEqual(response.status_code, 400)
        res_data = json.loads(response.content)
        self.assertFalse(res_data['success'])
        self.assertEqual(res_data['error'], 'Invalid OTP. 2 attempt(s) remaining.')

        # Attempt 2
        response = self.client.post(reverse('password_reset_verify'), {
            'email': 'testuser@gmail.com',
            'password': 'Newpassword123!',
            'confirm_password': 'Newpassword123!',
            'otp': '999999'
        })
        self.assertEqual(response.status_code, 400)
        res_data = json.loads(response.content)
        self.assertFalse(res_data['success'])
        self.assertEqual(res_data['error'], 'Invalid OTP. 1 attempt(s) remaining.')

        # Attempt 3 (Lockout)
        response = self.client.post(reverse('password_reset_verify'), {
            'email': 'testuser@gmail.com',
            'password': 'Newpassword123!',
            'confirm_password': 'Newpassword123!',
            'otp': '999999'
        })
        self.assertEqual(response.status_code, 400)
        res_data = json.loads(response.content)
        self.assertFalse(res_data['success'])
        self.assertIn('Too many failed attempts', res_data['error'])

        # Verify session cleared
        self.assertNotIn('reset_otp', self.client.session)

    def test_verify_otp_expired(self):
        # Set up expired OTP in session
        session = self.client.session
        session['reset_otp'] = '123456'
        session['reset_otp_email'] = 'testuser@gmail.com'
        session['reset_otp_expiry'] = (timezone.now() - timedelta(minutes=1)).isoformat()
        session['reset_otp_attempts'] = 0
        session.save()

        response = self.client.post(reverse('password_reset_verify'), {
            'email': 'testuser@gmail.com',
            'password': 'Newpassword123!',
            'confirm_password': 'Newpassword123!',
            'otp': '123456'
        })
        self.assertEqual(response.status_code, 400)
        res_data = json.loads(response.content)
        self.assertFalse(res_data['success'])
        self.assertIn('expired', res_data['error'].lower())

        # Verify session cleared
        self.assertNotIn('reset_otp', self.client.session)


class AdminManageUsersAndPaymentsTestCase(TestCase):
    def setUp(self):
        # Create non-staff user
        self.user = User.objects.create_user(
            username='traveler1',
            email='traveler1@gmail.com',
            password='Password123!',
            first_name='Traveler',
            last_name='One'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            phone_no='1234567890',
            address='123 Dreamland St',
            city='Dream City',
            state='Dream State',
            country='Dream Country',
            pincode='123456'
        )
        
        # Create package
        self.package = Package.objects.create(
            package_name='Mountain Adventure',
            destination='Himalayas',
            price=1500.00,
            description='Test adventure',
            image='packages/test.jpg',
            days=3,
            nights=2,
            hotel='Camp',
            bus='Volvo',
            day='Day 1: Trek',
            included='Meals',
            category='Mountain'
        )
        
        # Create booking
        self.booking = Booking.objects.create(
            user=self.user,
            package=self.package,
            full_name='Traveler One',
            email='traveler1@gmail.com',
            phone='1234567890',
            persons=2,
            amount=3000.00,
            status='Paid',
            travel_date=timezone.now().date()
        )
        
        # Create payment
        self.payment = Payment.objects.create(
            booking=self.booking,
            transaction_id='TXN_TEST123',
            amount=3000.00,
            payment_method='Razorpay',
            status='Successful'
        )
        
        self.client = Client()

    def test_unauthorized_access(self):
        # Verify that without admin session, actions redirect to admin_login
        # Edit user
        response = self.client.post(reverse('admin_user_edit', args=[self.user.id]), {
            'first_name': 'NewName'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('admin_login'))
        
        # Delete user
        response = self.client.post(reverse('admin_user_delete', args=[self.user.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('admin_login'))
        
        # Delete payment
        response = self.client.post(reverse('admin_payment_delete', args=[self.payment.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('admin_login'))

    def test_admin_user_edit_success(self):
        # Set admin in session
        session = self.client.session
        session['admin'] = True
        session.save()
        
        # Perform user edit POST
        response = self.client.post(reverse('admin_user_edit', args=[self.user.id]), {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
            'username': 'traveler_updated',
            'email': 'updated@gmail.com',
            'phone_no': '9876543210',
            'address': '456 New St',
            'date_of_birth': '1995-05-15',
            'gender': 'Male',
            'city': 'New City',
            'state': 'New State',
            'country': 'New Country',
            'pincode': '654321'
        })
        
        # Verify redirection to manage_users
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('manage_users'))
        
        # Verify DB is updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'UpdatedFirst')
        self.assertEqual(self.user.last_name, 'UpdatedLast')
        self.assertEqual(self.user.username, 'traveler_updated')
        self.assertEqual(self.user.email, 'updated@gmail.com')
        
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.phone_no, '9876543210')
        self.assertEqual(profile.address, '456 New St')
        self.assertEqual(profile.date_of_birth.strftime('%Y-%m-%d'), '1995-05-15')
        self.assertEqual(profile.gender, 'Male')
        self.assertEqual(profile.city, 'New City')
        self.assertEqual(profile.state, 'New State')
        self.assertEqual(profile.country, 'New Country')
        self.assertEqual(profile.pincode, '654321')

    def test_admin_user_delete_success(self):
        # Set admin in session
        session = self.client.session
        session['admin'] = True
        session.save()
        
        # Perform user delete POST
        response = self.client.post(reverse('admin_user_delete', args=[self.user.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('manage_users'))
        
        # Verify user is deleted
        self.assertFalse(User.objects.filter(id=self.user.id).exists())
        # Verify cascade deletes booking and profile
        self.assertFalse(UserProfile.objects.filter(id=self.profile.id).exists())
        self.assertFalse(Booking.objects.filter(id=self.booking.id).exists())

    def test_admin_payment_delete_success(self):
        # Set admin in session
        session = self.client.session
        session['admin'] = True
        session.save()
        
        # Perform payment delete POST
        response = self.client.post(reverse('admin_payment_delete', args=[self.payment.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('admin_payments'))
        
        # Verify payment is deleted
        self.assertFalse(Payment.objects.filter(id=self.payment.id).exists())
        # Verify booking is NOT deleted (payment deletion safety)
        self.assertTrue(Booking.objects.filter(id=self.booking.id).exists())
