from math import floor

import requests
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
today = datetime.date.today()


class Patients(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    First = db.Column(db.String(40))
    Last = db.Column(db.String(100))
    DateOfBirth = db.Column(db.String(90))
    Age = db.Column(db.String(10))
    Insurance = db.Column(db.String(150))
    PrimaryProvider = db.Column(db.String(50))
    Phone = db.Column(db.String(50))


class Employees(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Role = db.Column(db.String(50))
    First = db.Column(db.String(50))
    Last = db.Column(db.String(50))
    DateOfBirth = db.Column(db.String(10))
    NPI = db.Column(db.Integer, nullable=True)
    StLicense = db.Column(db.String(80), nullable=True)
    Medicaid = db.Column(db.Integer, nullable=True)
    Medicare = db.Column(db.String(80), nullable=True)
    DEA = db.Column(db.String(80), nullable=True)
    UPIN = db.Column(db.String(80), nullable=True)


class PatientProblems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    DxName = db.Column(db.String(25))
    DxCode = db.Column(db.String(10), nullable=True)
    DxOnSetDate = db.Column(db.String(10), nullable=True)
    PID = db.Column(db.Integer, db.ForeignKey('patients.id'), autoincrement=True)


class PatientAssessments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    DxName = db.Column(db.String(25))
    Assessment = db.Column(db.String(500))
    AssessmentDate = db.Column(db.String(10))
    PID = db.Column(db.Integer, db.ForeignKey('patients.id'))


class PatientCarePlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    DxName = db.Column(db.String(25))
    ProviderGoal = db.Column(db.String(500))
    PatientGoal = db.Column(db.String(500))
    ProviderAction = db.Column(db.String(500))
    PatientAction = db.Column(db.String(500))
    ProviderGoalMet = db.Column(db.BOOLEAN)
    PatientGoalMet = db.Column(db.BOOLEAN)
    PID = db.Column(db.Integer, db.ForeignKey('patients.id'))
    ProviderId = db.Column(db.Integer, db.ForeignKey('employees.id'))


class GlobalProblemList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    DxName = db.Column(db.String(25))
    DxCode = db.Column(db.String(10))


def addGlobalProblem(DxName, DxCode):
    DxName = DxName
    DxCode = DxCode
    db.session.add(GlobalProblemList(DxName=DxName, DxCode=DxCode))
    db.session.commit()


def getID(patientFirst):
    patient = Patients.query.filter_by(First=patientFirst).first()
    return patient


# Begin Logic Routes
@app.route('/DropTables', methods=['GET', 'POST'])
def DropTables():
    if request.method == 'POST':
        db.drop_all()
        return redirect('/home')


@app.route('/DropProblems', methods=['GET', 'POST'])
def DropProblems():
    patients = PatientProblems.query.all()
    if request.method == 'POST':
        for pt in patients:
            db.session.delete(pt)
            db.session.commit()
        return redirect('/home')


# End Logic Routes
# Begin Pop Up Routes
@app.route('/AddPt', methods=['GET', 'POST'])
def AddPt():
    if request.method == 'POST':
        first = request.form['first']
        last = request.form['last']

        dt_string = request.form.get('dateOfBirth')
        dateOfBirth = dt_string
        formatT = "%Y-%m-%d"
        dt_object = datetime.datetime.strptime(dt_string, formatT)
        currentDate_obj = datetime.datetime.today()
        age = currentDate_obj - dt_object
        age = str(age)
        age = age.split(" ")
        age = floor(int(age[0]) / 365)
        age = str(age)

        insurance = request.form['insurance']
        primaryProvider = request.form['primaryProvider']
        phone = request.form['phone']
        db.session.add(Patients(First=first, Last=last, DateOfBirth=dateOfBirth, Age=age, Insurance=insurance,
                                PrimaryProvider=primaryProvider, Phone=phone))
        db.session.commit()
        return redirect('/')
    return render_template('addPt.html')


@app.route('/AddProblem/<pid>', methods=['POST', 'GET'])
def AddProblem(pid):
    globalProblemList = GlobalProblemList.query.all()
    patients = Patients.query.filter_by(id=pid)
    if request.method == 'POST':
        dt_string = request.form.get('onSetDate')
        onSetDate = dt_string

        dxName = request.form['selectProblem']
        globalProblemListDxName = GlobalProblemList.query.filter_by(DxName=dxName).first()
        globalProblemListDxCode = GlobalProblemList.query.filter_by(DxName=dxName).first()
        if globalProblemListDxName.DxName == dxName:
            problemToAdd = PatientProblems(DxName=globalProblemListDxName.DxName,
                                           DxCode=globalProblemListDxCode.DxCode,
                                           DxOnSetDate=onSetDate,
                                           PID=pid)
            db.session.add(problemToAdd)
            db.session.commit()
            return redirect('/CPOE/' + pid)
        # else:
        #    return redirect('/AddProblem/' + pid)
    return render_template('addProblem.html', globalProblemList=globalProblemList, patients=patients, pid=pid)


@app.route('/AddProblemGlobal', methods=['GET', 'POST'])
def AddProblemToGlobalList():
    if request.method == 'POST':
        DxCode = request.form['icd10Code']
        globalProblems = GlobalProblemList.query.all()
        nameJsonObject = requests.get(
            'https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search?sf=code,name&terms=' + DxCode)
        nameJsonObjects = nameJsonObject.json()
        textNameJson = nameJsonObjects[3]
        nameOfDx = textNameJson[0]
        DxName = nameOfDx[1]
        for code in globalProblems:
            userICDCode = code.DxCode
            if DxCode == userICDCode:
                return redirect('/Errors/errorAddGlobalProblem')

        db.session.add(GlobalProblemList(DxName=DxName, DxCode=DxCode))
        db.session.commit()
        return redirect('/findPatient')
    return render_template('addProblemGlobal.html', GlobalProblemList=GlobalProblemList)


# End Pop Up Routes

# Begin Page Routes
@app.route('/', methods=['GET', 'POST'])
def init():
    db.create_all()
    patient = Patients.query.all()

    return render_template('init.html', patient=patient)


@app.route('/base', methods=['GET', 'POST'])
def base(pid):
    patient = Patients.query.filter_by(id=pid)
    render_template('home.html', patient=patient)


@app.route('/findPatient', methods=['GET', 'POST'])
def findPatient():
    patients = Patients.query.all()
    if request.method == 'POST':
        searchForRadio = request.form['searchForPatient']
        if searchForRadio == "pid":
            pid = request.form['searchFor']
            patientPID = Patients.query.filter_by(id=pid).first()
            for pt in patients:
                if str(pt.id) == pid:
                    break
                else:
                    return redirect('/Errors/errorAddGlobalProblem')

            return redirect('/home/' + str(patientPID.id))
        elif searchForRadio == "name":
            name = request.form['searchFor']
            patientName = Patients.query.filter_by(First=name).first()
            for pt in patients:
                if str(pt.First) == name:
                    break
                else:
                    return redirect('/Errors/errorAddGlobalProblem')
            pid = patientName.id
            return redirect('/home/' + str(pid))
        else:
            flash("Must select search by type")

    return render_template('findPatient.html')


@app.route('/home/<pid>', methods=['GET', 'POST'])
def home(pid):
    patient = Patients.query.filter_by(id=pid)

    return render_template('home.html', patient=patient)


@app.route('/DeleteProblem/<probId>/<pid>')
def DeleteProblem(probId, pid):
    id = PatientProblems.query.filter_by(id=probId).first()
    print(id)
    db.session.delete(id)
    db.session.commit()
    return redirect('/ChartSummary/' + pid)


@app.route('/ChartSummary/<pid>', defaults={'dxDDCode': None}, methods=['POST', 'GET'])
@app.route('/ChartSummary/<pid>/<dxDDCode>', methods=['POST', 'GET'])
def ChartSummary(pid, dxDDCode):
    patient = Patients.query.filter_by(id=pid)
    patientProblems = PatientProblems.query.filter_by(PID=pid)
    patientAssessments = PatientAssessments.query.filter_by(PID=pid)

    if request.method == 'POST':
        print('post')
        DxDD = request.form['DxDD']
        print(DxDD)

        if request.form['Submit'] == 'findDx':
            print('here')
            dxDD = request.form['DxDD']
            dxDDCode = dxDD.split(' | ')
            dxDDCode = dxDDCode[0]
            print(dxDD)
            print(dxDDCode)
            return redirect('/ChartSummary/' + pid + '/' + dxDDCode)
        elif request.form['Submit'] == 'Add Problem':
            return redirect('/AddProblem/' + pid)

    return render_template('chartSummary.html', patient=patient, patientProblems=patientProblems,
                           patientAssessments=patientAssessments, dxDDCode=dxDDCode)


@app.route('/CPOE/<pid>', methods=['POST', 'GET'])
def CPOE(pid):
    patient = Patients.query.filter_by(id=pid)
    patientProblems = PatientProblems.query.filter_by(PID=pid)
    patientAssessments = PatientAssessments.query.filter_by(PID=pid).first()

    if request.method == 'POST':
        print('post')
        if request.form.get('commitA&P'):
            print("commit1")
            problem1 = request.form['problemDD1']
            assessment1 = request.form['textarea1']
            print(assessment1)
            assessment1Add = PatientAssessments(DxName=problem1, Assessment=assessment1, AssessmentDate=str(today),
                                                PID=pid)
            db.session.add(assessment1Add)
            db.session.commit()
            return redirect('/home/' + str(pid))

        if request.form.get('commitA&P2'):
            problem2 = request.form['problemDD2']
            assessment2 = request.form['textarea2']
            assessment2Add = PatientAssessments(DxName=problem2, Assessment=assessment2, AssessmentDate=str(today),
                                                PID=pid)
            db.session.add(assessment2Add)
            db.session.commit()
            return redirect('/home/' + str(pid))
    return render_template('CPOE.html', patient=patient, patientProblems=patientProblems, pid=pid)


@app.route('/CarePlan/<pid>', methods=['GET', 'POST'])
def CarePlan(pid):
    patient = Patients.query.filter_by(id=pid)
    patientProblems = PatientProblems.query.filter_by(PID=pid)
    patientCarePlan = PatientCarePlan.query.filter_by(PID=pid)

    return render_template('carePlan.html', patient=patient, patientProblems=patientProblems,
                           patientCarePlan=patientCarePlan, pid=pid)


@app.route('/HPI')
def HPI():
    return render_template('HPI.html')


@app.route('/PtInstructions', methods=['GET','POST'])
def PtInstructions():
    if request.method == 'POST':
        print("here")

    return render_template('ptInstructions.html')


@app.route('/VS')
def VS():
    return render_template('VS.html')


@app.route('/Immunizations')
def Immunizations():
    return render_template('Immunizations.html')


@app.route('/PMHPSH')
def PMHPSH():
    return render_template('PMH-PSH.html')

@app.route('/FHIRExtract', methods=['GET','POST','PUSH'])
def FHIRExtract():


    return render_template('fhirExtract.html')


@app.route('/Errors/errorAddGlobalProblem')
def errorAddGlobalProblem():
    return render_template('Errors/errorAddGlobalProblem.html')


if __name__ == '__main__':
    app.run(debug=True)
