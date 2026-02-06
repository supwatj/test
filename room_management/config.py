"""Configuration settings for Room Management Application"""
import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database configuration - support environment variable
DATABASE_URI = os.environ.get('DATABASE_URI', os.path.join(BASE_DIR, 'instance', 'room_management.db'))

# Flask settings - support environment variables
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

# Vacancy calculation default settings
DEFAULT_EARLY_CHECKOUT_DAY = int(os.environ.get('DEFAULT_EARLY_CHECKOUT_DAY', 5))
DEFAULT_LATE_CHECKOUT_DAY = int(os.environ.get('DEFAULT_LATE_CHECKOUT_DAY', 25))

# Report settings
MONTHS_BEFORE = int(os.environ.get('MONTHS_BEFORE', 3))
MONTHS_AFTER = int(os.environ.get('MONTHS_AFTER', 3))
