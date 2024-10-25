from haru import Haru, Request
from haru.middlewares import LoggerMiddleware
from haru.sql import Model, Column, Integer, String, SessionManager, Base, get_session, get_engine


class User(Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(length=50), nullable=False)
    password = Column(String(length=100), nullable=False)


engine = get_engine('sqlite:///test.db')
Base.metadata.create_all(engine)
session = get_session(engine)

app = Haru(__name__)
app.add_middleware(LoggerMiddleware())


@app.route('/')
def index(req: Request):
    print(req.method)
    return 'Hello, world!'


@app.route('/user/<username:str>', methods=['GET', 'POST'])
def user(req: Request):
    if req.method == 'GET':
        return f'Hello, {req.params["username"]}!'
    else:
        with SessionManager(session) as s:
            if 'password' not in req.form:
                return 'Password is required.', 400
            new_user = User(name=req.params["username"], password=req.form["password"])
            s.add(new_user)
            return f'User: {new_user.name} created successfully!'


if __name__ == '__main__':
    app.run()
