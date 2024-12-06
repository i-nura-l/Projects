from os import system, name
from time import sleep
import random

def clear():
    # Clears the console screen
    system('cls' if name == 'nt' else 'clear')

def print_board(board):
    # Displays the current state of the board with labels
    print("   A B C D E F G")
    for idx, row in enumerate(board, start=1):
        print(f"{idx:2d} " + ' '.join(row))

def place_ships():
    # Defines the ships: size and symbol
    ships = [(3, 'S'), (2, 'S'), (2, 'S'), (1, 'S'), (1, 'S'), (1, 'S'), (1, 'S')]
    board = [['~' for _ in range(7)] for _ in range(7)]

    def is_valid(x, y, size, orientation):
        # Checks if the ship can be placed at the given coordinates without touching others
        for i in range(size):
            nx = x + i if orientation == 'horizontal' else x
            ny = y if orientation == 'horizontal' else y + i
            if nx < 0 or nx >= 7 or ny < 0 or ny >= 7 or board[ny][nx] != '~':
                return False
            # Check surrounding cells for adjacent ships
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    adj_x, adj_y = nx + dx, ny + dy
                    if 0 <= adj_x < 7 and 0 <= adj_y < 7:
                        if board[adj_y][adj_x] == 'S':
                            return False
        return True
    for size, symbol in ships:
        placed = False
        while not placed:
            orientation = random.choice(['horizontal', 'vertical'])
            x = random.randint(0, 6 - size) if orientation == 'horizontal' else random.randint(0, 6)
            y = random.randint(0, 6) if orientation == 'horizontal' else random.randint(0, 6 - size)

            if is_valid(x, y, size, orientation):
                for i in range(size):
                    nx = x + i if orientation == 'horizontal' else x
                    ny = y if orientation == 'horizontal' else y + i
                    board[ny][nx] = 'S'
                placed = True

    return board

def get_shot():
    # Prompts the player to enter a valid shot coordinate
    while True:
        shot = input("Enter your shot (e.g., A5): ").upper()
        if len(shot) == 2 and shot[0] in 'ABCDEFG' and shot[1] in '1234567':
            row = int(shot[1]) - 1
            col = ord(shot[0]) - ord('A')
            return row, col
        else:
            print("Invalid input. Please enter a letter (A-G) followed by a number (1-7).")

def play_game():
    clear()
    print("Welcome to Battleship!\n")
    sleep(2)

    player_name = input("Enter your name: ")
    shots = 0
    leaderboard = []

    while True:
        clear()
        print(f"Player: {player_name}\n")
        ships_board = place_ships()
        hidden_board = [['~' for _ in range(7)] for _ in range(7)]
        shots = 0
        hits = 0

        while hits < 7:  # Total ships segments: 3 + 2 + 2 + 1 + 1 + 1 + 1 = 11
            print_board(hidden_board)
            row, col = get_shot()

            if hidden_board[row][col] != '~':
                print("You've already shot at this location. Try again.")
                sleep(2)
                clear()
                continue

            shots += 1

            if ships_board[row][col] == 'S':
                hidden_board[row][col] = 'H'
                ships_board[row][col] = 'H'
                hits += 1
                print("Hit!")
            else:
                hidden_board[row][col] = 'M'
                print("Miss!")
            sleep(1.5)
            clear()

            # Check if a ship is sunk
            if ships_board[row][col] == 'H':
                sunk = True
                # Check all adjacent cells to determine if the ship is sunk
                for y in range(max(0, row-1), min(7, row+2)):
                    for x in range(max(0, col-1), min(7, col+2)):
                        if ships_board[y][x] == 'S':
                            sunk = False
                if sunk:
                    print("You sunk a ship!")
                    sleep(1.5)
                    clear()

        print_board(hidden_board)
        print(f"Congratulations, {player_name}! You sunk all the ships in {shots} shots.")
        leaderboard.append((player_name, shots))

        play_again = input("Do you want to play again? (yes/no): ").lower()
        if play_again != 'yes':
            clear()
            print("Game Over. Leaderboard:")
            # Sort leaderboard by shots taken
            leaderboard_sorted = sorted(leaderboard, key=lambda x: x[1])
            for idx, (name, score) in enumerate(leaderboard_sorted, start=1):
                print(f"{idx}. {name} - {score} shots")
            break
if __name__ == "__main__":
    play_game()
