# models.py
import random

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime


db = SQLAlchemy()


class UserDoctor(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(400), nullable=False)

    # Profile Section
    title = db.Column(db.String(50), nullable=True)
    name = db.Column(db.String(50), nullable=True)
    profile_picture = db.Column(db.String(100), nullable=True)

    # Personal and Contact Information
    first_name = db.Column(db.String(80), nullable=True)
    middle_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    telecom1 = db.Column(db.String(20), nullable=True)
    telecom2 = db.Column(db.String(20), nullable=True)
    current_home_address = db.Column(db.String(200), nullable=True)
    permanent_home_address = db.Column(db.String(200), nullable=True)

    # Professional Information
    license_number = db.Column(db.String(50), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    specialization = db.Column(db.String(100), nullable=True)

    # One-to-One Relationship with DoctorEmergencyContact
    doc_emergency_contact_id = db.Column(
        db.Integer,
        db.ForeignKey('doctor_emergency_contact.id', ondelete='CASCADE'),
        unique=True,
        nullable=True
    )

    # One-to-one relationship with DoctorEmergencyContact
    doc_emergency_contact = db.relationship(
        'DoctorEmergencyContact',
        back_populates='user',
        cascade='all',
        uselist=False
    )

    # One-to-Many Relationship with Patients
    patients = db.relationship(
        'Patient',
        back_populates='doctor',
        cascade="all, delete-orphan",
        foreign_keys='Patient.doctor_id'  # Specify which foreign key to use
    )

    def __repr__(self):
        return f"<UserDoctor {self.username}>"


# UserEmergencyContact model (Emergency contact information)
class DoctorEmergencyContact(db.Model):
    __tablename__ = 'doctor_emergency_contact'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=True)
    middle_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    relation = db.Column(db.String(50), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    dob = db.Column(db.Date, nullable=True)  # Date of birth
    email = db.Column(db.String(120), nullable=True)
    telecom = db.Column(db.String(15), nullable=True)
    address = db.Column(db.Text, nullable=True)
    validity_of_contact = db.Column(db.String(20), nullable=True)

    # Back reference to UserDoctor
    user = db.relationship('UserDoctor', back_populates='doc_emergency_contact')

    def __repr__(self):
        return f"<DoctorEmergencyContact {self.first_name} {self.last_name}>"


class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer, unique=True, nullable=False, default=lambda: Patient.generate_unique_patient_id())
    photo = db.Column(db.String(200))  # Filepath to photo
    language_preferred = db.Column(db.String(50))
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=True)
    marital_status = db.Column(db.String(20))
    age = db.Column(db.Integer)
    birth_date = db.Column(db.Date)
    is_multiple_birth = db.Column(db.Boolean, default=False)
    birth_no = db.Column(db.String(10))
    is_deceased = db.Column(db.Boolean, default=False)
    date_deceased = db.Column(db.Date, nullable=True)
    reason_deceased = db.Column(db.Text, nullable=True)
    phone_number = db.Column(db.String(15))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Link to doctor who added this patient
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign Key linking to UserDoctor
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Specify which foreign key to use for the relationship
    doctor = db.relationship(
        'UserDoctor',
        back_populates='patients',
        foreign_keys=[doctor_id]  # Specify the foreign key explicitly
    )

    # One-to-One Relationship with Emergency Contact
    pat_emergency_contact = db.relationship('PatientEmergencyContact', back_populates='patient', cascade='all',
                                            uselist=False)
    vitals = db.relationship(
        'PatientVital',
        back_populates='patient',
        cascade='all, delete-orphan',
    )

    medical_history = db.relationship(
        'PatientMedicalHistory',
        back_populates='patient',
        cascade='all, delete-orphan',
    )

    medication = db.relationship(
        'PatientMedication',
        back_populates='patient',
        cascade='all, delete-orphan',
    )

    laboratory = db.relationship(
        'PatientLaboratory',
        back_populates='patient',
        cascade='all, delete-orphan',
    )

    billing = db.relationship(
        'PatientBilling',
        back_populates='patient',
        cascade='all, delete-orphan',
    )

    radiology = db.relationship(
        'PatientRadiology',
        back_populates='patient',
        cascade='all, delete-orphan',
    )

    @classmethod
    def generate_unique_patient_id(cls):
        while True:
            # Generate a random 4-digit number (between 1000 and 9999)
            patient_id = random.randint(1000, 9999)

            # Check if the ID already exists in the database
            existing_patient = cls.query.filter_by(patient_id=patient_id).first()

            # If the ID does not exist, return it as the unique patient ID
            if not existing_patient:
                return patient_id

    def __repr__(self):
        return f"<Patient {self.first_name} {self.last_name}>"


class PatientEmergencyContact(db.Model):
    __tablename__ = 'patient_emergency_contacts'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    language_preferred = db.Column(db.String(50))
    first_name = db.Column(db.String(100), nullable=True)
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=True)
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    birth_date = db.Column(db.Date)
    relation = db.Column(db.String(20))
    phone_number = db.Column(db.String(15))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)

    # Back reference to Patient
    patient = db.relationship('Patient', back_populates='pat_emergency_contact')

    def __repr__(self):
        return f"<Patient {self.first_name} {self.last_name}>"


class PatientVital(db.Model):
    __tablename__ = 'vitals'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    weight = db.Column(db.String(100), nullable=True)  # Weight in kilograms
    blood_pressure = db.Column(db.String(20), nullable=True)  # Format: e.g., "120/80 mmHg"
    temperature = db.Column(db.String(100), nullable=True)  # Temperature in °C
    heart_rate = db.Column(db.String(100), nullable=True)  # Beats per minute
    respiratory_rate = db.Column(db.String(100), nullable=True)  # Breaths per minute
    oxygen_saturation = db.Column(db.String(100), nullable=True)  # Percentage
    blood_glucose = db.Column(db.String(100), nullable=True)  # Blood glucose in mg/dL
    pulse_oximetry = db.Column(db.String(100), nullable=True)  # Percentage
    measurement_date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)  # Measurement timestamp
    vital_status = db.Column(db.String(50), nullable=True)  # Status options (Final, Preliminary, etc.)
    vital_notes = db.Column(db.Text, nullable=True)  # Optional remarks or notes
    vital_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Back reference to Patient
    patient = db.relationship('Patient', back_populates='vitals')

    def __repr__(self):
        return f"<PatientVital patient_id={self.patient_id} status={self.status}>"


class PatientMedicalHistory(db.Model):
    __tablename__ = 'medical_history'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    past_medical_history = db.Column(db.Text, nullable=True)  # Past medical conditions and diagnoses
    family_history = db.Column(db.Text, nullable=True)  # Relevant family history
    surgical_history = db.Column(db.Text, nullable=True)  # Previous surgeries or procedures
    known_allergies = db.Column(db.Text, nullable=True)  # Known allergies (e.g., drugs, foods, environmental)
    immunization_status = db.Column(db.Text, nullable=True)  # General immunization status
    immunization_history = db.Column(db.Text, nullable=True)  # Detailed immunization history (dates, vaccines)
    chronic_conditions = db.Column(db.Text, nullable=True)  # Chronic conditions like diabetes, asthma, etc.
    medical_history_additional_notes = db.Column(db.Text, nullable=True)  # Optional notes
    medical_history_last_update = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)  # Date of last update

    patient = db.relationship('Patient', back_populates='medical_history')

    def __repr__(self):
        return f"<MedicalHistory {self.id}>"


class PatientMedication(db.Model):
    __tablename__ = 'medication'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    current_medications = db.Column(db.Text, nullable=True)  # Current medications with dosages and frequency
    known_medication_allergies = db.Column(db.Text, nullable=True)  # Known medication allergies
    previous_medications = db.Column(db.Text, nullable=True)  # Previous medications prescribed
    medication_history_notes = db.Column(db.Text, nullable=True)  # Additional notes on medication history
    medication_administration_instructions = db.Column(db.Text,
                                                       nullable=True)  # Instructions for administering medications
    changes_in_medication = db.Column(db.Text, nullable=True)  # Recent changes to medication regimen
    medication_refills = db.Column(db.String(100), nullable=True)  # Number of refills available
    medication_start_date = db.Column(db.Date, nullable=True)  # Start date of the medication
    medication_end_date = db.Column(db.Date, nullable=True)  # End date of the medication
    next_review_date = db.Column(db.Date, nullable=True)  # Next medication review date
    medication_last_update = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)  # Date of the last update

    patient = db.relationship('Patient', back_populates='medication')

    def __repr__(self):
        return f"<PatientMedication {self.id}>"


class PatientLaboratory(db.Model):
    __tablename__ = 'laboratory'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    test_type = db.Column(db.String(50), nullable=True)  # e.g., Blood Test, Urine Test
    test_code = db.Column(db.String(50), nullable=True)  # e.g., CBC, Blood Sugar
    test_result = db.Column(db.String(100), nullable=True)  # The result of the test
    units = db.Column(db.String(20), nullable=True)  # e.g., mg/dL, g/L
    reference_range = db.Column(db.String(50), nullable=True)  # e.g., 70-100 mg/dL
    test_date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)  # Date and time of the test
    laboratory_status = db.Column(db.String(20), nullable=True)  # e.g., Final, Preliminary
    interpretation = db.Column(db.String(20), nullable=True)  # e.g., Normal, Abnormal
    laboratory_notes = db.Column(db.Text, nullable=True)  # Optional remarks
    laboratory_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', back_populates='laboratory')

    def __repr__(self):
        return f"<Laboratory id={self.id}"


class PatientBilling(db.Model):
    __tablename__ = 'billing'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    billing_date = db.Column(db.Date, nullable=True, default=datetime.utcnow)
    billing_charges = db.Column(db.String(100), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    payment_status = db.Column(db.String(50), nullable=True)
    insurance_provider = db.Column(db.String(100), nullable=True)  # Only applicable if payment method is 'insurance'
    insurance_claim_number = db.Column(db.String(100), nullable=True)
    billing_comments = db.Column(db.Text, nullable=True)
    authorized_by = db.Column(db.String(100), nullable=True)
    billing_notes = db.Column(db.Text, nullable=True)
    billing_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', back_populates='billing')

    def __repr__(self):
        return f"<Billing {self.id}>"


class PatientRadiology(db.Model):
    __tablename__ = 'radiology'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    radiology_procedure = db.Column(db.String(100), nullable=True)
    procedure_date = db.Column(db.Date, nullable=True)
    imaging_type = db.Column(db.String(50), nullable=True)
    image_interpretation = db.Column(db.Text, nullable=True)
    radiologist_name = db.Column(db.String(100), nullable=True)
    findings = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.Text, nullable=True)
    follow_up_required = db.Column(db.String(100), nullable=True)
    follow_up_date = db.Column(db.Date, nullable=True)  #
    radiology_additional_notes = db.Column(db.Text, nullable=True)
    radiology_created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', back_populates='radiology')
    images = db.Column(db.Text)  # Stores the paths of uploaded images
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PatientRadiology id={self.id}, patient_id={self.patient_id}, procedure={self.radiology_procedure}>"


class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Link to logged-in user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ContactMessage {self.name} - {self.subject}>"