import getpass
import os
from passlib.hash import sha256_crypt


def pathadd(filename):
    return os.path.join(os.path.split(os.path.abspath(__file__))[0], filename)


with open(pathadd("list"), "r") as f:
    listM = f.read().strip().split("\n")


with open(pathadd("database"), "r") as f:
    data = eval(f.read())


def printlist(listtype, username="All"):
    string = f'{"=" * 15} {username} list {"=" * 15}'
    print(string)
    if username == "All":
        for i, j in enumerate(listtype):
            print(f"{i}) {j}")
    else:
        for i in listtype:
            print(i)
    print("=" * len(string))


def loop(text, name):
    while True:
        printlist(listM)
        number = input(text).lower()
        if "q" == number or "quit" == number:
            os.system(ver)
            break
        elif "a" == number or "all" == number:
            data[username][name] = set(listM)
            break
        else:
            try:
                [data[username][name].add(listM[int(i)]) for i in number.split(" ") if i.isdigit() is True]
            except KeyError:
                pass
            except IndexError:
                pass
    os.system(ver)

def editlist(text, name):
    while True:
        printlist(data[username][name], username)
        change = input(f"(A)dd OR (D)elete {text} OR (Q)uit: ").lower()
        if "q" in change:
            os.system(ver)
            break
        elif "a" in change:
            printlist(listM)
            number = input(f"Write number {text} OR (A)ll to add all {text} OR (Q)uit: ").lower()
            if "q" == number or "quit" == number:
                os.system(ver)
                continue
            elif "a" == number or "all" == number:
                data[username][name] = set(listM)
            else:
                try:
                    [data[username][name].add(listM[int(i)]) for i in number.split(" ") if i.isdigit() is True]
                except KeyError:
                    pass
                except IndexError:
                    pass
        elif "d" in change:
            printlist(listM)
            number = input(f"Write number {text} OR (A)ll to add all {text} OR (Q)uit: ").lower()
            if "q" == number or "quit" == number:
                os.system(ver)
                continue
            elif "a" == number or "all" == number:
                data[username][name] = set()
            else:
                try:
                    [data[username][name].remove(listM[int(i)]) for i in number.split(" ") if i.isdigit() is True]
                except KeyError:
                    pass
                except IndexError:
                    pass
        os.system(ver)


ver = 'cls' if os.name == 'nt' else 'clear'


while True:
    text = input("Change DataBase: (A)dd, (E)dit, (D)elete, (S)how, (Q)uit\n").lower()
    if "a" in text:
        os.system(ver)
        print("(A)dd")
        username = str(input("Username: "))
        password = sha256_crypt.hash(getpass.getpass())
        data[username] = {"password": password, "list": set(), "edit": set()}
        loop('Write number list "GROUP" (1 2 3 ... etc) OR (A)ll to add all list OR (Q)uit: ', "list")
        loop('Write number list "SITE" (1 2 3 ... etc) OR (A)ll to add all list OR (Q)uit: ', "edit")
    elif "e" in text:
        print("(E)dit")
        username = str(input("Username: "))
        if data.get(username) is None:
            print("No user")
            continue
        print(username)
        change = input("(P)assword OR (LG)ist group OR (LS)ist site OR (Q)uit: ").lower()
        if "q" in change:
            os.system(ver)
            continue
        elif "p" in change:
            password = sha256_crypt.hash(getpass.getpass())
            data[username]["password"] = password
        elif "lg" in change:
            editlist("list group", "list")
        elif "ls" in change:
            editlist("list site", "edit")
    elif "d" in text:
        print("(D)elete")
        try:
            data.pop(str(input("Username: ")))
        except KeyError:
            print("No username")
    elif "s" in text:
        print("=" * 40)
        for i in data.keys():
            print(f'{i}: Group - {data[i]["list"]} Site - {data[i]["edit"]}')
        print("=" * 40)
    elif "q" in text:
        print("(Q)uit")
        exit()
    else:
        print("Unknown command")
    with open(pathadd("database"), "w") as f:
        f.write(str(data))
