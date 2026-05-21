"""
DigitalForge Marketplace - WTForms Definitions
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, DecimalField, SelectField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length, NumberRange, URL, Optional, EqualTo
from app.models import Category


class LoginForm(FlaskForm):
    """User login form"""
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, max=100)
    ])
    remember = BooleanField('Remember Me')


class RegisterForm(FlaskForm):
    """User registration form"""
    full_name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    become_seller = BooleanField('I want to sell products')


class ProductUploadForm(FlaskForm):
    """Product upload form for sellers"""
    title = StringField('Product Title', validators=[
        DataRequired(),
        Length(min=5, max=150)
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=20, max=5000)
    ])
    short_description = StringField('Short Description (optional)', validators=[
        Optional(),
        Length(max=300)
    ])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    price = DecimalField('Price (USDC)', validators=[
        DataRequired(),
        NumberRange(min=0.99, max=9999.99, message='Price must be between 0.99 and 9999.99')
    ])
    tags = StringField('Tags (comma separated)', validators=[
        Optional(),
        Length(max=255)
    ])
    demo_url = StringField('Demo URL (optional)', validators=[
        Optional(),
        URL(message='Please enter a valid URL')
    ])

    # File fields
    product_file = FileField('Product File (ZIP)', validators=[
        FileRequired(),
        FileAllowed(['zip', 'rar', '7z'], 'Only ZIP/RAR/7Z files allowed')
    ])

    preview_image_1 = FileField('Primary Preview Image', validators=[
        FileRequired(),
        FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only')
    ])
    preview_image_2 = FileField('Preview Image 2', validators=[
        Optional(),
        FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only')
    ])
    preview_image_3 = FileField('Preview Image 3', validators=[
        Optional(),
        FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only')
    ])
    preview_image_4 = FileField('Preview Image 4', validators=[
        Optional(),
        FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only')
    ])
    preview_image_5 = FileField('Preview Image 5', validators=[
        Optional(),
        FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only')
    ])

    def __init__(self, *args, **kwargs):
        super(ProductUploadForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in
                                    Category.query.filter_by(is_active=True).order_by(Category.display_order).all()]


class ReviewForm(FlaskForm):
    """Product review form"""
    rating = SelectField('Rating', choices=[
        (5, '5 - Excellent'),
        (4, '4 - Very Good'),
        (3, '3 - Good'),
        (2, '2 - Fair'),
        (1, '1 - Poor')
    ], coerce=int, validators=[DataRequired()])
    comment = TextAreaField('Review (optional)', validators=[
        Optional(),
        Length(max=1000)
    ])


class ProfileForm(FlaskForm):
    """User profile edit form"""
    full_name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    bio = TextAreaField('Bio', validators=[
        Optional(),
        Length(max=500)
    ])
    wallet_address = StringField('Wallet Address (for crypto payouts)', validators=[
        Optional(),
        Length(min=42, max=42, message='Invalid Ethereum address length')
    ])
    avatar = FileField('Profile Picture', validators=[
        Optional(),
        FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only')
    ])