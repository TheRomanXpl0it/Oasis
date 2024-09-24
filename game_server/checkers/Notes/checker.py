#!/usr/bin/env python3

import hashlib
import os
import random
import string

import requests
import bs4

import names

import checklib

data = checklib.get_data()
action = data['action']
team_id = data['teamId']
service_addr = '10.60.' + team_id + '.1'
service_name = 'Notes'

os.makedirs('flag_ids', exist_ok=True)


def create_note(title: str, content: str, private: bool) -> int:
    note_data = {}
    note_data['title'] = title
    note_data['content'] = content
    if private:
        note_data['private'] = ''

    resp = requests.post(f'http://{service_addr}:8080/new', data=note_data)
    if resp.status_code != 200:
        checklib.quit(checklib.Status.DOWN,
                      f'Bad create note status code: {resp.status_code}')

    parts = resp.url.split('/view/')
    if len(parts) != 2:
        checklib.quit(checklib.Status.DOWN, 'Invalid create note redirect')

    try:
        return int(parts[1])
    except ValueError:
        checklib.quit(checklib.Status.DOWN, 'Invalid create note id')


def view_note(note_id: int) -> tuple[str, str]:
    resp = requests.get(f'http://{service_addr}:8080/view/{note_id}')
    if resp.status_code != 200:
        checklib.quit(checklib.Status.DOWN,
                      f'Bad view note status code: {resp.status_code}')

    html = bs4.BeautifulSoup(resp.text, features="html.parser")
    title_elem = html.select_one('div.container > h1')
    content_elem = html.select_one('div.container > p')
    if not title_elem or not content_elem:
        checklib.quit(checklib.Status.DOWN, 'Invalid view note page')

    return title_elem.text.strip(), content_elem.text.strip()


def check_sla():
    resp = requests.get(f'http://{service_addr}:8080')
    if resp.status_code != 200:
        checklib.quit(checklib.Status.DOWN,
                      f'Bad index page status code: {resp.status_code}')

    note_title = names.get_random_name()
    note_content = ''.join(random.choices(
        string.ascii_letters + string.digits, k=64))
    note_id = create_note(note_title, note_content, False)

    view_note_title, view_note_content = view_note(note_id)
    if view_note_title != note_title or view_note_content != note_content:
        checklib.quit(checklib.Status.DOWN, 'Invalid note title or content')

    checklib.quit(checklib.Status.OK)


def put_flag():
    flag = data['flag']

    note_title = names.get_random_name()
    note_id = create_note(note_title, flag, True)

    with open(f'flag_ids/flag_{hashlib.sha1(flag.encode()).hexdigest()}.txt', 'w') as f:
        f.write(str(note_id))

    try:
        checklib.post_flag_id(service_name, service_addr, note_id)
    except Exception as e:
        checklib.quit(checklib.Status.ERROR, "Checker error", str(e))
    checklib.quit(checklib.Status.OK)


def get_flag():
    flag = data['flag']

    with open(f'flag_ids/flag_{hashlib.sha1(flag.encode()).hexdigest()}.txt', 'r') as f:
        note_id = int(f.read())

    _, note_content = view_note(note_id)
    if note_content != flag:
        checklib.quit(checklib.Status.DOWN, 'No flag in note content')

    checklib.quit(checklib.Status.OK)


def main():
    try:
        if action == checklib.Action.CHECK_SLA.name:
            check_sla()
        elif action == checklib.Action.PUT_FLAG.name:
            put_flag()
        elif action == checklib.Action.GET_FLAG.name:
            get_flag()
    except requests.RequestException as e:
        checklib.quit(checklib.Status.DOWN, 'Request error', str(e))


if __name__ == "__main__":
    main()
