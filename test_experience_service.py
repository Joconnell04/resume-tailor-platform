"""
Test script for Experience Service
Run with: python manage.py shell < test_experience_service.py
"""
from django.contrib.auth import get_user_model
from experience.services import ExperienceService

User = get_user_model()

# Get the admin user
try:
    user = User.objects.get(username='admin')
    print(f"✓ Found user: {user.username}")
except User.DoesNotExist:
    print("✗ Admin user not found. Please create a superuser first.")
    exit()

# Test 1: Add a work experience
print("\n--- Test 1: Add Work Experience ---")
try:
    work_exp = ExperienceService.add_experience(user, {
        'type': 'work',
        'title': 'Senior Software Engineer',
        'organization': 'TechCorp',
        'location': 'San Francisco, CA',
        'start_date': '2020-01',
        'end_date': '2023-12',
        'current': False,
        'description': 'Led development of cloud infrastructure',
        'skills': ['Python', 'Django', 'AWS', 'Docker'],
        'achievements': [
            'Reduced deployment time by 50%',
            'Mentored 5 junior developers'
        ]
    })
    print(f"✓ Added work experience: {work_exp['title']} at {work_exp['organization']}")
    print(f"  ID: {work_exp['id']}")
except Exception as e:
    print(f"✗ Failed to add work experience: {e}")

# Test 2: Add an education experience
print("\n--- Test 2: Add Education Experience ---")
try:
    edu_exp = ExperienceService.add_experience(user, {
        'type': 'education',
        'title': 'BS Computer Science',
        'organization': 'University of California',
        'location': 'Berkeley, CA',
        'start_date': '2015-09',
        'end_date': '2019-05',
        'current': False,
        'description': 'Graduated with honors',
        'skills': ['Data Structures', 'Algorithms', 'Machine Learning'],
        'achievements': ['GPA: 3.8/4.0', 'Dean\'s List']
    })
    print(f"✓ Added education: {edu_exp['title']} at {edu_exp['organization']}")
    print(f"  ID: {edu_exp['id']}")
except Exception as e:
    print(f"✗ Failed to add education: {e}")

# Test 3: Get all experiences
print("\n--- Test 3: Get All Experiences ---")
try:
    experiences = ExperienceService.get_experiences(user)
    print(f"✓ Found {len(experiences)} experiences")
    for exp in experiences:
        print(f"  - {exp['type']}: {exp['title']} at {exp['organization']}")
except Exception as e:
    print(f"✗ Failed to get experiences: {e}")

# Test 4: Update an experience
print("\n--- Test 4: Update Experience ---")
try:
    if experiences:
        first_exp = experiences[0]
        updated = ExperienceService.update_experience(user, first_exp['id'], {
            'type': first_exp['type'],
            'title': first_exp['title'] + ' (Updated)',
            'organization': first_exp['organization'],
            'location': first_exp.get('location', ''),
            'start_date': first_exp.get('start_date', ''),
            'end_date': first_exp.get('end_date', ''),
            'current': first_exp.get('current', False),
            'description': 'Updated description',
            'skills': first_exp.get('skills', []),
            'achievements': first_exp.get('achievements', [])
        })
        print(f"✓ Updated experience: {updated['title']}")
except Exception as e:
    print(f"✗ Failed to update experience: {e}")

# Test 5: Validation test (should fail)
print("\n--- Test 5: Validation Test (Should Fail) ---")
try:
    ExperienceService.add_experience(user, {
        'type': 'invalid_type',
        'title': '',  # Empty required field
        'organization': 'Test'
    })
    print("✗ Validation should have failed!")
except Exception as e:
    print(f"✓ Validation correctly failed: {e}")

print("\n--- All Tests Complete ---")
