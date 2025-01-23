# routes.py
import logging

from flask import render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, login_user, logout_user, current_user
from ehr_system.models import (db, UserDoctor, DoctorEmergencyContact, Patient, PatientEmergencyContact, PatientVital,
                               PatientMedicalHistory, PatientMedication, PatientLaboratory, PatientBilling,
                               PatientRadiology, ContactMessage)
from datetime import datetime, timedelta
import random
import string
from flask_mail import Message
from ehr_system import mail, allowed_file
import os
from werkzeug.utils import secure_filename
import uuid

# Dictionary to track login attempts (Global variable)
login_attempts = {}


def parse_datetime(datetime_str):
    try:
        # Parse the datetime string in the 'YYYY-MM-DDTHH:MM' format
        return datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M') if datetime_str else None
    except ValueError as e:
        print(f"Error parsing datetime: {e}")  # Debugging
        return None


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    except ValueError:
        return None


def send_email_to_support(name, email, subject, message):
    try:
        support_email = current_app.config['MAIL_USERNAME']  # Support email from config

        # Send email to the support team
        support_msg = Message(
            subject=f"Support Request: {subject}",
            sender=f"{name} <{email}>",  # User's email
            recipients=[support_email],  # Your support email
            body=f"Message from {name} ({email}):\n\n{message}"
        )
        mail.send(support_msg)

        # Send confirmation email to the user
        user_msg = Message(
            subject="Your Support Request Has Been Received",
            sender=support_email,  # Support email as the sender
            recipients=[email],  # Send confirmation to the user
            body=f"Dear {name},\n\n"
                 f"Thank you for contacting us. Your message has been received, and our support team will get back to you as soon as possible.\n\n"
                 f"Best regards,\nFloris Support Team"
        )
        mail.send(user_msg)

    except Exception as e:
        current_app.logger.error(f"Failed to send support or confirmation email: {e}")
        raise e


def register_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/contact_us')
    def contact_us():
        return render_template('contact.html')

    @app.route('/about_us')
    def about_us():
        return render_template('about.html')

    @app.route('/contact_support_public', methods=['POST'])
    def contact_support_public():
        try:
            # Handle form data for non-logged-in users
            name = request.form.get('name')
            email = request.form.get('email')
            subject = request.form.get('subject')
            message = request.form.get('message')

            # Store message in the database
            contact_message = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            db.session.add(contact_message)
            db.session.commit()

            # Send email to support
            send_email_to_support(name, email, subject, message)

            flash('Your message has been sent successfully!', 'success')

            # Redirect to the contact form section
            return redirect(url_for('contact_us') + '#contactForm')

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'danger')
            return redirect(url_for('contact_us') + '#contactForm')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            # Debugging step
            logging.debug(f"Form Data: {request.form}")

            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            # Check if username exists
            existing_user_by_username = UserDoctor.query.filter_by(username=username).first()
            # Check if email exists
            existing_user_by_email = UserDoctor.query.filter_by(email=email).first()

            if existing_user_by_username and existing_user_by_email:
                flash('Both username and email are already in use. Please use a different username and email.',
                      'danger')
                return redirect(url_for('register') + '?modal=register')

            elif existing_user_by_username:
                flash('Username already exists. Please choose a different username.', 'danger')
                return redirect(url_for('register') + '?modal=register')

            elif existing_user_by_email:
                flash('Email already exists. Please use a different email.', 'danger')
                return redirect(url_for('register') + '?modal=register')

            # If username and email are unique, register the user
            hashed_password = generate_password_hash(password)
            new_user_doctor = UserDoctor(username=username, email=email, password=hashed_password)

            try:
                db.session.add(new_user_doctor)
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login') + '?modal=login&flash=success')
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred during registration: {e}", 'danger')
                return redirect(url_for('register') + '?modal=register')

        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            # Check if user_check is locked out
            if username in login_attempts:
                attempt_data = login_attempts[username]
                if attempt_data['locked'] and datetime.now() < attempt_data['lockout_time']:
                    remaining_time = (attempt_data['lockout_time'] - datetime.now()).seconds
                    flash(f'Account locked. Try again in {remaining_time // 60} minutes.', 'danger')
                    return redirect(url_for('login'))
                elif attempt_data['locked']:
                    # Reset lockout after time expires
                    login_attempts[username] = {'attempts': 0, 'locked': False, 'lockout_time': None}

            # Verify the user_check's credentials using SQLAlchemy
            user_check = UserDoctor.query.filter_by(username=username).first()

            if user_check and check_password_hash(user_check.password, password):
                login_user(user_check)
                flash('Login successful!, Please Update your information in the account section', 'doctor_dashboard')
                if username in login_attempts:
                    del login_attempts[username]  # Reset attempts on successful login
                return redirect(url_for('doctor_dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
                # Update login attempts
                if username not in login_attempts:
                    login_attempts[username] = {'attempts': 1, 'locked': False, 'lockout_time': None}
                else:
                    login_attempts[username]['attempts'] += 1

                # Lock account after 3 failed attempts
                if login_attempts[username]['attempts'] >= 3:
                    login_attempts[username]['locked'] = True
                    login_attempts[username]['lockout_time'] = datetime.now() + timedelta(minutes=10)
                    flash('Too many failed attempts. Your account has been locked for 10 minutes.', 'danger')

                return redirect(url_for('login') + '?modal=login')
        return render_template('index.html')

    @app.route('/forgot_password', methods=['GET', 'POST'])
    def forgot_password():
        show_modal = request.args.get('show_modal')  # Get show_modal from URL
        if request.method == 'POST':
            email = request.form.get('email')
            if not email:
                flash('Please provide a valid email address.', 'danger')
                show_modal = 'email'  # Show the email modal on error
            else:
                user = UserDoctor.query.filter_by(email=email).first()
                if user:
                    otp = ''.join(random.choices(string.digits, k=6))
                    session['otp'] = otp
                    session['email'] = email
                    msg = Message('Password Reset OTP', sender=app.config['MAIL_USERNAME'], recipients=[email])
                    msg.body = f"Your OTP for resetting your password is: {otp}"
                    mail.send(msg)
                    flash('An OTP has been sent to your email address.', 'info')
                    return redirect(url_for('forgot_password', show_modal='otp'))  # Redirect to OTP modal
                else:
                    flash('Email not found.', 'danger')
                    show_modal = 'email'
        return render_template('forgot_password.html', show_modal=show_modal)

    @app.route('/verify_otp', methods=['POST'])
    def verify_otp():
        entered_otp = request.form.get('otp')

        if entered_otp == session.get('otp'):
            flash('OTP verified successfully. Please set a new password.', 'info')
            return render_template('forgot_password.html', show_modal='reset')  # Redirect to reset password modal
        else:
            flash('Invalid OTP. Please try again.', 'danger')
            return redirect(url_for('forgot_password', show_modal='otp'))  # Redirect to OTP modal

    @app.route('/reset_password', methods=['POST'])
    def reset_password():
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('forgot_password', show_modal='reset'))

        email = session.get('email')
        if not email:
            flash('Session expired. Please try again.', 'danger')
            return redirect(url_for('forgot_password'))

        # Update the password in the database using SQLAlchemy
        user = UserDoctor.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()

        # Clear the session and redirect to log in
        session.pop('otp', None)
        session.pop('email', None)
        flash('Your password has been reset. Please log in.', 'success')
        return redirect(url_for('login') + '?modal=login')

    @app.route('/forgot_username', methods=['GET', 'POST'])
    def forgot_username():
        if request.method == 'POST':
            email = request.form.get('username_email')  # Get email from the form

            if not email:
                flash('Please provide a valid email address.', 'danger')
                return redirect(url_for('forgot_username', modal='username'))  # Reload modal with error

            # Check if the user_verify exists in the database using SQLAlchemy
            user = UserDoctor.query.filter_by(email=email).first()

            if user:
                # Send the username to the provided email
                msg = Message('Your Username', sender=app.config['MAIL_USERNAME'], recipients=[email])
                msg.body = f"Hello, {user.username}. Your username associated with this email is: {user.username}"
                mail.send(msg)

                flash('Your username has been sent to your email address.', 'info')
                return redirect(
                    url_for('login') + '?modal=login')  # Redirect to log in after successful username recovery

            else:
                flash('Email not found. Please check and try again.', 'danger')
                return redirect(url_for('forgot_username', modal='username'))  # Reload modal with error

        # Default modal when page is loaded
        modal = request.args.get('modal', 'username')
        return render_template('forgot_password.html', show_modal=modal)

    @app.route('/doctor_dashboard')
    @login_required
    def doctor_dashboard():
        user = UserDoctor.query.get_or_404(current_user.id)  # Get the current user's data
        return render_template('doctor_dashboard.html', user=user)

    @app.route('/contact_support_logged_in', methods=['POST'])
    @login_required
    def contact_support_logged_in():
        try:
            # Get form data
            name = request.form.get('name')
            email = request.form.get('email')
            subject = request.form.get('subject')
            message = request.form.get('message')
            current_page = request.form.get('current_page') or url_for('doctor_dashboard')

            # Store the message in the database
            contact_message = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message,
                user_id=current_user.id
            )
            db.session.add(contact_message)
            db.session.commit()

            # Send the email
            send_email_to_support(name, email, subject, message)

            flash('Your message has been sent successfully!', 'contact_support_logged_in')
            return redirect(current_page)

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'contact_support_logged_in')
            return redirect(request.form.get('current_page') or url_for('doctor_dashboard'))

    @app.route('/account')
    @login_required
    def account():
        user = UserDoctor.query.get_or_404(current_user.id)
        doc_emergency_contact = user.doc_emergency_contact
        return render_template('account.html', user=user, doc_emergency_contact=doc_emergency_contact)
    # route for account management for the doctor

    @app.route('/account/profile_picture', methods=['GET', 'POST'])
    @login_required
    def profile_picture():
        user = UserDoctor.query.get_or_404(current_user.id)
        doc_emergency_contact = user.doc_emergency_contact

        if request.method == 'POST':

            # Update title and name
            user.title = request.form.get('title', user.title)
            user.name = request.form.get('name', user.name)

            # Handle profile picture removal
            if request.form.get('remove_picture') == 'yes':
                try:
                    # Remove the profile picture file from the server
                    if user.profile_picture:
                        picture_path = os.path.join(app.config['PROFILE_PICTURE_FOLDER'], user.profile_picture)
                        if os.path.exists(picture_path):
                            os.remove(picture_path)

                    # Clear the profile picture from the user object
                    user.profile_picture = None
                    db.session.commit()
                    flash("Profile picture removed successfully!", "profile_picture")
                except Exception as e:
                    flash(f"An error occurred while removing the profile picture: {str(e)}", "profile_picture")
                    db.session.rollback()

            # Handle profile picture upload
            elif 'profile_picture' in request.files and request.files['profile_picture'].filename != '':
                profile_picture_file = request.files['profile_picture']

                # Check if the file has a valid extension
                if allowed_file(profile_picture_file.filename, app.config['ALLOWED_IMAGE_EXTENSIONS']):
                    picture_filename = secure_filename(profile_picture_file.filename)
                    picture_name = f"{uuid.uuid4()}_{picture_filename}"  # Generate a unique filename using UUID
                    save_path = os.path.join(app.config['PROFILE_PICTURE_FOLDER'], picture_name)

                    try:
                        # Save the file to the specified folder
                        profile_picture_file.save(save_path)

                        # Update the user's profile picture in the database
                        user.profile_picture = picture_name
                        db.session.commit()

                        flash("Profile picture updated successfully!", 'profile_picture')
                    except Exception as e:
                        flash(f"An error occurred while saving the profile picture: {str(e)}", 'profile_picture')
                        db.session.rollback()

            else:
                try:
                    # Commit other changes if no profile picture is uploaded or removed
                    db.session.commit()
                    flash("Profile updated successfully!", 'profile_picture')
                except Exception as e:
                    flash(f"An error occurred: {str(e)}", 'profile_picture')
                    db.session.rollback()

            return redirect(url_for('profile_picture'))

        return render_template('account.html', user=user, doc_emergency_contact=doc_emergency_contact)

    @app.route('/account/personal_contact_information', methods=['GET', 'POST'])
    @login_required
    def personal_contact_information():
        user = UserDoctor.query.get_or_404(current_user.id)  # Fetch the current user

        # Check if emergency contact exists for the user, if not, create a new one
        doc_emergency_contact = user.doc_emergency_contact
        if not doc_emergency_contact:
            doc_emergency_contact = DoctorEmergencyContact()
            user.doc_emergency_contact = doc_emergency_contact  # Associate emergency contact with the user
            db.session.add(doc_emergency_contact)
            db.session.commit()

        if request.method == 'POST':
            # Update personal information
            user.first_name = request.form.get('first_name', user.first_name)
            user.middle_name = request.form.get('middle_name', user.middle_name)
            user.last_name = request.form.get('last_name', user.last_name)
            user.gender = request.form.get('gender', user.gender)

            dob_str = request.form.get('dob')
            user.dob = parse_date(dob_str)
            if dob_str and not user.dob:
                flash('Invalid date format for Date of Birth. Please use YYYY-MM-DD.', 'personal_contact_information')
                return render_template('account.html', user=user, doc_emergency_contact=doc_emergency_contact)

            user.telecom1 = request.form.get('telecom1', user.telecom1)
            user.telecom2 = request.form.get('telecom2', user.telecom2)
            user.current_home_address = request.form.get('current_home_address', user.current_home_address)
            user.permanent_home_address = request.form.get('permanent_home_address', user.permanent_home_address)

            # Update emergency contact
            doc_emergency_contact.first_name = request.form.get('emergency_contact_first_name',
                                                                doc_emergency_contact.first_name)
            doc_emergency_contact.middle_name = request.form.get('emergency_contact_middle_name',
                                                                 doc_emergency_contact.middle_name)
            doc_emergency_contact.last_name = request.form.get('emergency_contact_last_name',
                                                               doc_emergency_contact.last_name)
            doc_emergency_contact.relation = request.form.get('emergency_contact_relation',
                                                              doc_emergency_contact.relation)
            doc_emergency_contact.gender = request.form.get('emergency_contact_gender', doc_emergency_contact.gender)

            emergency_dob_str = request.form.get('emergency_contact_dob')
            doc_emergency_contact.dob = parse_date(emergency_dob_str)
            if emergency_dob_str and not doc_emergency_contact.dob:
                flash('Invalid date format for Emergency Contact Date of Birth. Please use YYYY-MM-DD.',
                      'personal_contact_information')
                return render_template('account.html', user=user, doc_emergency_contact=doc_emergency_contact)

            doc_emergency_contact.email = request.form.get('emergency_contact_email', doc_emergency_contact.email)
            doc_emergency_contact.telecom = request.form.get('emergency_contact_telecom', doc_emergency_contact.telecom)
            doc_emergency_contact.address = request.form.get('emergency_contact_address', doc_emergency_contact.address)
            doc_emergency_contact.validity_of_contact = request.form.get('emergency_contact_validity_of_contact',
                                                                         doc_emergency_contact.validity_of_contact)

            try:
                db.session.commit()
                flash('Your personal and emergency contact information has been updated successfully.',
                      'personal_contact_information')
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred while updating your information: {str(e)}', 'personal_contact_information')

            return redirect(url_for('personal_contact_information') + '#personal_contact_info')

        return render_template('account.html', user=user, doc_emergency_contact=doc_emergency_contact)

    @app.route('/account/professional_information', methods=['GET', 'POST'])
    @login_required
    def professional_information():
        user = UserDoctor.query.get_or_404(current_user.id)  # Fetch the current user
        doc_emergency_contact = user.doc_emergency_contact

        if request.method == 'POST':
            # Update professional information
            user.license_number = request.form.get('license_number', user.license_number)
            user.department = request.form.get('department', user.department)
            user.specialization = request.form.get('specialization', user.specialization)

            try:
                db.session.commit()  # Save the changes
                flash('Your professional information has been updated successfully.',
                      'professional_information')

            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred while updating your professional information: {str(e)}',
                      'professional_information')

            return redirect(url_for('professional_information')
                            + '#professional_information')  # Redirect back to the same page

        # Render the professional information section
        return render_template('account.html', user=user, doc_emergency_contact=doc_emergency_contact)

    @app.route('/account/password_management', methods=['POST'])
    @login_required
    def password_management():
        user = UserDoctor.query.get_or_404(current_user.id)
        # Fetch the current user

        # Get the form inputs
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        # Verify current password
        if not check_password_hash(user.password, current_password):
            flash('Current password is incorrect.', 'password_management')
            return redirect(url_for('account') + '#security')

        # Update password
        user.password = generate_password_hash(new_password)

        try:
            db.session.commit()
            flash('Your password has been updated successfully.', 'password_management')

            # Log the user out after password change and force them to log in with the new password
            logout_user()
            login_user(user)  # Re-login the user with updated credentials

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating your password: {str(e)}', 'password_management')

        return redirect(url_for('account') + '#security')

    @app.route('/account/delete', methods=['POST'])
    @login_required
    def delete_account():
        user = UserDoctor.query.get(current_user.id)
        if user:
            try:
                db.session.delete(user)
                db.session.commit()
                logout_user()  # Logs out the user after deletion
                flash('Your account has been deleted successfully.', 'delete_account')
                return redirect(url_for('index'))  # Redirect to the home page
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred while deleting your account: {str(e)}', 'delete_account')
        else:
            flash('User not found.', 'delete_account')
        return redirect(url_for('account'))

    @app.route('/patients_dashboard', methods=['GET', 'POST'])
    @login_required
    def patients_dashboard():
        user = UserDoctor.query.get_or_404(current_user.id)
        # Get query parameters
        page = request.args.get('page', 1, type=int)  # Current page
        entries_per_page = request.args.get('entries', 10, type=int)  # Entries per page
        search_term = request.args.get('search', '', type=str).strip()  # Search term

        # Base query: Patients added by the current doctor
        query = Patient.query.filter_by(doctor_id=current_user.id)

        # Apply search filter
        if search_term:
            query = query.filter(
                db.or_(
                    Patient.first_name.ilike(f"%{search_term}%"),
                    Patient.middle_name.ilike(f"%{search_term}%"),
                    Patient.last_name.ilike(f"%{search_term}%"),
                    Patient.patient_id.ilike(f"%{search_term}%"),
                )
            )

        # Paginate the results
        patients = query.paginate(page=page, per_page=entries_per_page, error_out=False)

        # Generate URLs for pagination
        next_url = url_for('patients_dashboard', page=patients.next_num, entries=entries_per_page,
                           search=search_term) if patients.has_next else None
        prev_url = url_for('patients_dashboard', page=patients.prev_num, entries=entries_per_page,
                           search=search_term) if patients.has_prev else None

        return render_template(
            'patients_dashboard.html',
            user=user,
            patients=patients.items,  # List of patients for the current page
            pagination=patients,  # Pass the pagination object
            next_url=next_url,
            prev_url=prev_url,
            entries_per_page=entries_per_page,
            search_term=search_term,
        )

    @app.route('/patient/add_or_edit', methods=['GET', 'POST'])
    @app.route('/patient/add_or_edit/<int:patient_id>', methods=['GET', 'POST'])
    @login_required
    def add_or_edit_patient(patient_id=None):
        user = UserDoctor.query.get_or_404(current_user.id)
        patient = Patient.query.get(patient_id) if patient_id else None
        emergency_contact = patient.pat_emergency_contact if patient else None

        # Check if patient exists
        if patient_id and not patient:
            flash('Patient not found.', 'add_or_edit_patient')
            return redirect(url_for('patients_dashboard'))

        if request.method == 'POST':
            try:
                new_patient = None

                # Gather patient data
                language_preferred = request.form.get('language_preferred')
                first_name = request.form.get('first_name')
                middle_name = request.form.get('middle_name')
                last_name = request.form.get('last_name')
                gender = request.form.get('gender')
                marital_status = request.form.get('marital_status')
                age = request.form.get('age')
                birth_date = parse_date(request.form.get('birth_date'))
                is_multiple_birth = request.form.get('is_multiple_birth') == 'yes'
                birth_no = request.form.get('birth_no')
                is_deceased = request.form.get('is_deceased') == 'true'
                date_deceased = parse_date(request.form.get('date_deceased'))
                reason_deceased = request.form.get('reason_deceased')
                phone_number = request.form.get('phone_number')
                email = request.form.get('email')
                address = request.form.get('address')

                # Gather emergency contact data
                emergency_language_preferred = request.form.get('emergency_language_preferred')
                emergency_first_name = request.form.get('emergency_first_name')
                emergency_middle_name = request.form.get('emergency_middle_name')
                emergency_last_name = request.form.get('emergency_last_name')
                emergency_gender = request.form.get('emergency_gender')
                emergency_age = request.form.get('emergency_age')
                emergency_birth_date = parse_date(request.form.get('emergency_birth_date'))
                emergency_relation = request.form.get('emergency_relation')
                emergency_phone_number = request.form.get('emergency_phone_number')
                emergency_email = request.form.get('emergency_email')
                emergency_address = request.form.get('emergency_address')
                emergency_validity_of_contact = request.form.get('validityContact')

                # Handle profile picture
                photo_filename = None
                if 'photo' in request.files:
                    photo = request.files['photo']
                    if photo and allowed_file(photo.filename, app.config['ALLOWED_IMAGE_EXTENSIONS']):
                        # Delete old photo
                        if patient and patient.photo:
                            old_photo_path = os.path.join(app.config['PROFILE_PICTURE_FOLDER'], patient.photo)
                            try:
                                if os.path.exists(old_photo_path):
                                    os.remove(old_photo_path)
                            except Exception as e:
                                flash(f"Error removing old profile picture: {e}", 'add_or_edit_patient')

                        # Save new photo
                        photo_filename = f"{uuid.uuid4()}_{secure_filename(photo.filename)}"
                        photo_path = os.path.join(app.config['PROFILE_PICTURE_FOLDER'], photo_filename)
                        photo.save(photo_path)

                if patient:
                    # Update existing patient
                    patient.language_preferred = language_preferred
                    patient.first_name = first_name
                    patient.middle_name = middle_name
                    patient.last_name = last_name
                    patient.gender = gender
                    patient.marital_status = marital_status
                    patient.age = age
                    patient.birth_date = birth_date
                    patient.is_multiple_birth = is_multiple_birth
                    patient.birth_no = birth_no
                    patient.is_deceased = is_deceased
                    patient.date_deceased = date_deceased
                    patient.reason_deceased = reason_deceased
                    patient.phone_number = phone_number
                    patient.email = email
                    patient.address = address
                    if photo_filename:
                        patient.photo = photo_filename
                    db.session.commit()

                    # Update or create emergency contact
                    if emergency_contact:
                        emergency_contact.language_preferred = emergency_language_preferred
                        emergency_contact.first_name = emergency_first_name
                        emergency_contact.middle_name = emergency_middle_name
                        emergency_contact.last_name = emergency_last_name
                        emergency_contact.gender = emergency_gender
                        emergency_contact.age = emergency_age
                        emergency_contact.birth_date = emergency_birth_date
                        emergency_contact.relation = emergency_relation
                        emergency_contact.phone_number = emergency_phone_number
                        emergency_contact.email = emergency_email
                        emergency_contact.address = emergency_address
                        emergency_contact.validity_of_contact = emergency_validity_of_contact
                    else:
                        new_emergency_contact = PatientEmergencyContact(
                            patient_id=patient.id,
                            language_preferred=emergency_language_preferred,
                            first_name=emergency_first_name,
                            middle_name=emergency_middle_name,
                            last_name=emergency_last_name,
                            gender=emergency_gender,
                            age=emergency_age,
                            birth_date=emergency_birth_date,
                            relation=emergency_relation,
                            phone_number=emergency_phone_number,
                            email=emergency_email,
                            address=emergency_address,
                            validity_of_contact=emergency_validity_of_contact
                        )
                        db.session.add(new_emergency_contact)
                    flash('Patient and emergency contact updated successfully!', 'add_or_edit_patient')
                else:
                    # Add new patient
                    new_patient = Patient(
                        language_preferred=language_preferred,
                        first_name=first_name,
                        middle_name=middle_name,
                        last_name=last_name,
                        gender=gender,
                        marital_status=marital_status,
                        age=age,
                        birth_date=birth_date,
                        is_multiple_birth=is_multiple_birth,
                        birth_no=birth_no,
                        is_deceased=is_deceased,
                        date_deceased=date_deceased,
                        reason_deceased=reason_deceased,
                        phone_number=phone_number,
                        email=email,
                        address=address,
                        doctor_id=current_user.id,
                        photo=photo_filename
                    )
                    db.session.add(new_patient)
                    db.session.commit()

                    # Add emergency contact
                    new_emergency_contact = PatientEmergencyContact(
                        patient_id=new_patient.id,
                        language_preferred=emergency_language_preferred,
                        first_name=emergency_first_name,
                        middle_name=emergency_middle_name,
                        last_name=emergency_last_name,
                        gender=emergency_gender,
                        age=emergency_age,
                        birth_date=emergency_birth_date,
                        relation=emergency_relation,
                        phone_number=emergency_phone_number,
                        email=emergency_email,
                        address=emergency_address,
                        validity_of_contact=emergency_validity_of_contact
                    )
                    db.session.add(new_emergency_contact)
                    flash('Patient and emergency contact added successfully!', 'add_or_edit_patient')

                db.session.commit()
                return redirect(url_for('add_or_edit_patient', patient_id=patient.id if patient else new_patient.id))
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred: {e}', 'add_or_edit_patient')

        # Render the template for add or edit
        return render_template('add_patient.html', patient=patient, user=user, emergency_contact=emergency_contact)

    @app.route('/clinical/<int:patient_id>', methods=['GET', 'POST'])
    @login_required
    def clinical(patient_id):
        user = UserDoctor.query.get_or_404(current_user.id)
        # Fetch the patient
        patient = Patient.query.get_or_404(patient_id)

        active_tab = request.args.get('active_tab', 'vitals')  # Default to 'vitals'

        # Render
        return render_template('patient_clinical.html', user=user, patient=patient,
                               radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
                               rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
                               medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
                               vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
                               vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
                               medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
                               medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
                               laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
                               labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
                               billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
                               billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
                               medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
                               active_tab=active_tab
                               )

    @app.route('/patient/<int:patient_id>/vitals', methods=['GET', 'POST'])
    @login_required
    def patient_vitals(patient_id):
        user = UserDoctor.query.get_or_404(current_user.id)
        # Ensure the current user has access to the patient
        patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()

        if request.method == 'POST':
            try:
                # Update fields with data from the form, handling empty inputs
                vital_record_id = request.form.get('vital_record_id')
                weight = request.form.get('weight')
                blood_pressure = request.form.get('bloodPressure')
                temperature = request.form.get('temperature')
                heart_rate = request.form.get('heartRate')
                respiratory_rate = request.form.get('respiratoryRate')
                oxygen_saturation = request.form.get('oxygenSaturation')
                blood_glucose = request.form.get('bloodGlucose')
                pulse_oximetry = request.form.get('pulseOximetry')
                measurement_date = parse_datetime(request.form.get('measurementDate'))
                vital_status = request.form.get('vitalStatus') or 'Unknown'
                vital_notes = request.form.get('vitalsNotes') or ''

                if vital_record_id:  # Update an existing record
                    vit_record = PatientVital.query.get(vital_record_id)
                    if vit_record:
                        vit_record.weight = weight
                        vit_record.blood_pressure = blood_pressure
                        vit_record.temperature = temperature
                        vit_record.heart_rate = heart_rate
                        vit_record.respiratory_rate = respiratory_rate
                        vit_record.oxygen_saturation = oxygen_saturation
                        vit_record.blood_glucose = blood_glucose
                        vit_record.pulse_oximetry = pulse_oximetry
                        vit_record.measurement_date = measurement_date
                        vit_record.vital_status = vital_status
                        vit_record.vital_notes = vital_notes
                        flash('Vitals record updated successfully!', 'patient_vitals')
                    else:
                        flash('Vitals record not found.', 'patient_vitals')
                else:  # Create a new record
                    vit_record = PatientVital(
                        patient_id=patient.id,
                        weight=weight,
                        blood_pressure=blood_pressure,
                        temperature=temperature,
                        heart_rate=heart_rate,
                        respiratory_rate=respiratory_rate,
                        oxygen_saturation=oxygen_saturation,
                        blood_glucose=blood_glucose,
                        pulse_oximetry=pulse_oximetry,
                        measurement_date=measurement_date,
                        vital_status=vital_status,
                        vital_notes=vital_notes,
                    )
                    db.session.add(vit_record)
                    flash('Vitals record saved successfully!', 'patient_vitals')

                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving vitals record: {e}', 'patient_vitals')
            return redirect(url_for('patient_vitals', patient_id=patient.id, active_tab='vitals')
                            + "#vital-record-table")

        # GET request: fetch vital records
        vital_records = PatientVital.query.filter_by(patient_id=patient.id).all()

        # Prefill a specific record if requested
        vit_record = None
        vital_record_id = request.args.get('vital_record_id')
        if vital_record_id:
            vit_record = PatientVital.query.get(vital_record_id)

        return render_template(
            'patient_clinical.html',
            user=user,
            patient=patient,
            vital_records=vital_records,
            vit_record=vit_record,
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            active_tab='vitals'
            )

    @app.route('/view-vitals-record/<int:vital_record_id>', methods=['GET', 'POST'])
    @login_required
    def view_vitals_record(vital_record_id):
        # Query the vitals record
        rec_vit = PatientVital.query.get_or_404(vital_record_id)
        patient = Patient.query.filter_by(id=rec_vit.patient_id, doctor_id=current_user.id).first_or_404()
        vit_record = PatientVital.query.get(vital_record_id)
        # fetch the patient associated with the record and ensure ownership

        active_tab = request.args.get('active_tab', 'vitals')

        return render_template(
            'patient_clinical.html',
            user=UserDoctor.query.get_or_404(current_user.id),
            patient=patient,
            rec_vit=rec_vit,
            patient_id=rec_vit.patient_id,
            vit_record=vit_record,
            vital_records=PatientVital.query.filter_by(patient_id=rec_vit.patient_id).all(),
            active_tab=active_tab,
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all()
        )

    @app.route('/delete-vitals-record/<int:vital_record_id>', methods=['GET', 'POST'])
    @login_required
    def delete_vitals_record(vital_record_id):
        rec_vit = PatientVital.query.get_or_404(vital_record_id)
        active_tab = request.args.get('active_tab', 'vitals')

        db.session.delete(rec_vit)
        db.session.commit()
        flash('Vital record deleted successfully.', 'delete_vitals_record')
        return redirect(url_for('patient_vitals',  patient_id=rec_vit.patient_id, active_tab=active_tab)
                        + "#vital-record-table")

    @app.route('/vital-records-table', methods=['GET', 'POST'])
    @login_required
    def vital_records_table():
        user = UserDoctor.query.get_or_404(current_user.id)

        # Get query parameters
        vital_page = request.args.get('vital_page', 1, type=int)  # Current page
        vital_entries_per_page = request.args.get('vital_entries', 10, type=int)  # Entries per page
        vital_search_term = request.args.get('vital_search', '', type=str).strip()  # Search term
        active_tab = request.args.get('active_tab', 'vitals')  # Current tab (optional)
        patient_id = request.args.get('patient_id', type=int)  # Get the patient ID from query parameters

        # Fetch the patient
        patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()

        # Start building the query for vital records
        vital_query = PatientVital.query.join(Patient).filter(Patient.doctor_id == current_user.id)

        # Apply search filter if there's a search term
        if vital_search_term:
            try:
                vital_query = vital_query.filter(
                    db.or_(
                        db.cast(PatientVital.vital_updated_at, db.String).ilike(f"%{vital_search_term}%"),
                        db.cast(PatientVital.measurement_date, db.String).ilike(f"%{vital_search_term}%")
                    )
                )
                if vital_query.count() == 0:
                    flash("No records found for the given date.", "vital_records_table")
                    return redirect(url_for('vital_records_table', patient_id=patient_id,
                                            vital_entries=vital_entries_per_page) + "#vital-record-table")
            except ValueError:
                flash("Invalid date format. Please use 'YYYY-MM-DD'.", "vital_records_table")
                return redirect(url_for('vital_records_table', patient_id=patient_id,
                                        vital_entries=vital_entries_per_page) + "#vital-record-table")

        # Paginate the results
        vital_records = vital_query.paginate(page=vital_page, per_page=vital_entries_per_page, error_out=False)

        # Validate page number
        if vital_page > vital_records.pages > 0:
            flash("Requested page does not exist. Redirecting to the first page.", "vital_records_table")
            return redirect(url_for('vital_records_table', patient_id=patient_id, vital_page=1,
                                    vital_entries=vital_entries_per_page) + "#vital-record-table")

        # Generate URLs for pagination (next and previous pages)
        vital_next_url = url_for('vital_records_table', vital_page=vital_records.next_num,
                                 vital_entries=vital_entries_per_page, vital_search=vital_search_term,
                                 patient_id=patient_id) + "#vital-record-table" if vital_records.has_next else None
        vital_prev_url = url_for('vital_records_table', vital_page=vital_records.prev_num,
                                 vital_entries=vital_entries_per_page, vital_search=vital_search_term,
                                 patient_id=patient_id) + "#vital-record-table" if vital_records.has_prev else None

        # Render the template with the records and pagination links
        return render_template(
            'patient_clinical.html',
            user=user,
            patient=patient,
            vital_records=vital_records.items,  # List of vital records for the current page
            pagination=vital_records,  # Pass the pagination object
            vital_next_url=vital_next_url,
            vital_prev_url=vital_prev_url,
            vital_entries_per_page=vital_entries_per_page,
            vital_search_term=vital_search_term,
            active_tab=active_tab,
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
        )

    @app.route('/patient/<int:patient_id>/medical_history', methods=['GET', 'POST'])
    @login_required
    def medical_history(patient_id):
        user = UserDoctor.query.get_or_404(current_user.id)
        # Ensure the current user has access to the patient
        patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()

        if request.method == 'POST':
            try:
                # Update fields with data from the form
                medical_record_id = request.form.get('medical_record_id')
                past_medical_history = request.form.get('medicalHistory')
                family_history = request.form.get('familyHistory')
                surgical_history = request.form.get('surgicalHistory')
                known_allergies = request.form.get('knownAllergies')
                immunization_status = request.form.get('immunizationStatus')
                immunization_history = request.form.get('immunizationHistory')
                chronic_conditions = request.form.get('chronicConditions')
                medical_history_additional_notes = request.form.get('historyAdditionalNotes')

                if medical_record_id:
                    medic_record = PatientMedicalHistory.query.get(medical_record_id)
                    if medic_record:
                        medic_record.past_medical_history = past_medical_history
                        medic_record.family_history = family_history
                        medic_record.surgical_history = surgical_history
                        medic_record.known_allergies = known_allergies
                        medic_record.immunization_status = immunization_status
                        medic_record.immunization_history = immunization_history
                        medic_record.chronic_conditions = chronic_conditions
                        medic_record.medical_history_additional_notes = medical_history_additional_notes

                        flash('Medical History updated successfully', 'medical_history')
                    else:
                        flash('Medical history record not found', 'medical_history')
                else:  # Create a new record
                    medic_record = PatientMedicalHistory(
                        patient_id=patient.id,
                        past_medical_history=past_medical_history,
                        family_history=family_history,
                        surgical_history=surgical_history,
                        known_allergies=known_allergies,
                        immunization_status=immunization_status,
                        immunization_history=immunization_history,
                        chronic_conditions=chronic_conditions,
                        medical_history_additional_notes=medical_history_additional_notes
                    )
                    db.session.add(medic_record)
                    flash('Medical History saved successfully', 'medical_history')

                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving medical history: {e}', 'medical_history')
            return redirect(url_for('medical_history', patient_id=patient.id, active_tab='medical-history')
                            + "#medical_history_record_table")

        # GET request: fetch medical history records
        medical_records = PatientMedicalHistory.query.filter_by(patient_id=patient.id).all()

        # Prefill a specific record if requested
        medic_record = None
        medical_record_id = request.args.get('medical_record_id')
        if medical_record_id:
            medic_record = PatientMedicalHistory.query.get(medical_record_id)

        return render_template(
            'patient_clinical.html',
            user=user,
            patient=patient,
            medical_records=medical_records,
            medic_record=medic_record,
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            active_tab='medical-history'
            )

    @app.route('/view-medical-history-record/<int:medical_record_id>', methods=['GET', 'POST'])
    @login_required
    def view_medical_history_record(medical_record_id):
        rec_medic = PatientMedicalHistory.query.get_or_404(medical_record_id)
        patient = Patient.query.filter_by(id=rec_medic.patient_id, doctor_id=current_user.id).first_or_404()
        medic_record = PatientMedicalHistory.query.get(medical_record_id)
        # fetch the patient associated with the record and ensure ownership

        active_tab = request.args.get('active_tab', 'medical-history')

        return render_template(
            'patient_clinical.html',
            user=UserDoctor.query.get_or_404(current_user.id),
            patient=patient,
            rec_medic=rec_medic,  # This is the specific radiology record
            patient_id=rec_medic.patient_id,
            medic_record=medic_record,
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=rec_medic.patient_id).all(),
            active_tab=active_tab,
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all()
        )

    @app.route('/delete-medical-history-record/<int:medical_record_id>', methods=['GET', 'POST'])
    @login_required
    def delete_medical_history_record(medical_record_id):
        rec_medic = PatientMedicalHistory.query.get_or_404(medical_record_id)

        active_tab = request.args.get('active_tab', 'medical-history')
        db.session.delete(rec_medic)
        db.session.commit()
        flash('Medical history successfully.', 'delete_medical_history_record')
        return redirect(url_for('medical_history', patient_id=rec_medic.patient_id, active_tab=active_tab)
                        + '#medical_history_record_table')

    @app.route('/medical-history-records-table', methods=['GET', 'POST'])
    @login_required
    def medical_history_records_table():
        user = UserDoctor.query.get_or_404(current_user.id)

        # Get query parameters
        medical_page = request.args.get('medical_page', 1, type=int)  # Current page
        medical_entries_per_page = request.args.get('medical_entries', 10, type=int)  # Entries per page
        medical_search_term = request.args.get('medical_search', '', type=str).strip()  # Search term
        active_tab = request.args.get('active_tab', 'medical-history')  # Current tab (optional)
        patient_id = request.args.get('patient_id', type=int)  # Get the patient ID from query parameters

        # Fetch the patient
        patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()

        # Start building the query for vital records
        medical_query = PatientMedicalHistory.query.join(Patient).filter(Patient.doctor_id == current_user.id)

        # Apply search filter if there's a search term
        if medical_search_term:
            try:
                medical_query = medical_query.filter(
                    db.or_(
                        db.cast(PatientMedicalHistory.medical_history_last_update,
                                db.String).ilike(f"%{medical_search_term}%")
                    )
                )
                if medical_query.count() == 0:
                    flash("No records for the given date.", "medical_history_records_table")
                    return redirect(url_for('medical_history_records_table', patient_id=patient_id,
                                            medical_entries=medical_entries_per_page) + '#medical_history_record_table')
            except ValueError:
                flash("Invalid date format. Please use 'YYYY-MM-DD':", "medical_history_records_table")
                return redirect(url_for('medical_history_records_table', patient_id=patient_id,
                                        medical_entries=medical_entries_per_page) + '#medical_history_record_table')

        # Paginate the results
        medical_records = medical_query.paginate(page=medical_page, per_page=medical_entries_per_page, error_out=False)

        # validate page number
        if medical_page > medical_records.pages > 0:
            flash("Requested page does not exist. Redirecting to the first page.", "medical_history_records_table")
            return redirect(url_for('medical_history_records_table', patient_id=patient_id, medical_page=1,
                                    medical_entries=medical_entries_per_page) + '#medical_history_record_table')

        # Generate URLs for pagination (next and previous pages)
        medical_next_url = (url_for('medical_history_records_table', medical_page=medical_records.next_num,
                                    medical_entries=medical_entries_per_page,
                                    medical_search=medical_search_term,
                                    patient_id=patient_id)
                            + '#medical_history_record_table') if medical_records.has_next else None

        medical_prev_url = (url_for('medical_history_records_table', medical_page=medical_records.prev_num,
                                    medical_entries=medical_entries_per_page,
                                    medical_search=medical_search_term,
                                    patient_id=patient_id)
                            + '#medical_history_record_table') if medical_records.has_prev else None

        # Render the template with the records and pagination links
        return render_template(
            'patient_clinical.html',
            user=user,
            patient=patient,
            medical_records=medical_records.items,
            pagination=medical_records,  # Pass the pagination object
            medical_next_url=medical_next_url,
            medical_prev_url=medical_prev_url,
            medical_entries_per_page=medical_entries_per_page,
            medical_search_term=medical_search_term,
            vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            active_tab=active_tab
        )

    @app.route('/patient/<int:patient_id>/medicate', methods=['GET', 'POST'])
    @login_required
    def medicate(patient_id):
        user = UserDoctor.query.get_or_404(current_user.id)
        # Ensure the current user has access to the patient
        patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()

        if request.method == 'POST':
            try:
                # Update fields with data from the form, handling empty inputs
                medicate_record_id = request.form.get('medicate_record_id')
                current_medications = request.form.get('currentMedications')
                known_medication_allergies = request.form.get('knownMedicationAllergies')
                previous_medications = request.form.get('previousMedications')
                medication_history_notes = request.form.get('medicationHistoryNotes')
                medication_administration_instructions = request.form.get('medAdministrationInstruct')
                changes_in_medication = request.form.get('medicationChange')
                medication_refills = request.form.get('medRefills')
                medication_start_date = parse_date(request.form.get('medStart'))
                medication_end_date = parse_date(request.form.get('medEnd'))
                next_review_date = parse_date(request.form.get('nextReviewDate'))

                if medicate_record_id:
                    medit_record = PatientMedication.query.get(medicate_record_id)
                    if medit_record:
                        medit_record.current_medications = current_medications
                        medit_record.known_medication_allergies = known_medication_allergies
                        medit_record.previous_medications = previous_medications
                        medit_record.medication_history_notes = medication_history_notes
                        medit_record.medication_administration_instructions = medication_administration_instructions
                        medit_record.changes_in_medication = changes_in_medication
                        medit_record.medication_refills = medication_refills
                        medit_record.medication_start_date = medication_start_date
                        medit_record.medication_end_date = medication_end_date
                        medit_record.next_review_date = next_review_date

                        flash('Medication updated successfully', 'medicate')
                    else:
                        flash('Medication record not found', 'medicate')
                else:
                    medit_record = PatientMedication(
                        patient_id=patient.id,
                        current_medications=current_medications,
                        known_medication_allergies=known_medication_allergies,
                        previous_medications=previous_medications,
                        medication_history_notes=medication_history_notes,
                        medication_administration_instructions=medication_administration_instructions,
                        changes_in_medication=changes_in_medication,
                        medication_refills=medication_refills,
                        medication_start_date=medication_start_date,
                        medication_end_date=medication_end_date,
                        next_review_date=next_review_date
                    )
                    db.session.add(medit_record)
                    flash('Medication saved successfully', 'medicate')

                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving medication: {e}', 'medicate')
            return redirect(url_for('medicate', patient_id=patient.id,
                                    active_tab='medication') + '#medication_record_table')

        medicate_records = PatientMedication.query.filter_by(patient_id=patient.id).all()

        medit_record = None
        medicate_record_id = request.args.get('medicate_record_id')
        if medicate_record_id:
            medit_record = PatientMedication.query.get(medicate_record_id)

        return render_template(
            'patient_clinical.html',
            user=user,
            patient=patient,
            medit_record=medit_record,
            medicate_records=medicate_records,
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            active_tab='medication'
        )

    @app.route('/view-medicate-record/<int:medicate_record_id>', methods=['GET', 'POST'])
    @login_required
    def view_medicate_record(medicate_record_id):
        rec_medit = PatientMedication.query.get_or_404(medicate_record_id)
        patient = Patient.query.filter_by(id=rec_medit.patient_id, doctor_id=current_user.id).first()
        medit_record = PatientMedication.query.get(medicate_record_id)

        active_tab = request.args.get('active_tab', 'medication')

        return render_template('patient_clinical.html',
                               user=UserDoctor.query.get_or_404(current_user.id),
                               patient=patient,
                               rec_medit=rec_medit,
                               patient_id=rec_medit.patient_id,
                               medit_record=medit_record,
                               active_tab=active_tab,
                               medicate_records=PatientMedication.query.filter_by(patient_id=rec_medit.patient_id).all(),
                               radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
                               medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
                               vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
                               laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
                               billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
                               rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
                               vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
                               labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
                               billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
                               medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all()
                               )

    @app.route('/delete-medicate-record/<int:medicate_record_id>', methods=['GET', 'POST'])
    @login_required
    def delete_medicate_record(medicate_record_id):
        rec_medit = PatientMedication.query.get_or_404(medicate_record_id)
        active_tab = request.args.get('active_tab', 'medication')

        db.session.delete(rec_medit)
        db.session.commit()
        flash('Medication record successfully deleted', 'delete_medicate_record')
        return redirect(url_for('medicate', patient_id=rec_medit.patient_id,
                                active_tab=active_tab) + '#medication_record_table'
                        )

    @app.route('/medicate-records-table', methods=['GET', 'POST'])
    @login_required
    def medicate_records_table():
        user = UserDoctor.query.get_or_404(current_user.id)

        # Get query parameters
        medicate_page = request.args.get('medicate_page', 1, type=int)  # Current page
        medicate_entries_per_page = request.args.get('medicate_entries', 10, type=int)  # Entries per page
        medicate_search_term = request.args.get('medicate_search', '', type=str).strip()  # Search term
        active_tab = request.args.get('active_tab', 'medication')  # Current tab (optional)
        patient_id = request.args.get('patient_id', type=int)  # Get the patient ID from query parameters

        # Fetch the patient
        patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()

        # Start building the query for vital records
        medicate_query = PatientMedication.query.join(Patient).filter(Patient.doctor_id == current_user.id)

        # Apply search filter if there's a search term
        if medicate_search_term:
            try:
                medicate_query = medicate_query.filter(
                    db.or_(
                        db.cast(PatientMedication.medication_last_update, db.String).ilike(
                            f"%{medicate_search_term}%")
                    )
                )
                if medicate_query.count() == 0:
                    flash("No records found for the given date.", "medicate_records_table")
                    return redirect(url_for('medicate_records_table', patient_id=patient_id,
                                            medicate_entries=medicate_entries_per_page) + "#medication_record_table")

            except ValueError:
                flash("Invalid date format. Please use 'YYYY-MM-DD:", "medicate_records_table")
                return redirect(url_for('medicate_records_table', patient_id=patient_id,
                                        medicate_entries=medicate_entries_per_page) + "#medication_record_table")

        # Paginate the results
        medicate_records = medicate_query.paginate(page=medicate_page,
                                                   per_page=medicate_entries_per_page, error_out=False)

        # Validate page number
        if medicate_page > medicate_records.pages > 0:
            flash("Requested page does not exist. Redirecting to the first page.", "medicate_records_table")
            return redirect(url_for("medicate_records_table", patient_id=patient_id, medicate_page=1,
                                    medicate_entries=medicate_entries_per_page) + "#medication_record_table")

        # Generate URLs for pagination (next and previous pages)
        medicate_next_url = (url_for('medicate_records_table', medicate_page=medicate_records.next_num,
                                     medicate_entries=medicate_entries_per_page,
                                     medicate_search=medicate_search_term,
                                     patient_id=patient_id)
                             + "#medication_record_table") if medicate_records.has_next else None
        medicate_prev_url = (url_for('medicate_records_table', medicate_page=medicate_records.prev_num,
                                     medicate_entries=medicate_entries_per_page,
                                     medicate_search=medicate_search_term,
                                     patient_id=patient_id)
                             + "#medication_record_table") if medicate_records.has_prev else None

        # Render the template with the records and pagination links
        return render_template(
            'patient_clinical.html',
            user=user,
            patient=patient,
            medicate_records=medicate_records.items,  # List of vital records for the current page
            pagination=medicate_records,  # Pass the pagination object
            medicate_next_url=medicate_next_url,
            medicate_prev_url=medicate_prev_url,
            medicate_entries_per_page=medicate_entries_per_page,
            medicate_search_term=medicate_search_term,
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            active_tab=active_tab
        )

    @app.route('/patient/<int:patient_id>/laboratory', methods=['GET', 'POST'])
    @login_required
    def laboratory(patient_id):
        user = UserDoctor.query.get_or_404(current_user.id)
        patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()

        if request.method == 'POST':
            try:
                # Update fields with data from the form
                laboratory_record_id = request.form.get('laboratory_record_id')
                test_type = request.form.get('testType')
                test_code = request.form.get('testCode')
                test_result = request.form.get('testResult')
                units = request.form.get('Unit')
                reference_range = request.form.get('referenceRange')
                test_date = parse_datetime(request.form.get('testDate'))
                laboratory_status = request.form.get('laboratoryStatus')
                interpretation = request.form.get('interpret')
                laboratory_notes = request.form.get('labNotes')

                if laboratory_record_id:
                    labtory_record = PatientLaboratory.query.get(laboratory_record_id)
                    if labtory_record:
                        labtory_record.test_type = test_type
                        labtory_record.test_code = test_code
                        labtory_record.test_result = test_result
                        labtory_record.units = units
                        labtory_record.reference_range = reference_range
                        labtory_record.test_date = test_date
                        labtory_record.laboratory_status = laboratory_status
                        labtory_record.interpretation = interpretation
                        labtory_record.laboratory_notes = laboratory_notes

                        flash('Laboratory record updated successfully', 'laboratory')
                    else:
                        flash('Laboratory record not found', 'laboratory')
                else:
                    labtory_record = PatientLaboratory(
                        patient_id=patient_id,
                        test_type=test_type,
                        test_code=test_code,
                        test_result=test_result,
                        units=units,
                        reference_range=reference_range,
                        test_date=test_date,
                        laboratory_status=laboratory_status,
                        interpretation=interpretation,
                        laboratory_notes=laboratory_notes
                    )
                    db.session.add(labtory_record)
                    flash('Laboratory record saved successfully', 'laboratory')

                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving laboratory rec'
                      f'ord: {e}', 'laboratory')
            return redirect(url_for('laboratory', patient_id=patient_id, active_tab='laboratory')
                            + '#laboratory_record_table')

        # Get request: fetch laboratory records
        laboratory_records = PatientLaboratory.query.filter_by(patient_id=patient_id).all()

        # prefill a specific record if requested
        labtory_record = None
        laboratory_record_id = request.args.get('laboratory_record_id')
        if laboratory_record_id:
            labtory_record = PatientLaboratory.query.get(laboratory_record_id)

        return render_template(
            'patient_clinical.html',
            user=user,
            patient=patient,
            laboratory_records=laboratory_records,
            labtory_record=labtory_record,
            active_tab='laboratory',
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all()
        )

    @app.route('/view-laboratory-record/<int:laboratory_record_id>', methods=['GET', 'POST'])
    @login_required
    def view_laboratory_record(laboratory_record_id):
        rec_labtory = PatientLaboratory.query.get_or_404(laboratory_record_id)
        patient = Patient.query.filter_by(id=rec_labtory.patient_id, doctor_id=current_user.id).first_or_404()
        labtory_record = PatientLaboratory.query.get(laboratory_record_id)

        active_tab = request.args.get('active_tab', 'laboratory')

        return render_template(
            'patient_clinical.html',
            user=UserDoctor.query.get_or_404(current_user.id),
            patient=patient,
            rec_labtory=rec_labtory,
            patient_id=rec_labtory.patient_id,
            labtory_record=labtory_record,
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=rec_labtory.patient_id).all(),
            active_tab=active_tab,
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all()
        )

    @app.route('/delete-laboratory-record/<int:laboratory_record_id>', methods=['GET', 'POST'])
    @login_required
    def delete_laboratory_record(laboratory_record_id):
        rec_labtory = PatientLaboratory.query.get_or_404(laboratory_record_id)

        active_tab = request.args.get('active_tab', 'laboratory')
        db.session.delete(rec_labtory)
        db.session.commit()
        flash('Laboratory record successfully deleted.', 'delete_laboratory_record')
        return redirect(url_for('laboratory', patient_id=rec_labtory.patient_id,
                                active_tab=active_tab) + '#laboratory_record_table')

    @app.route('/laboratory-records-table', methods=['GET', 'POST'])
    @login_required
    def laboratory_records_table():
        user = UserDoctor.query.get_or_404(current_user.id)

        # Get query parameters
        laboratory_page = request.args.get('laboratory_page', 1, type=int)  # Current page
        laboratory_entries_per_page = request.args.get('laboratory_entries', 10, type=int)  # Entries per page
        laboratory_search_term = request.args.get('laboratory_search', '', type=str).strip()  # Search term
        active_tab = request.args.get('active_tab', 'laboratory')  # Current tab (optional)
        patient_id = request.args.get('patient_id', type=int)  # Get the patient ID from query parameters

        # Fetch the patient
        patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()

        # Start building the query for vital records
        laboratory_query = PatientLaboratory.query.join(Patient).filter(Patient.doctor_id == current_user.id)

        # Apply search filter if there's a search term
        if laboratory_search_term:
            search_results = False
            try:
                laboratory_query = laboratory_query.filter(
                    db.or_(
                        db.cast(PatientLaboratory.test_date, db.String).ilike(f"%{laboratory_search_term}%"),
                        db.cast(PatientLaboratory.laboratory_updated_at, db.String).ilike(f"%{laboratory_search_term}%")
                    )
                )
                results = laboratory_query.all()
                if results:
                    search_results = True
            except ValueError:
                pass

            if not search_results:
                laboratory_query = laboratory_query.filter(PatientLaboratory.test_type.ilike
                                                           (f"%{laboratory_search_term}%"))
                results = laboratory_query.all()
                if not results:
                    flash("No records found for the given search term.", 'laboratory_records_table')
                    return redirect(url_for('laboratory_records_table', patient_id=patient_id,
                                            laboratory_entries=laboratory_entries_per_page
                                            ) + '#laboratory_record_table')

        # Paginate the results
        laboratory_records = laboratory_query.paginate(page=laboratory_page, per_page=laboratory_entries_per_page,
                                                       error_out=False)

        # validate page number
        if laboratory_page > laboratory_records.pages > 0:
            flash("Requested page does not exist. Redirecting to the first page.", 'laboratory_records_table')
            return redirect(url_for('laboratory_records_table', patient_id=patient_id, laboratory_page=1,
                                    laboratory_entries=laboratory_entries_per_page)
                            + '#laboratory_record_table')

        # Generate URLs for pagination (next and previous pages)
        laboratory_next_url = (url_for('laboratory_records_table', laboratory_page=laboratory_records.next_num,
                                       laboratory_entries=laboratory_entries_per_page,
                                       laboratory_search=laboratory_search_term,
                                       patient_id=patient_id)
                               + '#laboratory_record_table') if laboratory_records.has_next else None
        laboratory_prev_url = (url_for('laboratory_records_table', laboratory_page=laboratory_records.prev_num,
                                       laboratory_entries=laboratory_entries_per_page,
                                       laboratory_search=laboratory_search_term,
                                       patient_id=patient_id)
                               + '#laboratory_record_table') if laboratory_records.has_prev else None

        # Render the template with the records and pagination links
        return render_template(
            'patient_clinical.html',
            user=user,
            patient=patient,
            laboratory_records=laboratory_records.items,  # List of vital records for the current page
            pagination=laboratory_records,  # Pass the pagination object
            laboratory_next_url=laboratory_next_url,
            laboratory_prev_url=laboratory_prev_url,
            laboratory_entries_per_page=laboratory_entries_per_page,
            laboratory_search_term=laboratory_search_term,
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            active_tab=active_tab
        )

    @app.route('/patient/<int:patient_id>/billing', methods=['GET', 'POST'])
    @login_required
    def billing(patient_id):
        user = UserDoctor.query.get_or_404(current_user.id)
        # Ensure the current user has access to the patient
        patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()

        if request.method == 'POST':
            try:
                # Update fields with data from the form, handling empty inputs
                billing_record_id = request.form.get('billing_record_id')
                billing_date = parse_date(request.form.get('billingDate'))
                billing_charges = request.form.get('billingCharge')
                payment_method = request.form.get('paymentMethod')
                payment_status = request.form.get('paymentStatus')
                insurance_provider = request.form.get('insuranceProvider') if payment_method == 'insurance' else None
                insurance_claim_number = request.form.get('claimNumber') if payment_method == 'insurance' else None
                billing_comments = request.form.get('billComment')
                billing_notes = request.form.get('billNotes')

                if billing_record_id:
                    billi_record = PatientBilling.query.get(billing_record_id)
                    if billi_record:
                        billi_record.billing_date = billing_date
                        billi_record.billing_charges = billing_charges
                        billi_record.payment_method = payment_method
                        billi_record.payment_status = payment_status
                        billi_record.insurance_provider = insurance_provider
                        billi_record.insurance_claim_number = insurance_claim_number
                        billi_record.billing_comments = billing_comments
                        billi_record.billing_notes = billing_notes

                        flash('Billing updated successfully', 'billing')
                    else:
                        flash('Billing record not found', 'billing')
                else:
                    billi_record = PatientBilling(
                        patient_id=patient.id,
                        billing_date=billing_date,
                        billing_charges=billing_charges,
                        payment_method=payment_method,
                        payment_status=payment_status,
                        insurance_provider=insurance_provider,
                        insurance_claim_number=insurance_claim_number,
                        billing_comments=billing_comments,
                        billing_notes=billing_notes
                    )
                    db.session.add(billi_record)
                    flash('Billing saved successfully', 'billing')
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving billing record: {e}', 'billing')
            return redirect(url_for('billing', patient_id=patient.id, active_tab='billing') + '#billing_record_table')

        billing_records = PatientBilling.query.filter_by(patient_id=patient.id).all()

        # prefill a specific record if requested
        billi_record = None
        billing_record_id = request.args.get('billing_record_id')
        if billing_record_id:
            billi_record = PatientBilling.query.get(billing_record_id)

        return render_template(
            'patient_clinical.html',
            user=user,
            patient=patient,
            billing_records=billing_records,
            billi_record=billi_record,
            active_tab='billing',
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all()
        )

    @app.route('/view-billing-record/<int:billing_record_id>', methods=['GET', 'POST'])
    @login_required
    def view_billing_record(billing_record_id):
        rec_billi = PatientBilling.query.get_or_404(billing_record_id)
        patient = Patient.query.filter_by(id=rec_billi.patient_id, doctor_id=current_user.id).first_or_404()
        billi_record = PatientBilling.query.get(billing_record_id)

        active_tab = request.args.get('active_tab', 'billing')

        return render_template(
            'patient_clinical.html',
            user=UserDoctor.query.get_or_404(current_user.id),
            patient=patient,
            rec_billi=rec_billi,
            patient_id=rec_billi.patient_id,
            billi_record=billi_record,
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            active_tab=active_tab,
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all()
        )

    @app.route('/delete-billing-record/<int:billing_record_id>', methods=['GET', 'POST'])
    @login_required
    def delete_billing_record(billing_record_id):
        rec_billi = PatientBilling.query.get_or_404(billing_record_id)

        active_tab = request.args.get('active_tab', 'billing')
        db.session.delete(rec_billi)
        db.session.commit()
        flash('Billing record successfully deleted', 'delete_billing_record')
        return redirect(url_for('billing', patient_id=rec_billi.patient_id,
                                active_tab=active_tab))

    @app.route('/billing-records-table', methods=['GET', 'POST'])
    @login_required
    def billing_records_table():
        user = UserDoctor.query.get_or_404(current_user.id)

        # Get query parameters
        billing_page = request.args.get('billing_page', 1, type=int)  # Current page
        billing_entries_per_page = request.args.get('billing_entries', 10, type=int)  # Entries per page
        billing_search_term = request.args.get('billing_search', '', type=str).strip()  # Search term
        active_tab = request.args.get('active_tab', 'billing')  # Current tab (optional)
        patient_id = request.args.get('patient_id', type=int)  # Get the patient ID from query parameters

        # Fetch the patient
        patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()

        # Start building the query for vital records
        billing_query = PatientBilling.query.join(Patient).filter(Patient.doctor_id == current_user.id)

        # Apply search filter if there's a search term
        if billing_search_term:
            try:
                billing_query = billing_query.filter(
                    db.or_(
                        db.cast(PatientBilling.billing_date, db.String).ilike(f"%{billing_search_term}%"),
                        db.cast(PatientBilling.billing_updated_at, db.String).ilike(f"%{billing_search_term}%")
                    )
                )
                if billing_query.count() == 0:
                    flash("No records found for the given date.", "billing_records_table")
                    return redirect(url_for('billing_records_table', patient_id=patient_id,
                                            billing_entries=billing_entries_per_page) + '#billing_record_table')
            except ValueError:
                flash("Invalid date format. Please use 'YYYY-MM-DD'.", "billing_records_table")
                return redirect(url_for('billing_records_table', patient_id=patient_id,
                                        billing_entries=billing_entries_per_page) + '#billing_record_table')

        # Paginate the results
        billing_records = billing_query.paginate(page=billing_page, per_page=billing_entries_per_page,
                                                 error_out=False)
        # validate page number
        if billing_page > billing_records > 0:
            flash("Requested page does not exist. Redirecting to the first page.", "billing_records_table")
            return redirect(url_for('billing_records_table', patient_id=patient_id,
                                    billing_entries=billing_entries_per_page) + '#billing_record_table')

        # Generate URLs for pagination (next and previous pages)
        billing_next_url = (url_for('billing_records_table', billing_page=billing_records.next_num,
                                    billing_entries=billing_entries_per_page,
                                    billing_search=billing_search_term,
                                    patient_id=patient_id)
                            + '#billing_record_table') if billing_records.has_next else None
        billing_prev_url = (url_for('billing_records_table', billing_page=billing_records.prev_num,
                                    billing_entries=billing_entries_per_page,
                                    billing_search=billing_search_term,
                                    patient_id=patient_id)
                            + '#billing_record_table') if billing_records.has_prev else None

        # Render the template with the records and pagination links
        return render_template(
            'patient_clinical.html',
            user=user,
            patient=patient,
            billing_records=billing_records.items,  # List of vital records for the current page
            pagination=billing_records,  # Pass the pagination object
            billing_next_url=billing_next_url,
            billing_prev_url=billing_prev_url,
            billing_entries_per_page=billing_entries_per_page,
            billing_search_term=billing_search_term,
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            radiology_records=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            active_tab=active_tab
        )

    @app.route('/patient/<int:patient_id>/radiology', methods=['GET', 'POST'])
    @login_required
    def radiology(patient_id):
        user = UserDoctor.query.get_or_404(current_user.id)  # Get the logged-in doctor
        patient = Patient.query.filter_by(id=patient_id,
                                          doctor_id=current_user.id).first_or_404()
        # Ensure the doctor owns the patient

        # Handle POST request for creating or updating a radiology record
        if request.method == 'POST':
            try:
                record_id = request.form.get('record_id')
                radiology_procedure = request.form.get('radProcedure')
                procedure_date = parse_date(request.form.get('procedureDate'))
                imaging_type = request.form.get('imagingType')
                image_files = request.files.getlist('imageFiles')
                image_interpretation = request.form.get('imageInterpretation')
                findings = request.form.get('findings')
                recommendations = request.form.get('recommendations')
                follow_up_required = request.form.get('followUp')
                follow_up_date = parse_date(request.form.get('followUpDate'))
                radiologist_name = request.form.get('radiologistName')
                radiology_additional_notes = request.form.get('radAdditionalNotes')

                # Handle image uploads
                image_paths = []
                for image_file in image_files:
                    if image_file:
                        # Generate a unique filename using uuid
                        filename = secure_filename(image_file.filename)
                        file_extension = os.path.splitext(filename)[1]  # Get file extension
                        unique_filename = f"{uuid.uuid4()}{file_extension}"  # Unique filename with extension
                        filepath = os.path.join(app.config['PATIENT_DICOM_FOLDER'], unique_filename)
                        image_file.save(filepath)
                        image_paths.append(unique_filename)  # Store just the unique filename

                # Create or update the radiology record
                if record_id:
                    # Update existing record
                    rad_record = PatientRadiology.query.get(record_id)
                    if rad_record:
                        # Fetch old images
                        old_images = rad_record.images.split(',') if rad_record.images else []
                        # only update images if new ones are uploaded
                        if image_paths:
                            # remove old images from the file system
                            for old_image in old_images:
                                old_image_path = os.path.join(app.config['PATIENT_DICOM_FOLDER'], old_image)
                                if os.path.exists(old_image_path):
                                    os.remove(old_image_path)

                            # update the images field with new images
                            rad_record.images = ','.join(image_paths)

                        # updating other fields
                        rad_record.radiology_procedure = radiology_procedure
                        rad_record.procedure_date = procedure_date
                        rad_record.imaging_type = imaging_type
                        rad_record.image_interpretation = image_interpretation
                        rad_record.findings = findings
                        rad_record.recommendations = recommendations
                        rad_record.follow_up_required = follow_up_required
                        rad_record.follow_up_date = follow_up_date
                        rad_record.radiologist_name = radiologist_name
                        rad_record.radiology_additional_notes = radiology_additional_notes
                else:
                    # Create new record
                    rad_record = PatientRadiology(
                        patient_id=patient.id,
                        radiology_procedure=radiology_procedure,
                        procedure_date=procedure_date,
                        imaging_type=imaging_type,
                        image_interpretation=image_interpretation,
                        findings=findings,
                        recommendations=recommendations,
                        follow_up_required=follow_up_required,
                        follow_up_date=follow_up_date,
                        radiologist_name=radiologist_name,
                        radiology_additional_notes=radiology_additional_notes,
                        images=','.join(image_paths)  # Save image paths in the database
                    )
                    db.session.add(rad_record)

                db.session.commit()
                flash('Radiology record saved successfully!', 'radiology')

            except Exception as e:
                db.session.rollback()
                flash(f'Error updating radiology record: {e}', 'radiology')

            return redirect(url_for('radiology', patient_id=patient.id, active_tab='radiology')
                            + '#radiology_record_table')

        # GET request: fetch radiology records
        radiology_records = PatientRadiology.query.filter_by(patient_id=patient.id).all()
        # Check if there is a specific record to pre-fill, otherwise return empty
        rad_record = None
        record_id = request.args.get('record_id')  # Get record_id from the query parameters
        if record_id:
            rad_record = PatientRadiology.query.get(record_id)  # Fetch specific record by ID

        return render_template('patient_clinical.html', user=user, patient=patient,
                               radiology_records=radiology_records,
                               rad_record=rad_record,
                               active_tab='radiology',
                               vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
                               medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
                               medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
                               laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
                               billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
                               vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
                               medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
                               labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
                               billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
                               medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all()
                               )

    @app.route('/view-radiology-record/<int:record_id>', methods=['GET', 'POST'])
    @login_required
    def view_radiology_record(record_id):
        # Query the radiology record
        user = UserDoctor.query.get_or_404(current_user.id)
        record = PatientRadiology.query.get_or_404(record_id)
        rad_record = PatientRadiology.query.get(record_id)
        patient = Patient.query.filter_by(id=record.patient_id, doctor_id=current_user.id).first_or_404()

        # Fetch the patient associated with the record and ensure ownership
        active_tab = request.args.get('active_tab', 'radiology')

        # Render the patient_clinical.html with the radiology record data
        return render_template(
            'patient_clinical.html',
            user=user,
            patient=patient,
            record=record,  # This is the specific radiology record
            patient_id=record.patient_id,
            rad_record=rad_record,
            radiology_records=PatientRadiology.query.filter_by(patient_id=record.patient_id).all(),
            vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            active_tab=active_tab
            )

    @app.route('/delete-radiology-record/<int:record_id>', methods=['GET', 'POST'])
    @login_required
    def delete_radiology_record(record_id):
        record = PatientRadiology.query.get_or_404(record_id)
        active_tab = request.args.get('active_tab', 'radiology')

        # Get the associated image files from the record (assuming 'images' is a comma-separated string)
        image_paths = record.images.split(',') if record.images else []

        # Delete the associated images from the upload folder
        for image in image_paths:
            file_path = os.path.join(app.config['PATIENT_DICOM_FOLDER'], image)
            if os.path.exists(file_path):
                os.remove(file_path)  # Delete the file

        # Now, delete the record from the database
        db.session.delete(record)
        db.session.commit()

        flash('Radiology record deleted successfully.', 'delete_radiology_record')
        return redirect(url_for('radiology', patient_id=record.patient_id, active_tab=active_tab,
                                ) + '#radiology_record_table')

    @app.route('/radiology-records-table', methods=['GET', 'POST'])
    @login_required
    def radiology_records_table():
        user = UserDoctor.query.get_or_404(current_user.id)

        # Get query parameters
        radiology_page = request.args.get('radiology_page', 1, type=int)  # Current page
        radiology_entries_per_page = request.args.get('radiology_entries', 10, type=int)  # Entries per page
        radiology_search_term = request.args.get('radiology_search', '', type=str).strip()  # Search term
        active_tab = request.args.get('active_tab', 'radiology')  # Current tab (optional)
        patient_id = request.args.get('patient_id', type=int)  # Get the patient ID from query parameters

        # Fetch the patient
        patient = Patient.query.filter_by(id=patient_id, doctor_id=current_user.id).first_or_404()

        # Start building the query for radiology records
        radiology_query = PatientRadiology.query.filter(PatientRadiology.patient_id == patient.id)

        # Apply search filter if there's a search term
        if radiology_search_term:
            radiology_query = radiology_query.filter(
                db.or_(
                    PatientRadiology.radiology_procedure.ilike(f"%{radiology_search_term}%"),
                    db.cast(PatientRadiology.updated_at, db.String).ilike(f"%{radiology_search_term}%"),
                    db.cast(PatientRadiology.procedure_date, db.String).ilike(f"%{radiology_search_term}%")
                )
            )

        # Paginate the results
        radiology_records = radiology_query.paginate(page=radiology_page, per_page=radiology_entries_per_page,
                                                     error_out=False)

        # Validate page number
        if radiology_page > radiology_records.pages > 0:
            flash("Requested page does not exist. Redirecting to the first page", "radiology_records_table")
            return redirect(url_for('radiology_records_table', patient_id=patient_id, radiology_page=1,
                                    radiology_entries=radiology_entries_per_page) + '#radiology_record_table')

        # Generate URLs for pagination (next and previous pages)
        radiology_next_url = (url_for('radiology_records_table', radiology_page=radiology_records.next_num,
                                      radiology_entries=radiology_entries_per_page,
                                      radiology_search=radiology_search_term,
                                      patient_id=patient_id)
                              + '#radiology_record_table') if radiology_records.has_next else None
        radiology_prev_url = (url_for('radiology_records_table', radiology_page=radiology_records.prev_num,
                                      radiology_entries=radiology_entries_per_page,
                                      radiology_search=radiology_search_term,
                                      patient_id=patient_id)
                              + '#radiology_record_table') if radiology_records.has_prev else None

        # Render the template with the records and pagination links
        return render_template(
            'patient_clinical.html',
            user=user,
            patient=patient,
            radiology_records=radiology_records.items,  # List of radiology records for the current page
            pagination=radiology_records,  # Pass the pagination object
            radiology_next_url=radiology_next_url,
            radiology_prev_url=radiology_prev_url,
            radiology_entries_per_page=radiology_entries_per_page,
            radiology_search_term=radiology_search_term,
            medical_records=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            vital_records=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medicate_records=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            laboratory_records=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billing_records=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            rad_record=PatientRadiology.query.filter_by(patient_id=patient.id).all(),
            vit_record=PatientVital.query.filter_by(patient_id=patient.id).all(),
            medit_record=PatientMedication.query.filter_by(patient_id=patient.id).all(),
            labtory_record=PatientLaboratory.query.filter_by(patient_id=patient.id).all(),
            billi_record=PatientBilling.query.filter_by(patient_id=patient.id).all(),
            medic_record=PatientMedicalHistory.query.filter_by(patient_id=patient.id).all(),
            active_tab=active_tab
        )

    @app.route('/delete_patient/<int:patient_id>', methods=['GET', 'POST'])
    @login_required
    def delete_patient(patient_id):
        # Fetch the patient record
        patient = Patient.query.get_or_404(patient_id)

        # Delete the patient
        db.session.delete(patient)
        db.session.commit()

        flash(f"Patient {patient.first_name} {patient.last_name} has been deleted.", "delete_patient")
        return redirect(url_for('patients_dashboard'))

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))
