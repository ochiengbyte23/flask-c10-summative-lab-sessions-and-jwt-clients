from flask import Flask, request, session, make_response
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, User, Note
from flask_cors import CORS
import os
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False, 
)

app.secret_key = os.environ.get('SECRET_KEY') or 'dev-secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, supports_credentials=True)
migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)

class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            user = User(username=data.get('username'))
            user.password_hash = data.get('password')
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return user.to_dict(), 201
        except IntegrityError:
            db.session.rollback() # Good practice to rollback the failed transaction
            return {"error": "That username is already taken. Please try another."}, 422
        except Exception as e:
            return {"errors": [str(e)]}, 422
        
class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(username=data.get('username')).first()
        if user and user.authenticate(data.get('password')):
            session['user_id'] = user.id
            return user.to_dict(), 200
        return {"error": "Invalid username or password"}, 401

class Logout(Resource):
    def delete(self):
        session.pop('user_id', None)
        return {}, 204
    
class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.filter_by(id=user_id).first()
            if user:
                return user.to_dict(), 200
        return {"error": "Unauthorized"}, 401
    
    
    
    
class Notes(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Login required"}, 401
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = 10
        notes_query = Note.query.filter_by(user_id=user_id).paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            "notes": [n.to_dict() for n in notes_query.items],
            "total": notes_query.total,
            "current_page": notes_query.page
        }, 200

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Login required"}, 401
        
        data = request.get_json()
        try:
            new_note = Note(title=data['title'], content=data['content'], user_id=user_id)
            db.session.add(new_note)
            db.session.commit()
            return new_note.to_dict(), 201
        except Exception as e:
            return {"errors": [str(e)]}, 422

class NoteById(Resource):
    def patch(self, id):
        user_id = session.get('user_id')
        note = Note.query.filter_by(id=id, user_id=user_id).first()
        if not note:
            return {"error": "Note not found"}, 404
        
        data = request.get_json()
        for attr in data:
            if hasattr(note, attr):
                setattr(note, attr, data[attr])
        db.session.commit()
        return note.to_dict(), 200

    def delete(self, id):
        user_id = session.get('user_id')
        note = Note.query.filter_by(id=id, user_id=user_id).first()
        if not note:
            return {"error": "Note not found"}, 404
        
        db.session.delete(note)
        db.session.commit()
        return {}, 204
    
    
    
api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/me')
api.add_resource(Notes, '/notes')
api.add_resource(NoteById, '/notes/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)