-- =============================================================================
-- sample_data.sql — 5 Fictional Student Enquiries + 2 Demo Bookings (SQLite)
-- Safe to rerun: uses INSERT OR IGNORE based on unique phone constraint.
-- Auto-loaded on initial setup by database/db.py
-- =============================================================================

INSERT OR IGNORE INTO student_enquiries
    (id, student_name, phone, normalized_phone, email, student_class, exam_goal, course)
VALUES
    (
        '11111111-aaaa-4444-8888-000000000001',
        'Aarav Sharma',
        '9876543210',
        '9876543210',
        'aarav.sharma@example.com',
        'Class 11',
        'NEET',
        'NEET Foundation'
    ),
    (
        '11111111-aaaa-4444-8888-000000000002',
        'Priya Patel',
        '+91 98765 43211',
        '9876543211',
        'priya.patel@example.com',
        'Class 12',
        'JEE',
        'JEE Advanced'
    ),
    (
        '11111111-aaaa-4444-8888-000000000003',
        'Rohan Mehta',
        '09876543212',
        '9876543212',
        'rohan.mehta@example.com',
        'Class 11',
        'JEE',
        'JEE Main + Advanced'
    ),
    (
        '11111111-aaaa-4444-8888-000000000004',
        'Sneha Reddy',
        '98765-43213',
        '9876543213',
        'sneha.reddy@example.com',
        'Class 12',
        'NEET',
        'NEET Foundation + Biology'
    ),
    (
        '11111111-aaaa-4444-8888-000000000005',
        'Karthik Nair',
        '+91-98765-43214',
        '9876543214',
        'karthik.nair@example.com',
        'Class 11',
        'NEET',
        'NEET Foundation'
    );

INSERT OR IGNORE INTO demo_bookings 
    (id, lead_id, demo_date, demo_time, zoom_link, status)
VALUES (
    '22222222-bbbb-4444-8888-000000000001',
    '11111111-aaaa-4444-8888-000000000001',
    date('now', '+3 days'),
    '3:00 PM',
    'https://zoom.us/j/DEMO-PLACEHOLDER',
    'Booked'
);

INSERT OR IGNORE INTO demo_bookings 
    (id, lead_id, demo_date, demo_time, zoom_link, status)
VALUES (
    '22222222-bbbb-4444-8888-000000000002',
    '11111111-aaaa-4444-8888-000000000002',
    date('now', '+5 days'),
    '5:00 PM',
    'https://zoom.us/j/DEMO-PLACEHOLDER',
    'Attended'
);
