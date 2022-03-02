import argparse
import sys
import json
import socket
import select

# from log.server_log_config import *
import time

from descripts import Port
from log.server_log_decorator import *
from utils import load_configs, send_message, get_message
from metaclasses import ServerMaker

# CONFIGS = {}


# функция для парсинга ком строки именными аргументами
def arg_parser():
    CONFIGS = load_configs()
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=CONFIGS['DEFAULT_PORT'], type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    # if not 1023 < listen_port < 65536:
    #     log('critical', f'Попытка запуска с некоректного порта: {listen_port}'
    #                     f'Порт должен быть в пределах от 1024 до 65535')
    #     sys.exit(1)
    #
    return listen_address, listen_port


# Основной класс сервера
class Server(metaclass=ServerMaker):
    port = Port()
    CONFIGS = load_configs()


    def __init__(self, listen_address, listen_port):
        # Параментры подключения
        self.addr = listen_address
        self.port = listen_port

        # Список подключённых клиентов.
        self.clients = []

        # Список сообщений на отправку.
        self.messages = []

        # Словарь содержащий сопоставленные имена и соответствующие им сокеты.
        self.names = dict()

    def init_socket(self):

        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        # Начинаем слушать сокет.
        self.sock = transport
        self.sock.listen(self.CONFIGS.get('MAX_CONNECTIONS'))
        log('info', f'Сервер запущен по адресу: {self.addr}, на порту: {self.port}.')
        print(f'Сервер запущен по адресу: {self.addr}, на порту: {self.port}.')

    def main_serv(self):
        # Инициализация Сокета
        self.init_socket()

        # Основной цикл программы сервера
        while True:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                log('info', f'Установлено соединение с ПК {client_address}')
                self.clients.append(client)
            finally:
                recv_data_lst = []
                send_data_lst = []
                err_lst = []
            # Проверяем на наличие ждущих клиентов
            try:
                recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            # принимаем сообщения и если ошибка, исключаем клиента.
            requests = self.read_request(recv_data_lst, self.clients)
            # print(f'Прочитаны смс {clients}')
            # print(f"send_data_list {recv_data_list}")
            if requests:
                self.write_responses(requests, send_data_lst, self.clients)
                # print(f'Отправлены смс {clients}')

    def read_request(self, r_list, clients):
        responses = {}

        for sock in r_list:
            try:
                data = get_message(sock, self.CONFIGS)
                responses[sock] = data
            except:
                clients.remove(sock)
        return responses

    def write_responses(self, requests, w_list, clients):
        for sock in w_list:  # перебор всех клиентов в w_list
            for _, request in requests.items():  # тк requests это словарь {клиент: сообщение} вытягиваем все
                # смс от всех клиентов "_" это игнор
                # алиаса для "клиента" мы его не использ
                print(request)
                if request['action'] == 'presence':
                    req_pres = self.handle_message(request, self.CONFIGS)

                    send_message(sock, req_pres, self.CONFIGS)

                else:
                    try:
                        send_message(sock, request, self.CONFIGS)
                        # print(f'отправлено смс {request}')
                    except:
                        sock.close()
                        clients.remove(sock)

    def handle_message(self, message, CONFIGS):
        # print(message[CONFIGS.get('USER')][CONFIGS.get('ACCOUNT_NAME')])
        if CONFIGS.get('ACTION') in message and message[CONFIGS.get('ACTION')] == CONFIGS.get('PRESENCE') \
                and CONFIGS.get('TIME') in message and CONFIGS.get('USER') in message:
            # == message[CONFIGS.get('USER')][CONFIGS.get('ACCOUNT_NAME')]:
            return {CONFIGS.get('RESPONSE'): 200,
                    CONFIGS.get('USER'): message[CONFIGS.get('USER')][CONFIGS.get('ACCOUNT_NAME')]}
        return {
            CONFIGS.get('RESPONSE'): 400,
            CONFIGS.get('ERROR'): 'Bad Request'
        }


def main():
    listen_address, listen_port = arg_parser()

    # Создание экземпляра класса - сервера.
    server = Server(listen_address, listen_port)
    server.main_serv()


if __name__ == '__main__':
    main()
