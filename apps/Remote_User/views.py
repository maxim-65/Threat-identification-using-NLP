from django.db.models import Count
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from pathlib import Path
from datetime import datetime, date, timedelta

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib
from django.contrib.auth.hashers import make_password, check_password

# Create your views here.
from apps.Remote_User.models import ClientRegister_Model,cyber_threat_identification,detection_ratio,detection_accuracy
from apps.Remote_User.models import prediction_audit

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / 'data' / 'Datasets.csv'
MODEL_CACHE_PATH = PROJECT_ROOT / 'ml_cache' / 'prediction_bundle.joblib'
_PREDICTION_MODEL_CACHE = {
    'dataset_mtime': None,
    'vectorizer': None,
    'classifier': None,
}


def clear_prediction_model_cache():
    _PREDICTION_MODEL_CACHE['dataset_mtime'] = None
    _PREDICTION_MODEL_CACHE['vectorizer'] = None
    _PREDICTION_MODEL_CACHE['classifier'] = None
    if MODEL_CACHE_PATH.exists():
        MODEL_CACHE_PATH.unlink()


def _normalize_label(value):
    try:
        return 1 if int(value) == 1 else 0
    except (TypeError, ValueError):
        text = str(value).strip().lower()
        return 1 if text in {'1', 'threat', 'cyber threat found', 'yes', 'true'} else 0


def _parse_timestamp_to_date(value):
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y",
        "%m/%d/%Y %H:%M:%S",
        "%d-%m-%Y",
        "%d-%m-%Y %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(raw.replace("Z", "")).date()
    except ValueError:
        return None


def _infer_cyber_threat_type(tweet_text, source='', protocol=''):
    text = f"{tweet_text or ''} {source or ''} {protocol or ''}".lower()

    rules = [
        ('DDoS / Flooding Attack', ['ddos', 'flood', 'botnet', 'traffic spike', 'syn flood']),
        ('Phishing / Social Engineering', ['phish', 'credential', 'spoof', 'fake login', 'social engineering']),
        ('Malware / Ransomware', ['malware', 'ransom', 'trojan', 'worm', 'payload', 'encrypt files']),
        ('Data Breach / Exfiltration', ['data leak', 'exfiltration', 'breach', 'stolen data', 'dumped database']),
        ('Web Application Attack', ['sql injection', 'xss', 'csrf', 'webshell', 'path traversal']),
        ('Brute Force / Unauthorized Access', ['brute force', 'password spray', 'unauthorized login', 'credential stuffing']),
    ]

    for threat_type, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return threat_type

    return 'Suspicious Cyber Activity (General)'


def _get_prediction_model():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    dataset_mtime = DATASET_PATH.stat().st_mtime
    if (
        _PREDICTION_MODEL_CACHE['vectorizer'] is not None
        and _PREDICTION_MODEL_CACHE['classifier'] is not None
        and _PREDICTION_MODEL_CACHE['dataset_mtime'] == dataset_mtime
    ):
        return _PREDICTION_MODEL_CACHE['vectorizer'], _PREDICTION_MODEL_CACHE['classifier']

    if MODEL_CACHE_PATH.exists():
        try:
            bundle = joblib.load(MODEL_CACHE_PATH)
            if bundle.get('dataset_mtime') == dataset_mtime:
                _PREDICTION_MODEL_CACHE['dataset_mtime'] = bundle['dataset_mtime']
                _PREDICTION_MODEL_CACHE['vectorizer'] = bundle['vectorizer']
                _PREDICTION_MODEL_CACHE['classifier'] = bundle['classifier']
                return _PREDICTION_MODEL_CACHE['vectorizer'], _PREDICTION_MODEL_CACHE['classifier']
        except Exception:
            pass

    df = pd.read_csv(DATASET_PATH, encoding='latin-1')
    if 'tweet_text' not in df.columns or 'Label' not in df.columns:
        raise ValueError("Datasets.csv must contain 'tweet_text' and 'Label' columns")

    tweets = df['tweet_text'].fillna('').astype(str)
    labels = df['Label'].apply(_normalize_label)

    vectorizer = CountVectorizer()
    features = vectorizer.fit_transform(tweets)

    classifier = MultinomialNB()
    classifier.fit(features, labels)

    try:
        MODEL_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                'dataset_mtime': dataset_mtime,
                'vectorizer': vectorizer,
                'classifier': classifier,
            },
            MODEL_CACHE_PATH,
        )
    except Exception:
        pass

    _PREDICTION_MODEL_CACHE['dataset_mtime'] = dataset_mtime
    _PREDICTION_MODEL_CACHE['vectorizer'] = vectorizer
    _PREDICTION_MODEL_CACHE['classifier'] = classifier
    return vectorizer, classifier

def login(request):


    if request.method == "POST" and 'submit1' in request.POST:

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password')
        enter = ClientRegister_Model.objects.filter(
            Q(username__iexact=username) | Q(email__iexact=username)
        ).first()
        if enter:
            password_ok = check_password(password, enter.password) or enter.password == password
            if password_ok:
                request.session["userid"] = enter.id
                return redirect('ViewYourProfile')

        return render(request,'RUser/login.html', {'object': 'Invalid username/email or password'})

    return render(request,'RUser/login.html')

def index(request):
    total_records = 0
    threat_found_count = 0
    no_threat_count = 0
    input_features = 0

    if DATASET_PATH.exists():
        try:
            df = pd.read_csv(DATASET_PATH, encoding='latin-1')
            total_records = len(df)
            input_features = len(df.columns)
            if 'Label' in df.columns:
                normalized = df['Label'].apply(_normalize_label)
                threat_found_count = int((normalized == 1).sum())
                no_threat_count = int((normalized == 0).sum())
        except Exception:
            pass

    threat_ratio = round((threat_found_count / total_records) * 100, 2) if total_records else 0
    no_threat_ratio = round((no_threat_count / total_records) * 100, 2) if total_records else 0

    total_predictions = cyber_threat_identification.objects.count()
    db_threat_found = cyber_threat_identification.objects.filter(Prediction='Cyber Threat Found').count()
    db_no_threat = cyber_threat_identification.objects.filter(Prediction='No Cyber Threat Found').count()

    today = date.today()
    week_ago = today - timedelta(days=6)
    predictions_today = 0
    predictions_last_7_days = 0
    for ts in cyber_threat_identification.objects.values_list('timestamp', flat=True):
        parsed_date = _parse_timestamp_to_date(ts)
        if not parsed_date:
            continue
        if parsed_date == today:
            predictions_today += 1
        if week_ago <= parsed_date <= today:
            predictions_last_7_days += 1

    return render(
        request,
        'RUser/index.html',
        {
            'total_records': total_records,
            'threat_found_count': threat_found_count,
            'no_threat_count': no_threat_count,
            'input_features': input_features,
            'threat_ratio': threat_ratio,
            'no_threat_ratio': no_threat_ratio,
            'total_predictions': total_predictions,
            'db_threat_found': db_threat_found,
            'db_no_threat': db_no_threat,
            'predictions_today': predictions_today,
            'predictions_last_7_days': predictions_last_7_days,
        },
    )

def Add_DataSet_Details(request):

    return render(request, 'RUser/Add_DataSet_Details.html', {"excel_data": ''})


def Register1(request):

    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phoneno = request.POST.get('phoneno')
        country = request.POST.get('country')
        state = request.POST.get('state')
        city = request.POST.get('city')
        address = request.POST.get('address')
        gender = request.POST.get('gender')

        if not username:
            return render(request, 'RUser/Register1.html', {'object': 'Username is required', 'status_type': 'error'})

        if not email:
            return render(request, 'RUser/Register1.html', {'object': 'Email is required', 'status_type': 'error'})

        if not password:
            return render(request, 'RUser/Register1.html', {'object': 'Password is required', 'status_type': 'error'})

        if not phoneno:
            return render(request, 'RUser/Register1.html', {'object': 'Phone number is required', 'status_type': 'error'})

        if ClientRegister_Model.objects.filter(username=username).exists():
            return render(request, 'RUser/Register1.html', {'object': 'Username already exists', 'status_type': 'error'})

        if ClientRegister_Model.objects.filter(email=email).exists():
            return render(request, 'RUser/Register1.html', {'object': 'Email already registered', 'status_type': 'error'})

        if not phoneno or not phoneno.isdigit() or len(phoneno) != 10:
            return render(request, 'RUser/Register1.html', {'object': 'Phone number must be exactly 10 digits', 'status_type': 'error'})

        if not password or len(password) < 4:
            return render(request, 'RUser/Register1.html', {'object': 'Password must be at least 4 characters', 'status_type': 'error'})

        hashed_password = make_password(password)
        ClientRegister_Model.objects.create(
            username=username,
            email=email,
            password=hashed_password,
            phoneno=phoneno,
            country=country or '',
            state=state or '',
            city=city or '',
            address=address or '',
            gender=gender or '',
        )

        obj = "Registered Successfully"
        return render(request, 'RUser/Register1.html',{'object':obj, 'status_type': 'success'})
    else:
        return render(request,'RUser/Register1.html')

def ViewYourProfile(request):
    userid = request.session.get('userid')
    if not userid:
        return render(request, 'RUser/login.html', {'object': 'Please login to view your profile'})

    obj = get_object_or_404(ClientRegister_Model, id=userid)
    return render(request,'RUser/ViewYourProfile.html',{'object':obj})


def Predict_Cyber_Threat_Identification_Type(request):
    if request.method == "POST":
        fid = request.POST.get('fid')
        tweet_text = request.POST.get('tweet_text')
        timestamp = request.POST.get('timestamp')
        source = request.POST.get('source')
        symbols = request.POST.get('symbols')
        company_names = request.POST.get('company_names')
        url = request.POST.get('url')
        source_ip = request.POST.get('source_ip')
        protocol = request.POST.get('protocol')
        dest_ip = request.POST.get('dest_ip')

        if not tweet_text:
            return render(request, 'RUser/Predict_Cyber_Threat_Identification_Type.html', {'objs': 'Please enter tweet_text', 'is_error': True, 'threat_type': None})

        if timestamp and not _parse_timestamp_to_date(timestamp):
            return render(request, 'RUser/Predict_Cyber_Threat_Identification_Type.html', {'objs': 'Timestamp format is invalid (use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)', 'is_error': True, 'threat_type': None})

        try:
            vectorizer, classifier = _get_prediction_model()
            vector = vectorizer.transform([str(tweet_text)])
            prediction = int(classifier.predict(vector)[0])
            confidence = round(float(classifier.predict_proba(vector)[0][prediction]) * 100, 2)
        except Exception:
            return render(request, 'RUser/Predict_Cyber_Threat_Identification_Type.html', {'objs': 'Prediction temporarily unavailable', 'is_error': True, 'threat_type': None})

        if (prediction == 0):
            val = 'No Cyber Threat Found'
            threat_type = 'No Threat Detected'
        elif (prediction == 1):
            val = 'Cyber Threat Found'
            threat_type = _infer_cyber_threat_type(tweet_text, source=source, protocol=protocol)
            print(f"Predicted cyber threat type: {threat_type}")

        cyber_threat_identification.objects.create(
        fid=fid,
        tweet_text=tweet_text,
        timestamp=timestamp,
        source=source,
        symbols=symbols,
        company_names=company_names,
        url=url,
        source_ip=source_ip,
        protocol=protocol,
        dest_ip=dest_ip,
        Prediction=val)

        try:
            username = None
            if request.session.get('userid'):
                user_obj = ClientRegister_Model.objects.filter(id=request.session.get('userid')).first()
                username = user_obj.username if user_obj else None
            prediction_audit.objects.create(
                username=username or 'anonymous',
                fid=fid or '',
                predicted_label=val,
                confidence=str(confidence),
            )
        except Exception:
            pass

        return render(request, 'RUser/Predict_Cyber_Threat_Identification_Type.html', {'objs': val, 'confidence': confidence, 'threat_type': threat_type, 'is_error': False})
    return render(request, 'RUser/Predict_Cyber_Threat_Identification_Type.html')



