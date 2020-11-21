from example import *


def write_wrapper(func):
    '''Оборачиваю результат моей работы'''
    def wrapper(self):
        with open('readme.md') as file:
            print('\n')
            print('Проект_0 состоит из:')
            sentences = [sentence.rstrip() for sentence in file]
            for s in sentences:
                if 'example.py' in s or 'algorithm.py' in s:
                    print(s)
            func(self)
            print('\n')
            print(sentences[-1])
    return wrapper


class GuessingGame:
    def __init__(self):
        '''Т.к. известно, что компьютер загадывает целые числа от 1 до 100,
        то алгоритм будет работать в границах диапазона от 0 до 101'''
        self._border = (0, 101,)
    
    def game_core_v3(self, number):
        '''Постоянно делим пополам диапазон вариантов искомых чисел.
        Устанавливаем новые границы поиска "загаданного" числа '''
        count = 0
        min_border = self._border[0] # минимальная граница
        max_border = self._border[1] # максимальная граница
        predict = 50 # предполагаю, что "загаданное" число - это середина диапазона искомых вариантов
        while number != predict:
            count+=1
            if number > predict:
                min_border = predict # меняем нижнюю границу диапазона в котором находится искомое число
                predict += (max_border - predict)//2 # предполагаю, что число по середине уже нового диапазона 
            elif number < predict:
                max_border = predict # меняем верхнюю границу диапазона
                predict -= (predict - min_border)//2
        return (count)

    def get_score_v1(self):
        '''Узнаем, как быстро алгоритм угадывает число'''
        score_game(game_core_v1)

    def get_score_v2(self):
        score_game(game_core_v2)

    @write_wrapper
    def get_score_v3(self):
        score_game(self.game_core_v3)
