from algorithm import GuessingGame


if __name__ == '__main__':
    obj = GuessingGame()
    obj.get_score_v3()
    while True:
        user_input = input('Хотите продолжить? (Y/n)\n')
        if user_input.lower() == 'y':
            pass
        elif user_input.lower() == 'n':
            pass
        else:
            pass
        
        break