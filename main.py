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


class PatientAssessments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    DxName = db.Column(db.String(25))
    Assessment1 = db.Column(db.String(500))
    Assessment1Date = db.Column(db.String(10))
    Assessment2 = db.Column(db.String(500))
    Assessment2Date = db.Column(db.String(10))
    PID = db.Column(db.Integer, db.ForeignKey('patients.id'))


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
        dateOfBirth = request.form['dateOfBirth']
        age = request.form['age']
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
    # Pid = Patients.query.filter_by(id=id).first()

    globalProblemList = GlobalProblemList.query.all()
    patients = Patients.query.filter_by(id=pid)
    if request.method == 'POST':
        onSetDate = request.form['onSetDate']
        patient = request.form['findPatient']

        if patient is not None:
            dxName = request.form['selectProblem']
            globalProblemListDxName = GlobalProblemList.query.filter_by(DxName=dxName).first()

            if globalProblemListDxName.DxName == dxName:
                problemToAdd = PatientProblems(DxName=globalProblemListDxName.DxName,
                                               DxCode=str(GlobalProblemList.DxCode),
                                               DxDescription=str(GlobalProblemList.DxDescription),
                                               DxOnSetDate=onSetDate,
                                               PID=pid)
                db.session.add(problemToAdd)
                db.session.commit()
                return redirect('/CPOE/' + pid)
            else:
                return redirect('/AddProblem/' + pid)
    return render_template('addProblem.html', globalProblemList=globalProblemList, patients=patients, pid=pid)


@app.route('/AddProblemGlobal', methods=['GET', 'POST'])
def AddProblemToGlobalList():
    if request.method == 'POST':
        DxName = request.form['DxName']
        DxCode = request.form['DxCode']
        DxDescription = request.form['DxDescription']
        addGlobalProblem(DxName, DxCode, DxDescription)
        return redirect('/')
    return render_template('addProblemGlobal.html', GlobalProblemList=GlobalProblemList)


# End Pop Up Routes

# Begin Page Routes
@app.route('/', methods=['GET', 'POST'])
def init():
    db.create_all()
    patient = Patients.query.all()

    return render_template('init.html', patient=patient)


@app.route('/findPatient', methods=['GET', 'POST'])
def findPatient():
    if request.method == 'POST':
        searchForRadio = request.form['searchForPatient']
        if searchForRadio == "pid":
            pid = request.form['searchFor']
            patientPID = Patients.query.filter_by(id=pid).first()
            return redirect('/home/' + str(patientPID.id))
        elif searchForRadio == "name":
            name = request.form['searchFor']
            patientName = Patients.query.filter_by(First=name).first()
            pid = patientName.id
            return redirect('/home/' + str(pid))
        else:
            flash("Must select search by type")

    return render_template('findPatient.html')


@app.route('/home/<pid>', methods=['GET', 'POST'])
def home(pid):
    patient = Patients.query.filter_by(id=pid)

    return render_template('home.html', patient=patient)


@app.route('/ChartSummary', methods=['POST', 'GET'])
def ChartSummary():
    patients = Patients.query.all()
    patientProblems = PatientProblems.query.all()
    return render_template('chartSummary.html', patients=patients, patientProblems=patientProblems)


@app.route('/CPOE/<pid>', methods=['POST', 'GET'])
def CPOE(pid):
    patient = Patients.query.filter_by(id=pid)
    patientProblems = PatientProblems.query.filter_by(PID=pid)
    patientAssessments = PatientAssessments.query.filter_by(PID=pid).first()
    today = datetime.date.today()
    if request.method == 'POST':
        if request.form.get('commitA&P1'):
            assessment1 = request.form['assessment1']
            assessment1Add = PatientAssessments(Assessment1=assessment1, Assessment1Date=today)
            return redirect('/home/' + str(pid))

        elif request.form.get('commitA&P2'):
            assessment2 = request.form['assessment2']
            return redirect('/home/' + str(pid))
    return render_template('CPOE.html', patient=patient, patientProblems=patientProblems, pid=pid)


@app.route('/CarePlan')
def CarePlan():
    return render_template('carePlan.html')


@app.route('/HPI')
def HPI():
    return render_template('HPI.html')


@app.route('/PtInstructions')
def PtInstructions():
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


if __name__ == '__main__':
    app.run(debug=True)
