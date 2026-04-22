from flask import Flask, request, session, make_response
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, User, Note

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
            return user.to_dict(), 200
        return {"error": "Unauthorized"}, 401
    
    
    
api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/me')

if __name__ == '__main__':
    app.run(port=5555, debug=True)