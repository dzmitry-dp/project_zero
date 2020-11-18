from project_0 import score_game


def text_writer(func):
    def wrapper(self):
        with open('readme.txt') as file:
            sentences = [x for x in file]
            print(sentences[-2], end='')
            print(sentences[-1])
        func(self)
    return wrapper


class GuessingGame:
    def __init__(self):
        '''Т.к. известно, что компьютер загадывает целые числа от 1 до 100,
        то алгоритм будет работать в границах диапазона от 0 до 101'''
        self._border = (0, 101,)
    
    def game_core(self, number):
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

    @text_writer
    def get_score(self):
        '''Узнаем, как быстро алгоритм угадывает число'''
        score_game(self.game_core)
