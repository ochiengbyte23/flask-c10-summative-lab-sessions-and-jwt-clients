from app import app
from models import db, User, Note
from faker import Faker
import random

fake = Faker()

with app.app_context():
    
    Note.query.delete()
    User.query.delete()

    users = []
    for _ in range(10):
        user = User(
            username=fake.unique.user_name()
        )
        # simple password for easy testing
        user.password_hash = "password123"
        
        users.append(user)
        db.session.add(user)
    
    db.session.commit()

    for user in users:
        num_notes = random.randint(5, 15)
        
        for _ in range(num_notes):
            n = Note(
                title=fake.sentence(nb_words=4).replace(".", ""),
                content=fake.paragraph(nb_sentences=4),
                user_id=user.id
            )
            db.session.add(n)
    
    db.session.commit()
    

    print("\nTry logging in with one of these usernames:")
    for u in User.query.limit(5).all():
        print(f"- {u.username}")