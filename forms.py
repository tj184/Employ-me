from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField, TextAreaField,
                     FileField, SubmitField, DateField, RadioField, SelectMultipleField, widgets)
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, Regexp
from flask_wtf.file import FileAllowed
from models import User
import re

# ---------- Preset data ----------
INDIAN_CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Ahmedabad', 'Chennai',
    'Kolkata', 'Pune', 'Jaipur', 'Lucknow', 'Surat', 'Nagpur', 'Indore',
    'Bhopal', 'Visakhapatnam', 'Vadodara', 'Rajkot', 'Nashik', 'Aurangabad',
    'Dhanbad', 'Coimbatore', 'Madurai', 'Mysore', 'Guwahati', 'Chandigarh',
    'Patna', 'Ranchi', 'Bhubaneswar', 'Thiruvananthapuram', 'Kochi',
    'Ludhiana', 'Agra', 'Varanasi', 'Meerut', 'Faridabad', 'Ghaziabad',
    'Noida', 'Gurgaon', 'Amritsar', 'Jodhpur', 'Udaipur', 'Allahabad',
    'Kanpur', 'Raipur', 'Dehradun', 'Shimla', 'Panaji', 'Puducherry',
    'Bikaner', 'Ajmer', 'Kolhapur', 'Solapur', 'Jabalpur', 'Gwalior',
    'Ujjain', 'Siliguri', 'Jamshedpur', 'Cuttack', 'Rourkela',
    'Vijayawada', 'Warangal', 'Tirupati', 'Salem', 'Erode', 'Tiruchirappalli',
    'Kozhikode', 'Malappuram', 'Thrissur', 'Kannur', 'Mangalore',
    'Belgaum', 'Hubli', 'Dharwad', 'Shimoga', 'Gulbarga', 'Davangere',
    'Bellary', 'Kurnool', 'Nellore', 'Rajahmundry', 'Kakinada',
    'Anantapur', 'Kadapa', 'Proddatur', 'Hospet', 'Bidar', 'Bijapur',
    'Raichur', 'Sangli', 'Satara', 'Dhule', 'Jalgaon', 'Akola',
    'Amravati', 'Nanded', 'Latur', 'Parbhani', 'Beed', 'Osmanabad',
    'Yavatmal', 'Wardha', 'Chandrapur', 'Bilaspur', 'Korba', 'Bhilai',
    'Durg', 'Rajnandgaon', 'Jagdalpur', 'Ambikapur', 'Raigarh', 'Janjgir',
    'Koraput', 'Jeypore', 'Berhampur', 'Sambalpur', 'Balasore',
    'Bhadrak', 'Baripada', 'Jharsuguda', 'Angul', 'Rourkela',
    'Asansol', 'Durgapur', 'Bardhaman', 'Malda', 'Bahrampur',
    'Krishnanagar', 'Barasat', 'Howrah', 'Barrackpur', 'Haldia',
    'Darjeeling', 'Kalimpong', 'Jalpaiguri', 'Cooch Behar', 'Alipurduar',
    'Agartala', 'Aizawl', 'Imphal', 'Shillong', 'Itanagar', 'Dibrugarh',
    'Jorhat', 'Tezpur', 'Silchar', 'Bongaigaon', 'Tinsukia',
    'Nagaon', 'Diphu', 'Karimganj', 'Dhubri', 'Goalpara',
    'Gandhinagar', 'Anand', 'Bhavnagar', 'Jamnagar', 'Junagadh',
    'Gandhidham', 'Morbi', 'Surendranagar', 'Navsari', 'Vapi',
    'Bharuch', 'Palanpur', 'Mehsana', 'Bhuj', 'Porbandar',
    'Veraval', 'Godhra', 'Dahod', 'Nadiad', 'Ankleshwar',
    'Satna', 'Rewa', 'Sagar', 'Morena', 'Bhind', 'Datia',
    'Shivpuri', 'Guna', 'Ashoknagar', 'Mandsaur', 'Neemuch',
    'Ratlam', 'Dewas', 'Ujjain', 'Shajapur', 'Sehore',
    'Hoshangabad', 'Betul', 'Chhindwara', 'Balaghat', 'Mandla',
    'Seoni', 'Katni', 'Singrauli', 'Sidhi', 'Shahdol',
    'Umaria', 'Anuppur', 'Burhanpur', 'Khandwa', 'Khargone',
    'Badwani', 'Dhar', 'Jhabua', 'Alirajpur', 'Sheopur',
    'Karauli', 'Dholpur', 'Bharatpur', 'Alwar', 'Sikar',
    'Jhunjhunu', 'Churu', 'Bikaner', 'Sri Ganganagar', 'Hanumangarh',
    'Nagaur', 'Jodhpur', 'Jaisalmer', 'Barmer', 'Jalore',
    'Sirohi', 'Pali', 'Rajsamand', 'Udaipur', 'Dungarpur',
    'Banswara', 'Chittorgarh', 'Kota', 'Bundi', 'Sawai Madhopur',
    'Tonk', 'Bhilwara', 'Ajmer', 'Jaipur Rural', 'Dausa',
    'Sikar', 'Jhunjhunu', 'Alwar', 'Bharatpur', 'Dholpur',
    'Karauli', 'Sawai Madhopur', 'Bundi', 'Kota', 'Baran',
    'Jhalawar', 'Pratapgarh', 'Chittorgarh', 'Rajsamand', 'Udaipur',
    'Dungarpur', 'Banswara', 'Sirohi', 'Jalore', 'Pali',
    'Nagaur', 'Jodhpur', 'Jaisalmer', 'Barmer', 'Jalore',
    'Bikaner', 'Sri Ganganagar', 'Hanumangarh', 'Churu', 'Jhunjhunu',
    'Hisar', 'Sirsa', 'Fatehabad', 'Jind', 'Kaithal',
    'Kurukshetra', 'Ambala', 'Yamunanagar', 'Panchkula', 'Karnal',
    'Panipat', 'Sonipat', 'Rohtak', 'Jhajjar', 'Rewari',
    'Mahendragarh', 'Bhiwani', 'Charkhi Dadri', 'Gurgaon', 'Faridabad',
    'Mewat', 'Palwal', 'Ballabgarh', 'Bahadurgarh', 'Sirsa',
    'Amritsar', 'Jalandhar', 'Ludhiana', 'Patiala', 'Bathinda',
    'Mohali', 'Pathankot', 'Firozpur', 'Abohar', 'Malerkotla',
    'Sangrur', 'Barnala', 'Mansa', 'Moga', 'Kapurthala',
    'Tarn Taran', 'Gurdaspur', 'Hoshiarpur', 'Nawanshahr', 'Rupnagar',
    'Fatehgarh Sahib', 'SAS Nagar', 'Chandigarh',
    'Dehradun', 'Haridwar', 'Roorkee', 'Rishikesh', 'Haldwani',
    'Kathgodam', 'Rudrapur', 'Kashipur', 'Ramnagar', 'Nainital',
    'Almora', 'Pithoragarh', 'Mussoorie', 'Tehri', 'Uttarkashi',
    'Srinagar', 'Jammu', 'Leh', 'Kargil', 'Anantnag',
    'Baramulla', 'Sopore', 'Kupwara', 'Pulwama', 'Budgam',
    'Rajouri', 'Poonch', 'Doda', 'Kishtwar', 'Ramban',
    'Reasi', 'Udhampur', 'Kathua', 'Samba', 'Dharamshala',
    'Mandi', 'Kullu', 'Manali', 'Shimla', 'Solan',
    'Baddi', 'Nahan', 'Bilaspur', 'Hamirpur', 'Una',
    'Kangra', 'Chamba',
]

SKILLS_CHOICES = [
    ('customer_service', 'Customer Service'),
    ('sales', 'Sales'),
    ('cash_handling', 'Cash Handling'),
    ('billing_counter', 'Billing / Counter Operations'),
    ('inventory_management', 'Inventory Management'),
    ('product_knowledge', 'Product Knowledge'),
    ('merchandising', 'Merchandising & Display'),
    ('store_operations', 'Store Operations'),
    ('team_management', 'Team Management'),
    ('communication', 'Communication Skills'),
    ('time_management', 'Time Management'),
    ('computer_basics', 'Basic Computer Knowledge'),
    ('language_hindi', 'Hindi Language'),
    ('language_english', 'English Language'),
    ('language_regional', 'Regional Language'),
    ('driving_license', 'Driving License'),
    ('bike_riding', 'Bike Riding'),
    ('delivery', 'Delivery / Logistics'),
    ('cooking', 'Cooking / Food Preparation'),
    ('housekeeping', 'Housekeeping / Cleaning'),
    ('security', 'Security Services'),
    ('tailoring', 'Tailoring / Stitching'),
    ('electrical', 'Electrical Work'),
    ('plumbing', 'Plumbing'),
    ('painting', 'Painting'),
    ('carpentry', 'Carpentry'),
    ('masonry', 'Masonry'),
    ('mechanic', 'Mechanic (Auto/Bike)'),
    ('welding', 'Welding'),
    ('ac_repair', 'AC Repair'),
    ('mobile_repair', 'Mobile Repair'),
    ('computer_repair', 'Computer Repair'),
    ('beautician', 'Beautician / Salon'),
    ('barber', 'Barber'),
    ('tailoring', 'Tailoring'),
    ('embroidery', 'Embroidery'),
    ('accounting', 'Basic Accounting'),
    ('data_entry', 'Data Entry'),
    ('reception', 'Reception / Front Desk'),
    ('call_center', 'Call Center / Telecalling'),
]

# ---------- Custom validators ----------
def validate_mobile(form, field):
    if not re.match(r'^[6-9]\d{9}$', field.data):
        raise ValidationError('Enter a valid 10-digit Indian mobile number.')

def validate_pincode(form, field):
    if not re.match(r'^\d{6}$', field.data):
        raise ValidationError('Pincode must be 6 digits.')

# ---------- Forms ----------
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters.'),
        # add strength validator (as before)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    role = SelectField('I am a', choices=[('jobseeker', 'Jobseeker'), ('employer', 'Employer')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

class ProfileForm(FlaskForm):
    # Name
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    middle_name = StringField('Middle Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])

    # Personal
    dob = DateField('Date of Birth', validators=[DataRequired()], format='%Y-%m-%d')
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired(), Length(max=300)])
    pincode = StringField('Pincode', validators=[DataRequired(), validate_pincode])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State', validators=[DataRequired(), Length(max=100)])
    mobile = StringField('Mobile Number', validators=[DataRequired(), validate_mobile])
    father_husband_name = StringField("Father's / Husband's Name", validators=[DataRequired(), Length(max=100)])

    # Education
    education_level = SelectField('Highest Education', choices=[
        ('Post Graduate', 'Post Graduate'),
        ('Graduate', 'Graduate'),
        ('12th', '12th / Intermediate'),
        ('10th', '10th / Matriculation'),
        ('Others', 'Others')
    ], validators=[DataRequired()])
    education_other = StringField('Please specify your education', validators=[Optional(), Length(max=100)])

    # Work preferences
    preferred_location1 = StringField('Preferred Location 1', validators=[DataRequired(), Length(max=100)])
    preferred_location2 = StringField('Preferred Location 2', validators=[Optional(), Length(max=100)])
    preferred_location3 = StringField('Preferred Location 3', validators=[Optional(), Length(max=100)])
    employment_type = SelectField('Employment Type', choices=[
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Both', 'Both')
    ], validators=[DataRequired()])

    # Skills
    selected_skills = SelectMultipleField('Skills (check all that apply)',
                                         choices=SKILLS_CHOICES,
                                         widget=widgets.ListWidget(prefix_label=False),
                                         option_widget=widgets.CheckboxInput())
    custom_skills = StringField('Other skills (comma separated)', validators=[Optional(), Length(max=200)])

    # Images
    profile_pic = FileField('Profile Picture', validators=[FileAllowed(['jpg','png','jpeg'], 'Images only!')])
    aadhar_card = FileField('Aadhaar Card (not shared with employers)', validators=[FileAllowed(['jpg','png','jpeg'], 'Images only!')])

    submit = SubmitField('Save Profile')