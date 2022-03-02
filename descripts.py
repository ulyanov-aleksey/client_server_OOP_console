from log.server_log_decorator import *


class Port:
    def __set__(self, obj_of_cls, value):
        # obj_of_cls -  объект класса
        # value - значение в данном случае порта
        if not 1023 < value < 65536:
            print(f'Попытка запуска с некорректного порта: {value}, порт должен быть в пределах от 1024 до '
                  f'65535. Повторите ввод порта')
            log('critical', f'Попытка запуска с некорректного порта: {value}, порт должен быть в пределах от 1024 до '
                            f'65535')
            exit(1)
        # Если порт прошел проверку, добавляем его в список атрибутов экземпляра
        obj_of_cls.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        # owner - <class '__main__.Server'> - родительский класс (владелец)
        # name - port
        self.name = name
