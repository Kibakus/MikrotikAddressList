import os
import re
import time
from threading import Thread
from datetime import timedelta

from flask import Flask, redirect, url_for, render_template, request, session
from passlib.hash import sha256_crypt
import paramiko
import dns.reversename
import dns.resolver


def pathsettings(filename):  # Узнать где находиться файл и прописать полный путь
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "Settings", filename)


def pathadd(filename):  # Узнать где находиться файл и прописать полный путь
    return os.path.join(os.path.dirname(__file__), filename)


#  Редактировать параметры

"""
IPADRESS = "192.168.0.3"
SSHUSERNAME = "admin"
PORT = 22
"""

IPADRESS = "192.168.99.74"
SSHUSERNAME = "admin"
PORT = 22


SSHKEY = pathsettings('privat')

log = ""

app = Flask(__name__, template_folder=pathadd("templates"))


#  Открыть SSH соеденение
def sshpipe():
    sshcon = paramiko.SSHClient()
    sshcon.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sshcon.connect(IPADRESS, username=SSHUSERNAME, port=PORT, key_filename=SSHKEY)
    return sshcon


sshcon = sshpipe()


#  Проверка пользователя в базе
def checkpass(userName, password, login=False):
    datauser = data.get(userName)
    if datauser is None:
        session["status"] = "Login Error"
        return False
    else:
        if sha256_crypt.verify(password, datauser['password']):
            session["status"] = ""
            session['username'] = userName
            if login:
                session.permanent = True
                session['logged_in'] = True
        else:
            session["status"] = "Password Error"
            return False
    return True


#  Output address-list Mikrotik
def ipdata():
    stdin, stdout, stderr = sshcon.exec_command('/ip firewall address-list print terse where list ~"^' + "\$|^".join(listM) + '\$" dynamic')
    table = list(map(list, re.findall("(\d+).+comment=(.+?) list=(.+?) address=(.+?) creation.+timeout=(.+) ", stdout.read().decode("utf-8"))))
    for i, j in enumerate(table):
        try:
            iphosts = f"{j[3]}({dns.resolver.resolve(dns.reversename.from_address(j[3]),'PTR')[0]})"
        except:
            iphosts = j[3] + "(None)"
        table[i].append(iphosts)
    return sorted(table, key=lambda name: name[2].lower())


def ipdatauser(Username):
    stdin, stdout, stderr = sshcon.exec_command('/ip firewall address-list print terse where list ~"^' + "\$|^".join(data.get(session['username'])['list']) + '\$" comment=' + Username)
    datassh = stdout.read().decode("utf-8")
    # table = list(map(list, re.findall("(\d+).+comment=(.+?) list=(.+?) address=(.+?) creation(?![^\n]*timeout).+?\n", datassh)))
    # [table[i].append("∞") for i in range(len(table))]
    table = list(map(list, re.findall("(\d+).+comment=(.+?) list=(.+?) address=(.+?) creation.+timeout=(.+) ", datassh)))
    for i, j in enumerate(table):
        try:
            iphosts = f"{j[3]}({dns.resolver.resolve(dns.reversename.from_address(j[3]),'PTR')[0]})"
        except:
            iphosts = j[3] + "(None)"
        table[i].append(iphosts)
    return sorted(table, key=lambda name: name[2].lower())


def ipdatacustom(custom):
    if custom is None:
        return []
    stdin, stdout, stderr = sshcon.exec_command('/ip firewall address-list print terse where list=' + custom)
    datassh = stdout.read().decode("utf-8")
    table = list(map(list, re.findall("\d+   list=(.+?) address=(.+?) creation(?![^\n]*timeout).+?\n", datassh)))
    [table[i].insert(0, "") for i in range(len(table))]
    table = list(map(list, re.findall("   comment=(.+?) list=(.+?) address=(.+?) creation(?![^\n]*timeout).+?\n", datassh))) + table
    return table


class ParseData(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global data
        global table
        global listM
        while True:
            with open(pathsettings("database"), "r") as f:
                data = eval(f.read())
            with open(pathsettings("list"), "r") as f:
                listM = f.read().strip().split("\n")
            table = ipdata()
            time.sleep(60)


#  Главная страница (загрузка address-list и вывод одной из трех страниц)
@app.route('/')
def home():
    if not session.get("status"):
        session["status"] = ""
    if not session.get('logged_in'):
        return render_template('login.html', table=table, status=session["status"])
    elif session.get("mode") == "changepass":
        return render_template('change.html', status=session["status"])
    elif session.get("mode") == "edit":
        return render_template('edit.html', editlist=sorted(data.get(session['username'])['edit']), listCustom=ipdatacustom(session.get("listcustom")), listname=session.get("listcustom"))
    session["count"] = 0
    return render_template('index.html', table=ipdatauser(session['username']), status=session["status"], username=session['username'], listsUser=sorted(data.get(session['username'])['list']), listsite=bool(data.get(session['username'])['edit']))


#  Обработчик авторизации
@app.route('/login', methods=['POST'])
def logining():
    try:
        session["count"] += 1
    except KeyError:
        session["count"] = 0
    checkpass(request.form['username'], request.form['password'], True)
    return redirect(url_for("home"))


#  Обработчик добавления в address-list
@app.route('/obr', methods=['POST'])
def obr():
    global table
    if not session.get('logged_in'):
        return render_template('login.html')
    if request.form["listM"] not in data.get(session['username'])['list']:
        return redirect(url_for("home"))
    if 24 <= int(request.form["timeout"]):
        timeout = 24
    else:
        timeout = int(request.form["timeout"])
    if request.form["ipaddress"] == "":
        ip = request.remote_addr
    elif len([i for i in request.form["ipaddress"].split(".") if int(i) < 255]) == 4:
        ip = request.form["ipaddress"].strip()
    else:
        session["status"] = "No valid IP"
        return redirect(url_for("home"))
    ids = [i[0] for i in table if i[1] == session['username'] and i[3] == ip]
    if ids != [] and int(request.form["change"]) == 1:  # Изменение времени в address-list
        sshcon.exec_command(f'/ip firewall address-list set timeout={timeout}:0:0 [find where list={request.form["listM"]} comment={session["username"]} address={ip}]')
        sshcon.exec_command(f'/log warning message="{request.form["listM"]} CHANGE user: {session["username"]}, ip: {ip}, mac: 111, timeout: {timeout}h"')
    else:
        sshcon.exec_command(f'/ip firewall address-list add address={ip} timeout={timeout}:0:0 list={request.form["listM"]} comment={session["username"]}')
        sshcon.exec_command(f'/log warning message="{request.form["listM"]} ADD user: {session["username"]}, ip: {ip}, mac: 111, timeout: {timeout}h"')
    session['logged_in'] = False  # Закрытие сессии
    table = ipdata()
    return redirect(url_for("home"))


#  Обработчик выбора списка
@app.route('/listcustom', methods=['GET'])
def listcustom():
    if not session.get('logged_in'):
        return render_template('login.html')
    if request.args.get("listUse") in data.get(session['username'])['edit']:
        session["listcustom"] = request.args.get("listUse")
    return redirect(url_for("home"))


#  Обработчик изменение пароля и добавления в базу
@app.route('/editadd', methods=['POST'])
def editadd():
    if not session.get('logged_in'):
        return render_template('login.html')
    if session["listcustom"] in data.get(session['username'])['edit']:
        if request.form["comment"] == "":
            sshcon.exec_command(f'/ip firewall address-list add address={request.form["ip"].strip()} list={session["listcustom"]}')
        else:
            sshcon.exec_command(f'/ip firewall address-list add address={request.form["ip"].strip()} list={session["listcustom"]} comment={request.form["comment"]}')
    return redirect(url_for("home"))


#  Обработчик изменение списков и переадресация на страницу с изменением списков
@app.route('/edit', methods=['GET'])
def edit():
    if not session.get('logged_in'):
        return render_template('login.html')
    if data.get(session['username'])['edit'] == set():
        return redirect(url_for("home"))
    session["mode"] = "edit"
    return redirect(url_for("home"))


#  Обработчик изменение пароля и переадресация на страницу с изменением пароля
@app.route('/changepass', methods=['GET'])
def changepass():
    if not session.get('logged_in'):
        return render_template('login.html')
    session["mode"] = "changepass"
    return redirect(url_for("home"))


#  Обработчик изменение пароля и добавления в базу
@app.route('/changepassok', methods=['POST'])
def changepassok():
    if not session.get('logged_in'):
        return render_template('login.html')
    if not checkpass(session['username'], request.form['password']):
        session["status"] = "Старый пароль не верный"
        return redirect(url_for("home"))
    if request.form['newpassword'] != request.form['confirmpassword']:
        session["status"] = "Новые пароли не совпадают"
        return redirect(url_for("home"))
    if len(request.form['newpassword']) < 6:
        session["status"] = "Новый пароль меньше 6 символов"
        return redirect(url_for("home"))
    data[session['username']]['password'] = sha256_crypt.hash(request.form['newpassword'])
    with open(pathsettings("database"), "w") as f:
        f.write(str(data))
    session["mode"] = None
    return redirect(url_for("home"))


#  Обработчик закрытия сессии в address-list
@app.route('/close')
def close():
    global table
    if not session.get('logged_in'):
        return render_template('login.html')
    if request.args.get("comment") is None:
        for i in table:
            if i[1] == session['username'] and i[3] == request.args.get("ip"):
                sshcon.exec_command(f'/ip firewall address-list remove [find where list={request.args.get("listname")} comment={session["username"]} address={request.args.get("ip")}]')
                sshcon.exec_command(f'/log warning message="{request.args.get("listname")} DELETE user: {session["username"]}, ip: {request.args.get("ip")}, mac: 111"')
        table = ipdata()
    else:
        if request.args.get("listname") in data.get(session['username'])['edit']:
            sshcon.exec_command(f'/ip firewall address-list remove [find where list={request.args.get("listname")} address={request.args.get("ip")}]')
            sshcon.exec_command(f'/log warning message="{request.args.get("listname")} DELETE user: {session["username"]}, ip: {request.args.get("ip")}, mac: 111"')
    return redirect(url_for("home"))


#  Обработчик отмены
@app.route('/back', methods=['GET'])
def back():
    if not session.get('logged_in'):
        return render_template('login.html')
    session["mode"] = None
    session["listcustom"] = None
    return redirect(url_for("home"))


#  Обработчик выхода
@app.route('/logout')
def logout():
    if not session.get('logged_in'):
        return render_template('login.html')
    session['logged_in'] = False
    session.clear()
    return redirect(url_for("home"))


#  подгрузка базы и запуск сервера
if __name__ == "__main__":
    ParseData().start()
    while True:
        if "data" in globals():
            break
        else:
            time.sleep(0.5)
    app.permanent_session_lifetime = timedelta(minutes=3)
    app.secret_key = os.urandom(12)
    app.run(debug=False, host='0.0.0.0', port=10000)
