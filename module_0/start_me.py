from algorithm import GuessingGame


def try_again():
    print('Не верно введенные данные! Попробуйте еще раз')
    interact()

def print_my_algorithm():
    user_input = input('Хотите продолжить? (Y/n)\n')
    if user_input.lower() == 'y':
        alg_number = input('''Результат работы какого алгоритма вывести на экран?
    1. game_core_v1
    2. game_core_v2\n''')
        interact(alg_number)
    elif user_input.lower() == 'n':
        exit()
    else:
        try_again()

def print_examples_algorithm(alg_number):
    alg_number = int(alg_number.strip('.'))
    if alg_number == 1:
        GuessingGame.get_score_v1()
    elif alg_number == 2:
        GuessingGame.get_score_v2()
    else:
        try_again()

def interact(alg_number=None):
    if alg_number == None:
        print_my_algorithm()
    else:
        print_examples_algorithm(alg_number)

if __name__ == '__main__':
    obj = GuessingGame()
    obj.get_score_v3()
    interact()
        