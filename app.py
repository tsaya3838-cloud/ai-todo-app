import json
import os
from datetime import date, datetime

from flask import Flask, render_template, request, redirect, url_for, abort
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)


def get_worksheet():
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
    ]
    credentials = Credentials.from_service_account_info(
        json.loads(os.environ.get('GOOGLE_CREDENTIALS_JSON')),
        scopes=scopes,
    )
    gc = gspread.authorize(credentials)
    sh = gc.open("AI-ToDo-List")
    return sh.get_worksheet(0)


def attach_deadline_alerts(tasks):
    today = date.today()

    for task in tasks:
        status = task.get('ステータス', '未完了')
        deadline_str = (task.get('期日') or '').strip()
        task['deadline_alert'] = ''
        task['deadline_alert_level'] = ''

        if status == '完了' or not deadline_str:
            continue

        try:
            deadline_date = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        except ValueError:
            continue

        diff_days = (deadline_date - today).days
        if diff_days < 0:
            task['deadline_alert'] = '期限切れ'
            task['deadline_alert_level'] = 'overdue'
        elif diff_days == 0:
            task['deadline_alert'] = '今日が期限'
            task['deadline_alert_level'] = 'today'
        else:
            task['deadline_alert'] = f'あと{diff_days}日'
            task['deadline_alert_level'] = 'upcoming'

    return tasks


@app.route('/', methods=['GET', 'POST'])
def index():
    worksheet = get_worksheet()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        deadline = request.form.get('deadline', '').strip()
        category = request.form.get('category', 'その他').strip() or 'その他'
        worksheet.append_row([title, content, deadline, '未完了', category])
        return redirect(url_for('index'))

    tasks = attach_deadline_alerts(worksheet.get_all_records())
    return render_template('index.html', tasks=tasks)


@app.route('/edit/<int:row_index>', methods=['GET', 'POST'])
def edit(row_index):
    worksheet = get_worksheet()
    tasks = worksheet.get_all_records()
    if row_index < 1 or row_index > len(tasks):
        abort(404)

    # 1行目はヘッダー。loop.index（1始まり）に対応するシート上の行は row_index + 1
    sheet_row = row_index + 1

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        deadline = request.form.get('deadline', '').strip()
        status = request.form.get('status', '未完了').strip() or '未完了'
        category = request.form.get('category', 'その他').strip() or 'その他'
        worksheet.update_cell(sheet_row, 1, title)
        worksheet.update_cell(sheet_row, 2, content)
        worksheet.update_cell(sheet_row, 3, deadline)
        worksheet.update_cell(sheet_row, 4, status)
        worksheet.update_cell(sheet_row, 5, category)
        return redirect(url_for('index'))

    task = tasks[row_index - 1]
    return render_template('edit.html', task=task, row_index=row_index)


@app.route('/complete/<int:row_index>')
def complete(row_index):
    worksheet = get_worksheet()
    tasks = worksheet.get_all_records()
    if row_index < 1 or row_index > len(tasks):
        abort(404)

    sheet_row = row_index + 1
    worksheet.update_cell(sheet_row, 4, '完了')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
