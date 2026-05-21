#!/usr/bin/env python3
"""
DigitalForge Marketplace - Entry Point
Production-ready WSGI application runner
"""
import os
from app import create_app, db
from app.models import Category, User

# Create app instance
app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.cli.command('init-db')
def init_db():
    """Initialize database with default categories."""
    with app.app_context():
        db.create_all()

        # Add default categories if none exist
        if not Category.query.first():
            default_categories = [
                {'name': 'Website Templates', 'slug': 'templates', 'icon': 'layout',
                 'description': 'HTML, CSS, and JS templates'},
                {'name': 'WordPress Themes', 'slug': 'wordpress', 'icon': 'type',
                 'description': 'WordPress themes and plugins'},
                {'name': 'AI Tools', 'slug': 'ai-tools', 'icon': 'brain',
                 'description': 'AI models, prompts, and tools'},
                {'name': 'Scripts & Code', 'slug': 'scripts', 'icon': 'code',
                 'description': 'Software scripts and source code'},
                {'name': 'Mobile Apps', 'slug': 'mobile', 'icon': 'smartphone',
                 'description': 'iOS and Android applications'},
                {'name': 'Figma Kits', 'slug': 'figma', 'icon': 'figma',
                 'description': 'UI/UX design systems and kits'},
                {'name': '3D Assets', 'slug': '3d', 'icon': 'box',
                 'description': '3D models and animations'},
                {'name': 'Video & Audio', 'slug': 'media', 'icon': 'film',
                 'description': 'Video templates and audio assets'},
            ]

            for cat_data in default_categories:
                category = Category(**cat_data)
                db.session.add(category)

            db.session.commit()
            print('Database initialized with default categories.')
        else:
            print('Categories already exist.')


@app.cli.command('create-admin')
def create_admin():
    """Create admin user from command line."""
    import getpass

    with app.app_context():
        email = input('Admin email: ').strip()
        username = input('Admin username: ').strip()
        password = getpass.getpass('Password: ')

        if User.query.filter_by(email=email).first():
            print('Email already exists!')
            return

        admin = User(
            email=email,
            username=username,
            is_admin=True,
            is_verified=True,
            is_seller=True
        )
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()
        print(f'Admin user {username} created successfully!')


if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)