import argparse
import json
import socket
import sys
import threading
import time

from log.client_log_decorator import *

from utils import load_configs, send_message, get_message
from metaclasses import ClientMaker


# функция для парсинга ком строки именными аргументами
def arg_parser(CONFIGS):
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=CONFIGS['DEFAULT_IP_ADDRESS'], nargs='?')
    parser.add_argument('port', default=CONFIGS['DEFAULT_PORT'], type=int, nargs='?')
    parser.add_argument('-m', '--mode', default='listen', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_mode = namespace.mode
    # для активации клиента на передачу "python3 client.py -m send" по умолчанию "получение"

    if not 1023 < server_port < 65536:
        log('critical', 'Порт должен быть в пределах от 1024 до 65535')
        sys.exit(1)

    if client_mode not in ('listen', 'send'):
        log('critical', f'Недопустимый режим {client_mode}, допустимые режимы: listen(чтение) или send(отправка)')
        sys.exit(1)

    return server_address, server_port, client_mode


class Client(object):
    account_name = input("Введите свое имя: ")

    CONFIGS = load_configs(is_server=False)
    server_address, server_port, client_mode = arg_parser(CONFIGS)

    # def __init__(self):
    #     pass

    def main(self):
        try:
            transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            transport.connect((self.server_address, self.server_port))
            presence_message = self.create_presence_message(self.account_name, self.CONFIGS)
            # print(presence_message)
            send_message(transport, presence_message, self.CONFIGS)
            print(self.server_port, self.server_address)
            answer = self.handle_response(get_message(transport, self.CONFIGS), self.CONFIGS)
            log('info', f'Установлено соединение с сервером. Ответ сервера: {answer}')
            print(f"Соединение установлено, ответ сервера {answer}")
        except json.JSONDecodeError:
            log('error', 'Не удалось декодировать JSON-строку')
            sys.exit(1)
        except ConnectionRefusedError:
            log('critical', f'Не удалось подключиться к серверу {self.server_address}:{self.server_port},'
                            f'конечный компьютер отверг запрос на подключение')
            sys.exit(1)

        else:
            if self.client_mode == 'send':
                print('Режим работы - отправка сообщений')
            else:
                print('Режим работы - прием сообщений')
            while True:
                # print(self.client_mode)
                if self.client_mode == 'send':
                    try:
                        self.send_to_user(transport, self.account_name)
                    except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                        log('error', f'Соединение с сервером {self.server_address} было потеряно.')
                        sys.exit(1)

                if self.client_mode == 'listen':
                    try:
                        self.handle_server_message_from_client(transport, self.account_name)
                    except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                        log('error', f'Соединение с сервером {self.server_address} было потеряно.')
                        sys.exit(1)

    # метод создания presense сообщения
    def create_presence_message(self, account_name, CONFIGS):
        msg_dict = {
            CONFIGS.get('ACTION'): CONFIGS.get('PRESENCE'),
            CONFIGS.get('TIME'): time.time(),
            CONFIGS.get('USER'): {
                CONFIGS.get('ACCOUNT_NAME'): account_name  # Здесь нужно сделать привязку к конкреному аккаунту
            }
        }
        return msg_dict

    # метод проверки response сообщения от сервера (ответ на presense)
    def handle_response(self, message, CONFIGS):
        if CONFIGS.get('RESPONSE') in message:
            if message[CONFIGS.get('RESPONSE')] == 200:
                # print('OK')
                return '200: OK'
            # print('False')
            return f'400: {message[CONFIGS.get("ERROR")]}'
        raise ValueError

    # метод получения сообщений (action - message) от сервера(клиента) и проверки конфигурации смс
    def handle_server_message_from_client(self, sock, account_name):
        while True:
            try:
                message = get_message(sock, self.CONFIGS)
                if self.CONFIGS['ACTION'] in message and message[self.CONFIGS['ACTION']] == self.CONFIGS['MESSAGE'] \
                        and message[self.CONFIGS['TO_CLIENT']] == account_name and self.CONFIGS['MESSAGE_TEXT'] \
                        in message:

                    print(f"{account_name} Для Вас получено сообщение от пользователя \
                    {message[self.CONFIGS['SENDER']]}: \n {message[self.CONFIGS['MESSAGE_TEXT']]}")

                else:
                    log('error', f"Получено некорректное сообщение от сервера для {account_name}: {message}")

            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                log('critical', 'Потеряно соединение с сервером.')
                break

    # метод отправки сообщения пользователю (action - message)
    def send_to_user(self, sock, account_name):
        print(self.help_text())
        while True:

            command = input('Введите команду: ')

            if command == 'message':
                self.create_message_to_client(sock, self.CONFIGS, account_name)

            elif command == 'help':
                print(self.help_text())
            elif command == 'exit':
                send_message(sock, self.create_exit_message(account_name), self.CONFIGS)
                print('Завершение соединения.')
                log('info', 'Завершение работы по команде пользователя.')

                time.sleep(0.5)
                break

            else:
                print('Команда не распознана, попробуйте снова. help - вывести поддерживаемые команды.')

    # метод создания сообщения для клиента (модель/dict)
    def create_message_to_client(self, sock, CONFIGS, account_name):
        to_client = input("Введите имя получателя или \'q\' для завершения работы: ")
        message = input("Введите текст сообщения или \'q\' для завершения работы: ")
        if message == "q" or to_client == "q":
            sock.close()
            sys.exit(0)
        message_dict = {
            CONFIGS['ACTION']: CONFIGS['MESSAGE'],
            CONFIGS['SENDER']: account_name,
            CONFIGS['TIME']: time.time(),
            CONFIGS['ACCOUNT_NAME']: account_name,
            CONFIGS['TO_CLIENT']: to_client,
            CONFIGS['MESSAGE_TEXT']: message
        }
        # print(message_dict)
        try:
            send_message(sock, message_dict, CONFIGS)
            log('info', f'Отправлено сообщение для пользователя {to_client}')
        except:
            log('critical', 'Потеряно соединение с сервером.')
            sys.exit(1)

    def create_exit_message(self, account_name):
        return {
            self.CONFIGS['ACTION']: self.CONFIGS['EXIT'],
            self.CONFIGS['TIME']: time.time(),
            self.CONFIGS['ACCOUNT_NAME']: account_name
        }

    def help_text(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')


if __name__ == '__main__':
    Client().main()
