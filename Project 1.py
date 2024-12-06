def marks():
    weight = 713 / 3
    while True:
        import random
        mark = random.sample(range(1, 8), 3)
        print("Box Locations (in kilometers):", mark)
        print('Please enter integer values between 1 and 7.')

        try:
            a = int(input("Enter the kilometer mark for Box 1: "))
            b = int(input("Enter the kilometer mark for Box 2: "))
            c = int(input("Enter the kilometer mark for Box 3: "))
        except ValueError:
            print("Invalid input. Please enter integer values between 1 and 7.")
            continue  # Restart the loop if input is invalid

        print(f"You have entered: {a, b, c}")

        if len({a, b, c}) != 3:
            print("Duplicate marks has been entered. Please enter unique marks.")
            continue  # Restart the loop for unique marks

        l = [a, b, c]
        #print(mark[1] // 2)
        count = 0
        for i in l:
            for j in mark:
                if i == j:
                    count += 1
        print(f' You have guessed right: {count}')

        if count == 3:
            total_weight = 3 * weight
            print(f'Good Job! The weight is: {weight*3} kg!')
            break
        else:
            marks()

marks()
