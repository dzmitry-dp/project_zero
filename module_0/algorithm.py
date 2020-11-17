from gtn import score_game


def game_core(number):
    count = 0
    min_border = 0
    max_border = 101
    predict = 50
    while number != predict:
        count+=1
        if number > predict:
            min_border = predict
            predict += (max_border - predict)//2
        elif number < predict:
            max_border = predict
            predict -= (predict - min_border)//2
    return (count)


if __name__ == '__main__':
    score_game(game_core)