from flask import Flask, request, render_template, redirect, flash, url_for, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_json import FlaskJSON, json_response
import datetime

app = Flask(__name__, static_url_path="/static")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
json = FlaskJSON(app)
json.init_app(app)


class Patients(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    First = db.Column(db.String(40))
    Last = db.Column(db.String(100))
    DateOfBirth = db.Column(db.String(90))
    Age = db.Column(db.Integer)
    Insurance = db.Column(db.String(150))
    PrimaryProvider = db.Column(db.String(50))
    Phone = db.Column(db.String(50))


class PatientProblems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    DxName = db.Column(db.String(25))
    DxCode = db.Column(db.String(10), nullable=True)
    DxDescription = db.Column(db.String(80), nullable=True)
    DxOnSetDate = db.Column(db.String(10), nullable=True)
    PID = db.Column(db.Integer, db.ForeignKey('patients.id'), autoincrement=True)


class GlobalProblemList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    DxName = db.Column(db.String(25))
    DxCode = db.Column(db.String(10))
    DxDescription = db.Column(db.String(80))


def addGlobalProblem(DxName, DxCode, DxDescription):
    DxName = DxName
    DxCode = DxCode
    DxDescription = DxDescription
    db.session.add(GlobalProblemList(DxName=DxName, DxCode=DxCode, DxDescription=DxDescription))
    db.session.commit()

def getID (patientFirst):
    patient = Patients.query.filter_by(First=patientFirst).first()
    return patient


@app.route('/', methods=['GET','POST'])
def home():
    db.create_all()
    patient = Patients.query.all()

    return render_template('home.html', patient=patient)

@app.route('/DropTables',methods=['GET','POST'])
def DropTables():
    if request.method == 'POST':
        db.drop_all()
        return redirect('/')
@app.route('/DropProblems', methods=['GET','POST'])
def DropProblems():
    patients = PatientProblems.query.all()
    if request.method == 'POST':
        for pt in patients:
            db.session.delete(pt)
            db.session.commit()
        return redirect('/')

@app.route('/AddPt', methods=['GET', 'POST'])
def AddPt():
    if request.method == 'POST':
        first = request.form['first']
        last = request.form['last']
        dateOfBirth = request.form['dateOfBirth']
        age = request.form['age']
        insurance = request.form['insurance']
        primaryProvider = request.form['primaryProvider']
        phone = request.form['phone']
        db.session.add(Patients(First=first, Last=last, DateOfBirth=dateOfBirth, Age=age, Insurance=insurance,
                                PrimaryProvider=primaryProvider, Phone=phone))
        db.session.commit()
        return redirect('/')
    return render_template('AddPt.html')


@app.route('/AddProblem/<id>', methods=['POST', 'GET'])
def AddProblem(id):
    Pid = Patients.query.filter_by(id=id).first()
    globalProblemList = GlobalProblemList.query.all()
    patients = Patients.query.all()
    if request.method == 'POST':
        onSetDate = request.form['onSetDate']
        patient = request.form['findPatient']
        parsePatient = str(patient).split(' ')
        patiedPID = int(parsePatient[2])



        if patient is not None:
            dxName = request.form['selectProblem']
            globalProblemListDxName = GlobalProblemList.query.filter_by(DxName=dxName).first()

            if globalProblemListDxName.DxName == dxName:
                db.session.add(PatientProblems(DxName=globalProblemListDxName.DxName,
                                               DxCode=str(GlobalProblemList.DxCode),
                                               DxDescription=str(GlobalProblemList.DxDescription),
                                               DxOnSetDate=onSetDate,
                                               PID=Pid))
                db.session.commit()
            else:
                return redirect('/AddProblem')
    return render_template('AddProblem.html', globalProblemList=globalProblemList, patients=patients)


@app.route('/AddProblemGlobal', methods=['POST', 'GET'])
def AddProblemToGlobalList():
    if request.method == 'POST':
        DxName = request.form['DxName']
        DxCode = request.form['DxCode']
        DxDescription = request.form['DxDescription']
        addGlobalProblem(DxName, DxCode, DxDescription)
        return redirect('/CPOE')
    return render_template('AddProblemGlobal.html', GlobalProblemList=GlobalProblemList)

@app.route('/ChartSummary', methods=['POST', 'GET'])
def ChartSummary():
    patients = Patients.query.all()
    patientProblems = PatientProblems.query.all()
    return render_template('ChartSummary.html', patients=patients, patientProblems=patientProblems)


@app.route('/CPOE', methods=['POST', 'GET'])
def CPOE():
    patients = Patients.query.all()
    patientProblems = PatientProblems.query.all()

    if request.method == 'POST':
        patientSelected = request.form['selectPatient']

        print(patientSelected)


    return render_template('CPOE.html', patients=patients, patientProblems=patientProblems)


@app.route('/HPI')
def HPI():
    return render_template('HPI.html')


@app.route('/PtInstructions')
def PtInstructions():
    return render_template('PtInstructions.html')


@app.route('/VS')
def VS():
    return render_template('VS.html')


@app.route('/Immunizations')
def Immunizations():
    return render_template('Immunizations.html')


@app.route('/PMHPSH')
def PMHPSH():
    return render_template('PMH-PSH.html')


if __name__ == '__main__':
    app.run(debug=True)
