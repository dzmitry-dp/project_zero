def game_core(number):
    count = 0
    min_number = 0
    max_number = 100
    predict = 50
    while number != predict:
        count+=1
        if number > predict:
            min_number = predict
            predict += (max_number - predict)//2
        elif number < predict:
            max_number = predict
            predict -= (predict - min_number)//2

        print('count:', count, 'min_number:', min_number,
            'max_number:', max_number, 'predict:', predict)
    return count


print(game_core(12))