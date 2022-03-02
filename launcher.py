import subprocess
import sys


def main():
    _proc_serv = subprocess.Popen(['gnome-terminal', '--wait', '--', 'python3', 'server_p2p.py'], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)
    cln_list = int(input('Введите число клиентов, которые только принимают смс: '))
    try:
        for k in range(cln_list):
            _proc_cln_listen = subprocess.Popen(['gnome-terminal', '--wait', '--', 'python3', 'client.py'],
                                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE, text=False)
    except ValueError:
        print('Необходимо ввести число клиентов')
        sys.exit(1)
    cln_send = int(input('Введите число клиентов, которые только отправляют смс: '))
    try:
        for j in range(cln_send):
            _proc_cln_send = subprocess.Popen(['gnome-terminal', '--wait', '--', 'python3', 'client.py', '-m', 'send'],
                                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                              text=False)
    except ValueError:
        print('Необходимо ввести число клиентов')
        sys.exit(1)


if __name__ == '__main__':
    main()
