# Room Management Flask Application Architecture

## Overview
A Flask-based web application for managing room occupancy with vacancy tracking and reporting using dual visualization: calendar heatmap + bar chart summary.

## Technology Stack
- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML, Bootstrap 5
- **Visualizations**: 
  - Custom Calendar Heatmap (CSS Grid + JavaScript)
  - Chart.js Bar Chart for summary
- **Template Engine**: Jinja2

## Project Structure

```
room_management/
├── app.py                    # Main Flask application
├── config.py                 # Configuration settings
├── models.py                 # Database models
├── requirements.txt          # Python dependencies
├── static/
│   ├── css/
│   │   └── styles.css        # Custom styles including heatmap
│   └── js/
│       ├── heatmap.js        # Calendar heatmap rendering
│       └── chart.js          # Bar chart rendering
└── templates/                # HTML templates
    ├── base.html             # Base template
    ├── index.html            # Dashboard
    ├── rooms.html            # Room management
    ├── check_in.html         # Check-in form
    ├── check_out.html        # Check-out form
    ├── vacancy_report.html   # Vacancy report with heatmap + bar chart
    └── settings.html         # Settings page
```

## Database Schema

### Room Model
```python
class Room:
    - id: Integer, Primary Key
    - room_number: String(20), Unique
    - room_type: String(50)  # e.g., Single, Double, Suite
    - floor: Integer
    - is_active: Boolean, default True
    - created_at: DateTime
```

### CheckInOut Model
```python
class CheckInOut:
    - id: Integer, Primary Key
    - room_id: Foreign Key to Room
    - check_in_date: Date
    - check_out_date: Date (nullable)
    - reason: String(255)  # Reason for check-out
    - created_at: DateTime
```

### VacancySettings Model
```python
class VacancySettings:
    - id: Integer, Primary Key
    - early_checkout_day: Integer, default 5   # Day before which checkout = vacant
    - late_checkout_day: Integer, default 25   # Day after which checkout = not vacant
    - created_at: DateTime
    - updated_at: DateTime
```

## Vacancy Calculation Logic

### Rules
1. **Vacant**: Checkout date < configured early day (default: 5th)
2. **Not Vacant**: Checkout date >= configured late day (default: 25th)
3. **Partially Vacant**: Checkout dates between early and late days

### Calculation Algorithm
For each month in the 6-month period (3 before, 3 after):
1. Get all rooms
2. For each room, check check-out dates in that month
3. Apply vacancy rules based on check-out day
4. Calculate vacant rooms = total rooms - occupied rooms

## Dual Visualization Design

### 1. Calendar Heatmap
**Purpose**: Show daily vacancy patterns and trends

**Layout**:
- **Columns**: 6 months (3 past, current, 3 future)
- **Rows**: Days of month (1-31)
- **Cells**: Color-coded by vacancy status

**Color Scheme**:
| Status | Color | Description |
|--------|-------|-------------|
| Occupied | 🔴 Red | Room is occupied |
| Vacant | 🟢 Green | Checkout before early day |
| Partially Vacant | 🟡 Yellow | Checkout between early and late days |
| Not Vacant | 🟠 Orange | Checkout after late day |
| Future | ⬜ Gray | No data or future dates |

**Cell Content**: Vacant rooms / Total rooms (e.g., "8/15")

### 2. Bar Chart Summary
**Purpose**: Quick comparison of monthly vacancy totals

**Chart.js Configuration**:
```javascript
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['Nov 2025', 'Dec 2025', 'Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026'],
        datasets: [{
            label: 'Vacant Rooms',
            data: [8, 7, 12, 9, 10, 8],
            backgroundColor: 'rgba(40, 167, 69, 0.8)',
            borderColor: 'rgba(40, 167, 69, 1)',
            borderWidth: 1
        }, {
            label: 'Occupied Rooms',
            data: [7, 8, 3, 6, 5, 7],
            backgroundColor: 'rgba(220, 53, 69, 0.8)',
            borderColor: 'rgba(220, 53, 69, 1)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        scales: {
            x: { stacked: true },
            y: { stacked: true, beginAtZero: true }
        }
    }
});
```

**Stacked Bar Chart**:
- Shows vacant vs occupied breakdown per month
- Color-coded bars matching heatmap legend
- Interactive tooltips with exact counts

## API Endpoints

### Rooms
- `GET /rooms` - List all rooms
- `POST /rooms` - Create new room
- `GET /rooms/<id>` - Get room details
- `PUT /rooms/<id>` - Update room
- `DELETE /rooms/<id>` - Delete room

### Check-in/Check-out
- `GET /check-in` - Check-in form
- `POST /check-in` - Record check-in
- `GET /check-out/<room_id>` - Check-out form
- `POST /check-out/<room_id>` - Record check-out with reason

### Reports
- `GET /vacancy-report` - Vacancy report with heatmap + bar chart
- `GET /api/vacancy-data` - JSON data for both visualizations

### Settings
- `GET /settings` - Settings page
- `POST /settings` - Update vacancy criteria

## Frontend Features

### Dashboard (index.html)
- Quick stats overview
- Link to main functions
- Current occupancy status
- Mini bar chart preview

### Vacancy Report Page (vacancy_report.html)
**Top Section - Bar Chart Summary**:
- Stacked bar chart showing monthly totals
- Legend matching heatmap colors
- Hover tooltips with detailed data

**Bottom Section - Calendar Heatmap**:
- Full 6-month grid
- Day-by-day breakdown
- Interactive cells with room details
- Responsive layout

### Settings Page
- Form to modify vacancy calculation criteria
- Early checkout day setting
- Late checkout day setting
- Live preview of how changes affect calculations

## Data Structure for Dual Visualization

```json
{
  "heatmap": {
    "months": [
      {
        "name": "November 2025",
        "year": 2025,
        "month": 11,
        "days": [
          {"day": 1, "status": "vacant", "vacantCount": 8, "occupiedCount": 7},
          {"day": 2, "status": "occupied", "vacantCount": 6, "occupiedCount": 9},
          ...
        ]
      },
      ...
    ]
  },
  "barchart": {
    "labels": ["Nov 2025", "Dec 2025", "Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026"],
    "vacant": [8, 7, 12, 9, 10, 8],
    "occupied": [7, 8, 3, 6, 5, 7]
  },
  "summary": {
    "totalRooms": 15,
    "earlyDay": 5,
    "lateDay": 25,
    "currentVacancyRate": 0.53
  }
}
```

## Implementation Steps

1. **Project Setup**
   - Create virtual environment
   - Install dependencies (Flask, Flask-SQLAlchemy, Flask-Bootstrap, Chart.js CDN)
   - Initialize project structure

2. **Database Models**
   - Define all models in models.py
   - Create database initialization script

3. **Core Routes**
   - Implement all API endpoints
   - Add input validation
   - Handle errors gracefully

4. **Vacancy Calculation Service**
   - Implement calculation logic
   - Generate data for both heatmap and bar chart
   - Handle edge cases

5. **Bar Chart Implementation**
   - Include Chart.js via CDN
   - Create stacked bar chart configuration
   - Add responsive styling

6. **Heatmap Visualization**
   - Create CSS Grid layout
   - Implement color scheme
   - Add JavaScript for interactivity

7. **Frontend Development**
   - Create base template with navigation
   - Build all page templates
   - Integrate both visualizations

8. **Testing**
   - Test database operations
   - Test vacancy calculation logic
   - Verify both visualizations render correctly
   - Test settings changes

## Vacancy Calculation Example

For February 2026 with default settings:
- Room A: Checked out on Feb 3 → Vacant (before 5th) → Green
- Room B: Checked out on Feb 15 → Partial (between 5th and 25th) → Yellow
- Room C: Checked out on Feb 28 → Not vacant (after 25th) → Orange
- Room D: Still occupied → Occupied → Red

**Bar Chart Data for Feb 2026**:
- Vacant: 1, Occupied: 1, Partial: 1, Not Vacant: 1

## Responsive Design

### Desktop
- Side-by-side layout: Bar chart (top), Heatmap (bottom)
- Full grid visible
- Detailed tooltips

### Tablet
- Stacked layout
- Simplified heatmap
- Collapsible sections

### Mobile
- Single column
- Horizontal scroll for heatmap
- Touch-friendly interactions

## Next Steps

Ready to implement with these specifications:
- SQLite database with SQLAlchemy
- Calendar heatmap + stacked bar chart dual visualization
- No authentication required
- Basic room information (number, type, floor)
- Configurable vacancy calculation criteria
