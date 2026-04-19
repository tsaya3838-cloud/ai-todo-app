import json
import os

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


@app.route('/', methods=['GET', 'POST'])
def index():
    worksheet = get_worksheet()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        deadline = request.form.get('deadline', '').strip()
        worksheet.append_row([title, content, deadline])
        return redirect(url_for('index'))

    tasks = worksheet.get_all_records()
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
        worksheet.update_cell(sheet_row, 1, title)
        worksheet.update_cell(sheet_row, 2, content)
        worksheet.update_cell(sheet_row, 3, deadline)
        return redirect(url_for('index'))

    task = tasks[row_index - 1]
    return render_template('edit.html', task=task, row_index=row_index)


if __name__ == '__main__':
    app.run(debug=True)
