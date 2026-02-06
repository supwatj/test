"""
Room Management Flask Application

Features:
- Room management (CRUD operations)
- Check-in/Check-out recording with reasons
- Vacancy calculation with configurable criteria
- Calendar heatmap and bar chart visualizations
"""
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Room, CheckInOut, VacancySettings
from config import DATABASE_URI, SECRET_KEY, DEBUG, DEFAULT_EARLY_CHECKOUT_DAY, DEFAULT_LATE_CHECKOUT_DAY, MONTHS_BEFORE, MONTHS_AFTER

# Create Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_URI}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True
}

# Initialize database
db.init_app(app)


# ==================== VACANCY CALCULATION LOGIC ====================

def calculate_vacancy_for_month(year, month, settings=None):
    """
    Calculate vacancy for a specific month.
    
    Args:
        year: Year to calculate
        month: Month to calculate (1-12)
        settings: VacancySettings object or None to use default
    
    Returns:
        dict with vacant_count, occupied_count, total_rooms, and daily_breakdown
    """
    if settings is None:
        settings = VacancySettings.get_settings()
    
    # Get all active rooms
    total_rooms = Room.query.filter_by(is_active=True).count()
    if total_rooms == 0:
        return {
            'vacant_count': 0,
            'occupied_count': 0,
            'total_rooms': 0,
            'daily_breakdown': []
        }
    
    # Get check-out records for this month
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)
    
    checkouts = CheckInOut.query.filter(
        CheckInOut.check_out_date >= month_start,
        CheckInOut.check_out_date <= month_end
    ).all()
    
    # Calculate vacancy based on check-out dates
    vacant_count = 0
    occupied_count = 0
    partial_count = 0
    not_vacant_count = 0
    
    daily_breakdown = []
    
    for day in range(1, month_end.day + 1):
        current_date = date(year, month, day)
        
        # Count checkouts on this day
        day_checkouts = [c for c in checkouts if c.check_out_date == current_date]
        
        # Determine vacancy status based on day
        status = 'unknown'
        vacant_today = 0
        occupied_today = 0
        
        for checkout in day_checkouts:
            if checkout.day < settings.early_checkout_day:
                vacant_today += 1
            elif checkout.day >= settings.late_checkout_day:
                occupied_today += 1
            else:
                # Between early and late - partially vacant
                occupied_today += 1
        
        if day < settings.early_checkout_day:
            status = 'vacant'
            vacant_today = total_rooms
            occupied_today = 0
        elif day >= settings.late_checkout_day:
            status = 'not_vacant'
            vacant_today = 0
            occupied_today = total_rooms
        else:
            status = 'partial'
            # Partial - use actual checkouts to determine
        
        daily_breakdown.append({
            'day': day,
            'date': current_date.isoformat(),
            'status': status,
            'vacant': vacant_today if vacant_today > 0 else (total_rooms if status == 'vacant' else 0),
            'occupied': occupied_today if occupied_today > 0 else (total_rooms if status == 'not_vacant' else 0)
        })
        
        if status == 'vacant':
            vacant_count += 1
        elif status == 'not_vacant':
            not_vacant_count += 1
        else:
            partial_count += 1
    
    return {
        'vacant_count': vacant_count,
        'occupied_count': occupied_count + not_vacant_count,
        'partial_count': partial_count,
        'total_rooms': total_rooms,
        'daily_breakdown': daily_breakdown
    }


def get_six_month_vacancy_data():
    """
    Get vacancy data for 6 months (3 before, current, 3 after).
    
    Returns:
        dict with bar_chart_data and heatmap_data
    """
    settings = VacancySettings.get_settings()
    
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    # Calculate 6 months: 3 before, current, 3 after
    months = []
    for i in range(-MONTHS_BEFORE, MONTHS_AFTER + 1):
        target_month = current_month + i
        target_year = current_year
        
        while target_month < 1:
            target_month += 12
            target_year -= 1
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        month_data = calculate_vacancy_for_month(target_year, target_month, settings)
        
        month_name = date(target_year, target_month, 1).strftime('%B %Y')
        
        months.append({
            'name': month_name,
            'year': target_year,
            'month': target_month,
            'short_name': date(target_year, target_month, 1).strftime('%b %Y'),
            'vacant_days': month_data['vacant_count'],
            'occupied_days': month_data['occupied_count'],
            'partial_days': month_data.get('partial_count', 0),
            'total_rooms': month_data['total_rooms'],
            'daily_breakdown': month_data['daily_breakdown']
        })
    
    # Prepare bar chart data
    bar_chart_data = {
        'labels': [m['short_name'] for m in months],
        'vacant': [m['vacant_days'] for m in months],
        'occupied': [m['occupied_days'] for m in months],
        'partial': [m['partial_days'] for m in months]
    }
    
    # Prepare heatmap data
    heatmap_data = {
        'months': months,
        'total_rooms': months[0]['total_rooms'] if months else 0,
        'early_day': settings.early_checkout_day,
        'late_day': settings.late_checkout_day
    }
    
    return {
        'bar_chart': bar_chart_data,
        'heatmap': heatmap_data,
        'settings': settings.to_dict()
    }


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Dashboard with overview stats"""
    total_rooms = Room.query.filter_by(is_active=True).count()
    
    # Get currently occupied rooms
    occupied_rooms = CheckInOut.query.filter(
        CheckInOut.check_out_date == None
    ).count()
    
    # Get recent check-ins/outs
    recent_records = CheckInOut.query.order_by(
        CheckInOut.created_at.desc()
    ).limit(10).all()
    
    return render_template('index.html',
                         total_rooms=total_rooms,
                         occupied_rooms=occupied_rooms,
                         vacant_rooms=total_rooms - occupied_rooms,
                         recent_records=recent_records)


# ==================== ROOM ROUTES ====================

@app.route('/rooms')
def rooms():
    """List all rooms"""
    rooms = Room.query.filter_by(is_active=True).all()
    all_rooms = Room.query.all()
    return render_template('rooms.html', rooms=rooms, all_rooms=all_rooms)


@app.route('/rooms/add', methods=['POST'])
def add_room():
    """Add a new room"""
    room_number = request.form.get('room_number')
    room_type = request.form.get('room_type', 'Standard')
    floor = request.form.get('floor', 1)
    
    try:
        floor = int(floor)
    except ValueError:
        floor = 1
    
    # Check if room number already exists
    existing = Room.query.filter_by(room_number=room_number).first()
    if existing:
        flash(f'Room {room_number} already exists!', 'danger')
        return redirect(url_for('rooms'))
    
    new_room = Room(
        room_number=room_number,
        room_type=room_type,
        floor=floor
    )
    db.session.add(new_room)
    db.session.commit()
    
    flash(f'Room {room_number} added successfully!', 'success')
    return redirect(url_for('rooms'))


@app.route('/rooms/<int:room_id>/edit', methods=['POST'])
def edit_room(room_id):
    """Edit an existing room"""
    room = Room.query.get_or_404(room_id)
    
    room.room_number = request.form.get('room_number')
    room.room_type = request.form.get('room_type', room.room_type)
    floor = request.form.get('floor', room.floor)
    
    try:
        room.floor = int(floor)
    except ValueError:
        pass
    
    db.session.commit()
    flash(f'Room {room.room_number} updated successfully!', 'success')
    return redirect(url_for('rooms'))


@app.route('/rooms/<int:room_id>/delete')
def delete_room(room_id):
    """Soft delete a room (set is_active=False)"""
    room = Room.query.get_or_404(room_id)
    room.is_active = False
    db.session.commit()
    
    flash(f'Room {room.room_number} deactivated!', 'warning')
    return redirect(url_for('rooms'))


# ==================== CHECK-IN/CHECK-OUT ROUTES ====================

@app.route('/check-in', methods=['GET', 'POST'])
def check_in():
    """Check-in a room"""
    if request.method == 'POST':
        room_id = request.form.get('room_id')
        check_in_date = datetime.strptime(request.form.get('check_in_date'), '%Y-%m-%d').date()
        
        # Check if room is already checked in
        existing_checkin = CheckInOut.query.filter(
            CheckInOut.room_id == room_id,
            CheckInOut.check_out_date == None
        ).first()
        
        if existing_checkin:
            flash('This room is already checked in!', 'danger')
            return redirect(url_for('check_in'))
        
        new_checkin = CheckInOut(
            room_id=room_id,
            check_in_date=check_in_date
        )
        db.session.add(new_checkin)
        db.session.commit()
        
        room = Room.query.get(room_id)
        flash(f'Room {room.room_number} checked in successfully!', 'success')
        return redirect(url_for('index'))
    
    # GET request - show form
    rooms = Room.query.filter_by(is_active=True).all()
    
    # Get available rooms (not currently checked in)
    occupied_room_ids = db.session.query(CheckInOut.room_id).filter(
        CheckInOut.check_out_date == None
    ).all()
    occupied_ids = [r[0] for r in occupied_room_ids]
    
    available_rooms = [r for r in rooms if r.id not in occupied_ids]
    
    return render_template('check_in.html', available_rooms=available_rooms)


@app.route('/check-out/<int:room_id>', methods=['GET', 'POST'])
def check_out(room_id):
    """Check-out a room"""
    room = Room.query.get_or_404(room_id)
    
    # Get current check-in record
    current_checkin = CheckInOut.query.filter(
        CheckInOut.room_id == room_id,
        CheckInOut.check_out_date == None
    ).first()
    
    if not current_checkin:
        flash(f'Room {room.room_number} is not currently checked in!', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        check_out_date = datetime.strptime(request.form.get('check_out_date'), '%Y-%m-%d').date()
        reason = request.form.get('reason', '')
        
        current_checkin.check_out_date = check_out_date
        current_checkin.reason = reason
        
        db.session.commit()
        
        flash(f'Room {room.room_number} checked out successfully!', 'success')
        return redirect(url_for('index'))
    
    # GET request - show form
    return render_template('check_out.html', 
                         room=room, 
                         current_checkin=current_checkin,
                         today=date.today().isoformat())


# ==================== VACANCY REPORT ROUTES ====================

@app.route('/vacancy-report')
def vacancy_report():
    """Vacancy report page with heatmap and bar chart"""
    vacancy_data = get_six_month_vacancy_data()
    
    return render_template('vacancy_report.html',
                         vacancy_data=vacancy_data,
                         page_title='Vacancy Report')


@app.route('/api/vacancy-data')
def api_vacancy_data():
    """API endpoint for vacancy data (JSON)"""
    vacancy_data = get_six_month_vacancy_data()
    return jsonify(vacancy_data)


# ==================== SETTINGS ROUTES ====================

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Settings page for vacancy criteria"""
    settings = VacancySettings.get_settings()
    
    if request.method == 'POST':
        early_day = request.form.get('early_checkout_day', 5)
        late_day = request.form.get('late_checkout_day', 25)
        
        try:
            early_day = int(early_day)
            late_day = int(late_day)
            
            if early_day < 1 or early_day > 28:
                flash('Early checkout day must be between 1 and 28', 'danger')
            elif late_day < 1 or late_day > 31:
                flash('Late checkout day must be between 1 and 31', 'danger')
            elif early_day >= late_day:
                flash('Early checkout day must be before late checkout day', 'danger')
            else:
                settings.early_checkout_day = early_day
                settings.late_checkout_day = late_day
                db.session.commit()
                flash('Settings updated successfully!', 'success')
                
        except ValueError:
            flash('Please enter valid numbers', 'danger')
    
    return render_template('settings.html', settings=settings)


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error=error), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error=error), 500


# ==================== DATABASE INITIALIZATION ====================

def init_database():
    """Initialize the database with default data"""
    with app.app_context():
        db.create_all()
        
        # Create default settings if none exist
        if not VacancySettings.query.first():
            default_settings = VacancySettings(
                early_checkout_day=DEFAULT_EARLY_CHECKOUT_DAY,
                late_checkout_day=DEFAULT_LATE_CHECKOUT_DAY
            )
            db.session.add(default_settings)
        
        # Create sample rooms if none exist
        if not Room.query.first():
            sample_rooms = [
                Room(room_number='101', room_type='Standard', floor=1),
                Room(room_number='102', room_type='Standard', floor=1),
                Room(room_number='103', room_type='Deluxe', floor=1),
                Room(room_number='201', room_type='Standard', floor=2),
                Room(room_number='202', room_type='Deluxe', floor=2),
                Room(room_number='203', room_type='Suite', floor=2),
                Room(room_number='301', room_type='Standard', floor=3),
                Room(room_number='302', room_type='Suite', floor=3),
            ]
            for room in sample_rooms:
                db.session.add(room)
        
        db.session.commit()
        print("Database initialized successfully!")


if __name__ == '__main__':
    import os
    
    # Create instance directory if it doesn't exist
    os.makedirs('instance', exist_ok=True)
    
    # Initialize database
    init_database()
    
    # Run the application
    app.run(debug=DEBUG, host='0.0.0.0', port=5000)
