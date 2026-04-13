from django.db.models import Avg, Q, Count
from django.db.models import FloatField
from django.shortcuts import render, redirect
from pathlib import Path
import xlwt
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, timedelta
import csv
from django.db.models.functions import TruncDate
from django.db.models.functions import Cast
from urllib.parse import urlencode

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn import svm
from sklearn.linear_model import LogisticRegression
from sklearn.tree import ExtraTreeClassifier

from apps.Remote_User.models import ClientRegister_Model, cyber_threat_identification, detection_ratio, detection_accuracy, prediction_audit

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / 'data' / 'Datasets.csv'


def _parse_iso_date(raw_value):
    if not raw_value:
        return None
    try:
        return date.fromisoformat(raw_value)
    except ValueError:
        return None


def _apply_audit_filters(request):
    queryset = prediction_audit.objects.all()
    quick = request.GET.get('quick', '').strip()
    sort = request.GET.get('sort', '').strip()
    username = request.GET.get('username', '').strip()
    label = request.GET.get('label', '').strip()
    from_date_raw = request.GET.get('from_date', '').strip()
    to_date_raw = request.GET.get('to_date', '').strip()
    min_confidence_raw = request.GET.get('min_confidence', '').strip()

    today = timezone.localdate()
    if quick == 'today':
        from_date_raw = today.isoformat()
        to_date_raw = today.isoformat()
    elif quick == 'last7':
        from_date_raw = (today - timedelta(days=6)).isoformat()
        to_date_raw = today.isoformat()
    elif quick == 'threat':
        label = 'Cyber Threat Found'
    elif quick == 'safe':
        label = 'No Cyber Threat Found'

    if username:
        queryset = queryset.filter(username__icontains=username)

    if label in {'Cyber Threat Found', 'No Cyber Threat Found'}:
        queryset = queryset.filter(predicted_label=label)
    else:
        label = ''

    from_date = _parse_iso_date(from_date_raw)
    to_date = _parse_iso_date(to_date_raw)

    if from_date:
        queryset = queryset.filter(created_at__date__gte=from_date)
    if to_date:
        queryset = queryset.filter(created_at__date__lte=to_date)

    min_confidence = None
    if min_confidence_raw:
        try:
            min_confidence = float(min_confidence_raw)
        except ValueError:
            min_confidence = None
            min_confidence_raw = ''

    if min_confidence is not None:
        queryset = queryset.annotate(confidence_num=Cast('confidence', FloatField())).filter(confidence_num__gte=min_confidence)

    sort_map = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'confidence_high': '-confidence',
        'confidence_low': 'confidence',
        'threat_first': '-predicted_label',
    }
    if sort not in sort_map:
        sort = 'newest'
    queryset = queryset.order_by(sort_map[sort], '-id')

    filters = {
        'quick': quick,
        'sort': sort,
        'username': username,
        'label': label,
        'from_date': from_date_raw,
        'to_date': to_date_raw,
        'min_confidence': min_confidence_raw,
    }
    return queryset, filters


def _build_query_tail(request, **overrides):
    payload = {}
    for key in ['quick', 'sort', 'username', 'label', 'from_date', 'to_date', 'min_confidence']:
        value = request.GET.get(key, '').strip()
        if value:
            payload[key] = value

    for key, value in overrides.items():
        if value in (None, ''):
            payload.pop(key, None)
        else:
            payload[key] = value

    return urlencode(payload)


def _normalize_label(value):
    try:
        return 1 if int(value) == 1 else 0
    except (TypeError, ValueError):
        text = str(value).strip().lower()
        return 1 if text in {'1', 'threat', 'cyber threat found', 'yes', 'true'} else 0


def _summarize_training_results(records):
    best_name = None
    best_score = None
    total = 0
    sum_scores = 0.0

    for row in records:
        raw_ratio = str(getattr(row, 'ratio', '')).replace('%', '').strip()
        try:
            score = float(raw_ratio)
        except ValueError:
            continue

        total += 1
        sum_scores += score
        if best_score is None or score > best_score:
            best_score = score
            best_name = getattr(row, 'names', 'N/A')

    avg_score = round(sum_scores / total, 2) if total else None
    return {
        'total_models': total,
        'best_model': best_name,
        'best_score': round(best_score, 2) if best_score is not None else None,
        'avg_score': avg_score,
    }


def _load_training_dataframe(uploaded_file=None):
    if uploaded_file is None:
        return pd.read_csv(DATASET_PATH, encoding='latin-1')

    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    try:
        return pd.read_csv(uploaded_file)
    except Exception:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        return pd.read_csv(uploaded_file, encoding='latin-1')


def _train_and_store_models(df):
    if 'tweet_text' not in df.columns or 'Label' not in df.columns:
        raise ValueError("Dataset must contain 'tweet_text' and 'Label' columns")

    if len(df) < 4:
        raise ValueError('Dataset must contain at least four rows')

    prepared = df.copy()
    prepared['results'] = prepared['Label'].apply(_normalize_label)

    if prepared['results'].nunique() < 2:
        raise ValueError('Dataset must contain both threat and no-threat labels')

    class_counts = prepared['results'].value_counts()
    if class_counts.min() < 2:
        raise ValueError('Each label class must contain at least two rows')

    X = CountVectorizer().fit_transform(prepared['tweet_text'].fillna('').astype(str))
    y = prepared['results']

    test_size = 0.5 if len(prepared) < 10 else 0.2
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=42,
        stratify=y,
    )

    models = [
        ("Naive Bayes", MultinomialNB()),
        ("Linear SVM", svm.LinearSVC()),
        ("Logistic Regression", LogisticRegression(random_state=42, solver='liblinear', max_iter=200)),
        ("Extra Tree Classifier", ExtraTreeClassifier(random_state=42)),
    ]

    detection_accuracy.objects.all().delete()
    for name, model in models:
        model.fit(X_train, y_train)
        score = accuracy_score(y_test, model.predict(X_test)) * 100
        detection_accuracy.objects.create(names=name, ratio=f"{score:.2f}")

    records = list(detection_accuracy.objects.all())
    return records, _summarize_training_results(records)


def serviceproviderlogin(request):
    if request.method == "POST":
        admin = request.POST.get('username')
        password = request.POST.get('password')
        if admin == "Admin" and password == "Admin":
            detection_accuracy.objects.all().delete()
            return redirect('service_provider_home')
        return render(request, 'SProvider/serviceproviderlogin.html', {'object': 'Invalid admin credentials'})

    return render(request, 'SProvider/serviceproviderlogin.html')


def service_provider_home(request):
    remote_users = ClientRegister_Model.objects.count()
    predicted_records = cyber_threat_identification.objects.count()
    training_models = detection_accuracy.objects.count()
    audit_records = prediction_audit.objects.count()
    threat_found = cyber_threat_identification.objects.filter(Prediction='Cyber Threat Found').count()
    threat_safe = cyber_threat_identification.objects.filter(Prediction='No Cyber Threat Found').count()

    return render(request, 'SProvider/service_provider_home.html', {
        'remote_users': remote_users,
        'predicted_records': predicted_records,
        'training_models': training_models,
        'audit_records': audit_records,
        'threat_found': threat_found,
        'threat_safe': threat_safe,
    })


def train_models(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('dataset_file')
        if not uploaded_file:
            return render(request, 'SProvider/train_models.html', {
                'objs': [],
                'status_msg': 'Please upload a CSV file before training',
                'summary': {},
            })

        try:
            df = _load_training_dataframe(uploaded_file)
            obj, summary = _train_and_store_models(df)
            return render(request, 'SProvider/train_models.html', {
                'objs': obj,
                'status_msg': f'Training completed for {uploaded_file.name}',
                'summary': summary,
                'uploaded_filename': uploaded_file.name,
            })
        except Exception as exc:
            return render(request, 'SProvider/train_models.html', {
                'objs': [],
                'status_msg': str(exc),
                'summary': {},
            })

    return render(request, 'SProvider/train_models.html', {
        'objs': [],
        'status_msg': 'Upload a CSV file to train and evaluate the models',
        'summary': {},
    })


def View_Predicted_Cyber_Threat_Identification_Type_Ratio(request):
    detection_ratio.objects.all().delete()

    total_count = cyber_threat_identification.objects.count()
    if total_count == 0:
        return render(request, 'SProvider/View_Predicted_Cyber_Threat_Identification_Type_Ratio.html', {'objs': []})

    found_count = cyber_threat_identification.objects.filter(Q(Prediction='Cyber Threat Found')).count()
    not_found_count = cyber_threat_identification.objects.filter(Q(Prediction='No Cyber Threat Found')).count()

    found_ratio = (found_count / total_count) * 100
    if found_ratio != 0:
        detection_ratio.objects.create(names='Cyber Threat Found', ratio=found_ratio)

    not_found_ratio = (not_found_count / total_count) * 100
    if not_found_ratio != 0:
        detection_ratio.objects.create(names='No Cyber Threat Found', ratio=not_found_ratio)

    obj = detection_ratio.objects.all()
    return render(request, 'SProvider/View_Predicted_Cyber_Threat_Identification_Type_Ratio.html', {'objs': obj})


def View_Remote_Users(request):
    obj = ClientRegister_Model.objects.all()
    return render(request, 'SProvider/View_Remote_Users.html', {'objects': obj})


def charts(request, chart_type):
    chart1 = detection_ratio.objects.values('names').annotate(dcount=Avg('ratio'))
    return render(request, "SProvider/charts.html", {'form': chart1, 'chart_type': chart_type})


def charts1(request, chart_type):
    chart1 = detection_accuracy.objects.values('names').annotate(dcount=Avg('ratio'))
    return render(request, "SProvider/charts1.html", {'form': chart1, 'chart_type': chart_type})


def View_Predicted_Cyber_Threat_Identification_Type(request):
    obj = cyber_threat_identification.objects.all()
    threat_found_count = obj.filter(Prediction='Cyber Threat Found').count()
    no_threat_count = obj.filter(Prediction='No Cyber Threat Found').count()
    return render(request, 'SProvider/View_Predicted_Cyber_Threat_Identification_Type.html', {
        'list_objects': obj,
        'threat_found_count': threat_found_count,
        'no_threat_count': no_threat_count,
    })


def likeschart(request, like_chart):
    charts_data = detection_accuracy.objects.values('names').annotate(dcount=Avg('ratio'))
    return render(request, "SProvider/likeschart.html", {'form': charts_data, 'like_chart': like_chart})


def Download_Predicted_DataSets(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Predicted_Datasets.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("sheet1")
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    data = cyber_threat_identification.objects.all()
    for my_row in data:
        row_num += 1
        ws.write(row_num, 0, my_row.fid, font_style)
        ws.write(row_num, 1, my_row.tweet_text, font_style)
        ws.write(row_num, 2, my_row.timestamp, font_style)
        ws.write(row_num, 3, my_row.source, font_style)
        ws.write(row_num, 4, my_row.symbols, font_style)
        ws.write(row_num, 5, my_row.company_names, font_style)
        ws.write(row_num, 6, my_row.url, font_style)
        ws.write(row_num, 7, my_row.source_ip, font_style)
        ws.write(row_num, 8, my_row.protocol, font_style)
        ws.write(row_num, 9, my_row.dest_ip, font_style)
        ws.write(row_num, 10, my_row.Prediction, font_style)

    wb.save(response)
    return response


def train_model(request):
    existing_results = detection_accuracy.objects.all()
    if existing_results.exists():
        existing_records = list(existing_results)
        status_msg = 'Showing cached training results'
        if request.GET.get('refreshed') == '1':
            status_msg = 'Prediction model cache refreshed and training results reloaded'
        return render(request, 'SProvider/train_model.html', {
            'objs': existing_records,
            'status_msg': status_msg,
            'summary': _summarize_training_results(existing_records),
        })

    try:
        df = _load_training_dataframe()
        obj, summary = _train_and_store_models(df)
        (PROJECT_ROOT / 'data' / 'Results.csv').write_text(df.to_csv(index=False), encoding='utf-8')
        return render(request, 'SProvider/train_model.html', {
            'objs': obj,
            'status_msg': 'Model training completed successfully',
            'summary': summary,
        })
    except Exception as exc:
        return render(request, 'SProvider/train_model.html', {
            'objs': [],
            'status_msg': str(exc),
            'summary': {},
        })


def refresh_prediction_model_cache(request):
    from apps.Remote_User.views import clear_prediction_model_cache

    clear_prediction_model_cache()
    return redirect('/train_model/?refreshed=1')


def view_prediction_audit_log(request):
    records, filters = _apply_audit_filters(request)

    total = records.count()
    threat_total = records.filter(predicted_label='Cyber Threat Found').count()
    safe_total = records.filter(predicted_label='No Cyber Threat Found').count()
    threat_pct = round((threat_total / total) * 100, 1) if total else 0
    safe_pct = round((safe_total / total) * 100, 1) if total else 0
    today = timezone.localdate()
    last_7_start = today - timedelta(days=6)
    today_total = records.filter(created_at__date=today).count()
    last_7_total = records.filter(created_at__date__gte=last_7_start, created_at__date__lte=today).count()

    paginator = Paginator(records, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)

    quick_links = {
        'all': _build_query_tail(request, quick='', from_date='', to_date='', label='', username=''),
        'today': _build_query_tail(request, quick='today'),
        'last7': _build_query_tail(request, quick='last7'),
        'threat': _build_query_tail(request, quick='threat'),
        'safe': _build_query_tail(request, quick='safe'),
    }

    clear_filters_query = _build_query_tail(
        request,
        quick='',
        username='',
        label='',
        from_date='',
        to_date='',
        min_confidence='',
    )

    confidence_links = {
        '70': _build_query_tail(request, min_confidence='70'),
        '80': _build_query_tail(request, min_confidence='80'),
        '90': _build_query_tail(request, min_confidence='90'),
        '95': _build_query_tail(request, min_confidence='95'),
    }

    trend_rows = []
    try:
        trend_qs = records.annotate(day=TruncDate('created_at')).values('day').annotate(
            total=Count('id'),
            threat=Count('id', filter=Q(predicted_label='Cyber Threat Found')),
        ).order_by('-day')[:7]

        trend_source = list(reversed(list(trend_qs)))
        max_total = max((row['total'] for row in trend_source), default=1)
        for row in trend_source:
            safe_count = row['total'] - row['threat']
            trend_rows.append({
                'day': row['day'],
                'total': row['total'],
                'threat': row['threat'],
                'safe': safe_count,
                'width_pct': int((row['total'] / max_total) * 100) if max_total else 0,
            })
    except Exception:
        trend_rows = []

    return render(request, 'SProvider/View_Prediction_Audit_Log.html', {
        'records': page_obj.object_list,
        'page_obj': page_obj,
        'query_tail': query_params.urlencode(),
        'export_query': query_params.urlencode(),
        'return_to': query_params.urlencode(),
        'trend_rows': trend_rows,
        'quick_links': quick_links,
        'clear_filters_query': clear_filters_query,
        'confidence_links': confidence_links,
        'stats': {
            'total': total,
            'threat_total': threat_total,
            'safe_total': safe_total,
            'threat_pct': threat_pct,
            'safe_pct': safe_pct,
            'today_total': today_total,
            'last_7_total': last_7_total,
        },
        'filters': filters,
    })


def download_prediction_audit_log(request):
    records, _filters = _apply_audit_filters(request)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Prediction_Audit_Log.xls"'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("audit_log")

    header_style = xlwt.XFStyle()
    header_style.font.bold = True

    headers = ['User', 'FID', 'Predicted Label', 'Confidence', 'Created At']
    for col_idx, header in enumerate(headers):
        ws.write(0, col_idx, header, header_style)

    row_idx = 1
    for rec in records[:5000]:
        ws.write(row_idx, 0, rec.username)
        ws.write(row_idx, 1, rec.fid)
        ws.write(row_idx, 2, rec.predicted_label)
        ws.write(row_idx, 3, rec.confidence)
        ws.write(row_idx, 4, str(rec.created_at))
        row_idx += 1

    wb.save(response)
    return response


def download_prediction_audit_log_csv(request):
    records, _filters = _apply_audit_filters(request)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Prediction_Audit_Log.csv"'

    writer = csv.writer(response)
    writer.writerow(['User', 'FID', 'Predicted Label', 'Confidence', 'Created At'])
    for rec in records[:10000]:
        writer.writerow([rec.username, rec.fid, rec.predicted_label, rec.confidence, rec.created_at])

    return response


def view_user_prediction_history(request, username):
    base_qs = prediction_audit.objects.filter(username=username)
    total = base_qs.count()
    threat_total = base_qs.filter(predicted_label='Cyber Threat Found').count()
    safe_total = base_qs.filter(predicted_label='No Cyber Threat Found').count()
    records = base_qs.order_by('-created_at')[:500]
    return_to = request.GET.get('return_to', '').strip()
    back_url = '/view_prediction_audit_log/'
    if return_to:
        back_url = '/view_prediction_audit_log/?' + return_to

    return render(request, 'SProvider/View_User_Prediction_History.html', {
        'records': records,
        'username': username,
        'back_url': back_url,
        'stats': {
            'total': total,
            'threat_total': threat_total,
            'safe_total': safe_total,
        },
    })