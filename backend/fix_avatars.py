"""
Fix avatars for existing users in the database
Run with: python fix_avatars.py
"""

from app import create_app, db
from app.models import User

app = create_app('development')

def get_avatar(name, is_female=False):
    """Generate avatar URL from UI Avatars API"""
    bg = 'C084FC' if is_female else '6366F1'  # purple for women, indigo for men
    color = 'ffffff'
    name_encoded = name.replace(' ', '+')
    return f"https://ui-avatars.com/api/?name={name_encoded}&background={bg}&color={color}&size=200&bold=true&rounded=true"

def fix_avatars():
    with app.app_context():
        users = User.query.all()
        updated_count = 0
        
        for user in users:
            if not user.profile_photo:
                bg = 'C084FC' if user.is_female else '6366F1'
                user.profile_photo = get_avatar(user.name, user.is_female)
                updated_count += 1
        
        db.session.commit()
        print(f"✅ Updated {updated_count} user avatars")
        print(f"📊 Total users with avatars: {len([u for u in User.query.all() if u.profile_photo])}")

if __name__ == '__main__':
    fix_avatars()
