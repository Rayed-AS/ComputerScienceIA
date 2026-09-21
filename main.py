#This is where I will create the routes for my different pages
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, RadioField, TextAreaField, FileField
from wtforms.validators import DataRequired, Length, Email
from flask_wtf.file import FileRequired, FileAllowed

#Setting up flask website
app = Flask(__name__)
app.config['SECRET_KEY'] = 'my_super_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///research.db'

#Creating database
db = SQLAlchemy(app)

#Creating tables for database
class User(db.Model):
    #Creating fields
    id = db.Column(db.Integer, primary_key = True, autoincrement = True, unique = True)
    email = db.Column(db.String, unique = True, nullable = False)
    password = db.Column(db.String(20), nullable = False)
    type = db.Column(db.String, nullable = False)
    opportunities = db.relationship("Opportunity", backref = "professor", lazy = "dynamic")
    applications = db.relationship("Application", backref = "student", lazy = "dynamic")

class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement = True, unique = True)
    name = db.Column(db.String, nullable = False)
    professor_name = db.Column(db.String, nullable = False)
    institute = db.Column(db.String, nullable = False)
    requirements = db.Column(db.String, nullable = False)
    description = db.Column(db.String(1000), nullable = False)
    location = db.Column(db.String, nullable = False)
    image = db.Column(db.String, nullable = False)
    prof_ID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    applications = db.relationship('Application', backref = 'opportunity', cascade = 'all, delete-orphan')

class Application(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement = True, unique = True)
    email = db.Column(db.String, nullable=False)
    institute = db.Column(db.String, nullable=False)
    content = db.Column(db.String(1000), nullable = False)
    level = db.Column(db.String, nullable = False)
    status = db.Column(db.String, nullable = False)
    student_ID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    opportunity_ID = db.Column(db.Integer, db.ForeignKey('opportunity.id'), nullable = False)

#Creating routes for web pages
@app.route('/student-home')
def student_home():
    return render_template("student-home.html")

@app.route('/professor-home')
def professor_home():
    return render_template("professor-home.html")

@app.route('/view-applications')
def view_applications():
    #Getting the current user who is logged in based on the stored session ID
    user = User.query.filter_by(id = session.get('user_id')).first()
    #Getting the applications made by the user
    applications = user.applications
    count = 0
    #Iterating through each individual application in the list
    for application in user.applications:
        #Incrementing count
        count +=1
    #Checking whether the number of applications exceeds the current amount
    if count <= 50:
        #Accounting for error associated with the user having no applications and clicking view applications
        try:
            return render_template("view-applications.html", applications = user.applications)
        except AttributeError:
            return error("No Applications Available")
    #If user has maximum applications then they must go back and delete some before viewing
    else:
        return error("You have reached the maximum amount of applications (50). Please delete a few applications and try again.")

@app.route('/error')
#An extensible error page that is used to display different errors
def error(encountered_error):
    return render_template('error.html', print = encountered_error)

@app.route('/view-applications-professor')
def view_applications_professor():
    Opp = Opportunity.query.filter_by(prof_ID = session.get('user_id')).first()
    if Opp:
        return render_template("view-applications-professor.html", applications = Application.query.filter_by(opportunity_ID = Opp.id))
    else:
        return error("No Opportunities to display Applications for")

@app.route('/view-opportunities-professor', methods =['GET'])
def view_opportunities_professor():
    search_query = request.args.get('query', '')
    if search_query != "":
        opportunities = Opportunity.query.all()
        for op in opportunities:
            if search_query in op.name:
                return render_template("view-opportunities-professor.html", opportunities = [op])
    return render_template("view-opportunities-professor.html", opportunities = Opportunity.query.all())

@app.route('/view-opportunities', methods = ['GET'])
def view_opportunities():
    return render_template("view-opportunities.html", opportunities = Opportunity.query.all())

class ApplicationForm(FlaskForm):
    institute = StringField('Educational Institute Name', validators = [DataRequired()])
    text = TextAreaField('Why are you the best candidate?', validators = [DataRequired(), Length(100, 1000)])
    level = RadioField('Educational level', choices = [("HighSchool", "I am in high-school"), ("Undergraduate", "I am an undergraduate")])
    submit = SubmitField("submit")

@app.route('/application-form/<int:op_id>', methods = ['GET', 'POST'])
def application_form(op_id):
    Apply = ApplicationForm()
    user = User.query.filter_by(id=session.get('user_id')).first()
    applications = user.applications
    for application in applications:
        if application.opportunity_ID == op_id:
            return error("You already submitted an application to this opportunity")
    if Apply.validate_on_submit():
        institute = Apply.institute.data
        content = Apply.text.data
        level = Apply.level.data
        NewApplication = Application(email = user.email, institute = institute, content = content, level = level, status = "Waiting", student_ID = user.id,opportunity_ID = op_id)
        db.session.add(NewApplication)
        db.session.commit()
        return redirect(url_for("student_home"))
    else:
        print(Apply.errors)
        if user.type == "Student":
            return render_template('application-form.html', form = Apply)
        else:
            return render_template('professor-home.html')

@app.route('/learn-more/<int:op_id>')
def learn_more(op_id):
    return render_template('learn-more.html', opportunity = Opportunity.query.filter_by(id=op_id).first())

@app.route('/learn-more-professor/<int:op_id>')
def learn_more_professor(op_id):
    return render_template('learn-more-professor.html', opportunity=Opportunity.query.filter_by(id=op_id).first())

@app.route('/status-change/<int:app_id>/<action>')
def status_change(app_id, action):
    App = Application.query.filter_by(id = app_id).first()
    App.status = action
    db.session.commit()
    return redirect(url_for('professor_home'))

@app.route('/delete/<int:op_id>')
def delete(op_id):
    opportunity = Opportunity.query.filter_by(id=op_id).first()
    user = User.query.filter_by(id=session.get('user_id')).first()
    if session.get('user_id') == opportunity.prof_ID:
        db.session.delete(opportunity)
        db.session.commit()
        
    if user.type == "Professor":
        return redirect(url_for('view_opportunities_professor'))
    else:
        return redirect(url_for('view_opportunities'))

@app.route('/delete-app/<int:app_id>')
def delete_app(app_id):
    application = Application.query.filter_by(id=app_id).first()
    user = User.query.filter_by(id=session.get('user_id')).first()
    if session.get('user_id') == application.student_ID:
        db.session.delete(application)
        db.session.commit()

    if user.type == "Professor":
        return redirect(url_for('view_opportunities_professor'))
    else:
        return redirect(url_for('view_opportunities'))

class OpportunityForm(FlaskForm):
    name = StringField("Opportunity Name", validators = [DataRequired()])
    professor_name = StringField("Professor Name", validators = [DataRequired()])
    institute = StringField("Institute", validators = [DataRequired()])
    requirements = TextAreaField("Requirements (Separate individual requirements with a colon)", validators = [DataRequired()])
    description = TextAreaField("Description", validators = [DataRequired(), Length(100, 1000)])
    location = RadioField("Where will it take place?", choices = [("On Campus", "On Campus"), ("Online", "Online")], validators = [DataRequired()])
    image = FileField("Display Image (JPG, PNG)", validators = [FileRequired(), FileAllowed(['jpg', 'png'], "JPG or PNG only")])
    submit = SubmitField("Publish")

@app.route('/publish-opportunity', methods = ['GET', 'POST'])
def publish_opportunity():
    OppForm = OpportunityForm()
    user = User.query.filter_by(id = session.get('user_id')).first()
    if  Opportunity.query.filter_by(id = user.id).first():
        return error("You already have an ongoing opportunity. Delete your previous opportunity to publish a new one.")
    if OppForm.validate_on_submit():
        name = OppForm.name.data
        professor_name = OppForm.professor_name.data
        institute = OppForm.institute.data
        requirements = OppForm.requirements.data
        description = OppForm.description.data
        location = OppForm.location.data
        image = OppForm.image.data.filename
        OppForm.image.data.save('static/images/' + image)
        NewOpportunity = Opportunity(name = name, professor_name = professor_name, institute = institute, requirements = requirements, description = description, location = location, image = image, prof_ID = session.get('user_id'))
        db.session.add(NewOpportunity)
        db.session.commit()
    else:
        print(OppForm.errors)
    return render_template("publish-opportunity.html", form = OppForm)

class LoginForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators = [DataRequired(), Length(min = 8, max = 20)])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=20)])
    type = RadioField('Role:', choices = [("Student", "I am a Student"), ("Professor", "I am a Professor")], validators = [DataRequired()])
    submit = SubmitField('Register')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    Login = LoginForm()
    if Login.validate_on_submit():
        email = Login.email.data
        password = Login.password.data
        current_user = User.query.filter_by(email = email).first()
        if current_user is None:
            return redirect(url_for('sign_up'))
        if current_user.password == password:
            session['user_id'] = current_user.id
            if current_user.type == "Student":
                return redirect(url_for('student_home'))
            if current_user.type == "Professor":
                return redirect(url_for('professor_home'))
    else:
        print(Login.errors)
    return render_template("login.html", form = Login)

@app.route("/")
@app.route('/sign-up', methods = ['GET', 'POST'])
def sign_up():
    Register = RegistrationForm()
    if Register.validate_on_submit():
        email = Register.email.data
        if User.query.filter_by(email = email).first():
            return redirect(url_for('login'))
        password = Register.password.data
        account_type = Register.type.data
        NewUser = User(email = email, password = password, type = account_type)
        db.session.add(NewUser)
        db.session.commit()
        return redirect(url_for('login'))
    else:
        print(Register.errors)
        for problem in Register.errors:
            print(problem)
            if problem == "email":
                return error('The email address entered is invalid. Please try again')

    return render_template("sign-up.html", form = Register)

with app.app_context():
    users = User.query.all()
    count = 0
    for user in users:
        count += 1
        print(user.password)
    print(count)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)