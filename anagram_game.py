#!/usr/bin/python3
"""
Python code to play a game with a command line, textual interface. In the game, an English word is randomly proposed (initially 4 letters). The player's job is to suggest an anagram of that word, also a valid English word, which must have either one more or one fewer letter than the original. The computer then suggests an anagram of that word with the same rules (one or fewer letter). Gameplay proceeds like this in turns. The user's score is counted based on how many turns they survive. There are three difficulty levels offered at the start of the game; the computer player chooses words that decrease or increase the player's likelihood of success based on the level.
"""

import os
import random
import requests

USED_WORDS = []

# Load words from a file
WORD_LIST_URL = "http://web.mit.edu/freebsd/head/share/dict/web2"
WORD_LIST_FILENAME = 'word_list_alpha.text'
def load_words():
    # Check if the word list file already exists
    if not os.path.exists(WORD_LIST_FILENAME):
        # Download the word list and save it locally
        print("Downloading word list...")
        response = requests.get(WORD_LIST_URL)
        # Ensure the response was successful
        if response.status_code == 200:
            with open(WORD_LIST_FILENAME, "w") as file:
                file.write(response.text)
        else:
            print("Failed to download the word list.")
            return []
    
    # Load words from the local file
    with open(WORD_LIST_FILENAME, "r") as file:
        words = file.read().split()
    
    return [word.strip() for word in words if word.strip() and starts_with_non_capital(word)]

def starts_with_non_capital(s):
    return not s.split()[0][0].isupper()

def words_by_length(words, length):
    return [word for word in words if len(word) == length]

def get_anagrams(base_word, words, length_diff) -> list[str]:
    base_letters = sorted(base_word)
    potential_anagrams = []
    for word in words:
        if len(word) != len(base_word) + length_diff:
            continue
        word_letters = sorted(word)
        # For words with one more letter, check if base_letters are in word_letters
        if length_diff == 1 and all(base_letters.count(letter) <= word_letters.count(letter) for letter in base_letters):
            potential_anagrams.append(word)
        # For words with one fewer letter, check if word_letters are in base_letters
        elif length_diff == -1 and all(word_letters.count(letter) <= base_letters.count(letter) for letter in word_letters):
            potential_anagrams.append(word)
    return potential_anagrams

def choose_next_word(current_word, words, difficulty) -> str:
    # Find anagrams with one more or one fewer letter, but at least 3
    potential_words_plus = get_anagrams(current_word, words, 1)
    potential_words_minus = get_anagrams(current_word, words, -1) if len(current_word) > 3 else []
    potential_words = potential_words_plus + potential_words_minus
    potential_words = [word for word in potential_words if word not in USED_WORDS]
    
    # Group by the number of available next-round anagrams
    word_anagram_counts = {word: len(get_anagrams(word, words, 1) + get_anagrams(word, words, -1)) for word in potential_words}
    
    # Choose next word based on difficulty
    if difficulty == 1:  # Easy: Choose words with the most available anagrams
        max_anagrams = max(word_anagram_counts.values())
        choices = [word for word, count in word_anagram_counts.items() if count == max_anagrams]
    elif difficulty == 3:  # Hard: Choose words with the fewest available anagrams
        min_anagrams = min(word_anagram_counts.values())
        choices = [word for word, count in word_anagram_counts.items() if count == min_anagrams]
    else:  # Medium: Random choice
        choices = list(word_anagram_counts.keys())
    
    return random.choice(choices) if choices else None

def get_all_potential_anagrams(current_word: str, words: list[str]) -> list[str]:
    all_words = get_anagrams(current_word, words, 1) + (get_anagrams(current_word, words, -1) if len(current_word) > 3 else [])
    return [word for word in all_words if word not in USED_WORDS]


INTRO_TEXT = """
Welcome to the Anagram Game.

You will be shown a word. 
You need to enter a new, English word that reuses all the letters from the last word, but has either one more or one fewer letter.
You cannot reuse words and all words must be at least 3 letters.
Your score will be determined by how many words you find and how many letters they use.

Good luck!
"""
# Main game loop
def play_game(words):
    print(INTRO_TEXT)
    print("Difficulty levels: 1. Easy, 2. Medium, 3. Hard")
    difficulty = int(input("Choose difficulty (1-3): "))
    
    if difficulty not in [1, 2, 3]:
        print("Invalid difficulty. Defaulting to Medium.")
        difficulty = 2
    
    # Adjust difficulty
    current_length = 4 if difficulty == 1 else 5 if difficulty == 2 else 6
    
    current_word = random.choice(words_by_length(words, current_length))
    potential_words = get_all_potential_anagrams(current_word, words)
    score = 0

    while True:
        print(f"Current word: {current_word}")
        print(f"There are {len(potential_words)} potential answers.")
        player_word = input("Enter an anagram (enter 'q' to quit): ").strip().lower()
        
        if player_word == 'q':
            print(f"You gave up. Acceptable words would have been {sorted(potential_words)}")
            break
    
        if player_word in USED_WORDS:
            print("This word has already been used. Please try another.")
            continue
        
        if len(player_word) < 3:
            print("Words must be at least 3 letters.")
            continue
        
        if player_word in potential_words:
            print("Correct!")
            score += len(player_word)
            print(f"Your score is {score}\n")
            USED_WORDS.append(player_word)
            current_word = choose_next_word(player_word, words, difficulty)
            USED_WORDS.append(current_word)
            potential_words = get_all_potential_anagrams(current_word, words)
        else:
            print("Incorrect or invalid word. Try again.\n")
    
    print(f"Game over. Your score: {score}")

words = load_words()
play_game(words)
