#!/usr/bin/python3
"""
Python code to play a game with a command line, textual interface. In the game, an English word is randomly proposed (initially 4 letters). The player's job is to suggest an anagram of that word, also a valid English word, which must have either one more or one fewer letter than the original. The computer then suggests an anagram of that word with the same rules (one or fewer letter). Gameplay proceeds like this in turns. The user's score is counted based on how many turns they survive. There are three difficulty levels offered at the start of the game; the computer player chooses words that decrease or increase the player's likelihood of success based on the level.
"""

from functools import lru_cache
import os
import random
import requests
from collections import defaultdict, Counter
from typing import Literal

USED_WORDS = []

WORD_LIST_URL = "http://web.mit.edu/freebsd/head/share/dict/web2"
WORD_LIST_FILENAME = 'word_list_alpha.text'
DICTIONARY = None
INTRO_TEXT = """
Welcome to Nearagrams.

You will be shown a word. 
You need to enter a Nearagam: an English word that reuses all the letters from the last word, but has either one more or one fewer letter.
You will take turns back and forth with the computer until no more Nearagams are left.

You cannot reuse words and all words must be at least 3 letters.
Your score will be determined by how many words you find and how many letters they use.

Good luck!
"""

def load_words() -> list[str]:
    """Download a word list from the Internet and cache it to disk.
    """
    if not os.path.exists(WORD_LIST_FILENAME):
        print("Downloading word list...")
        response = requests.get(WORD_LIST_URL)
        if response.status_code == 200:
            with open(WORD_LIST_FILENAME, "w") as file:
                file.write(response.text)
        else:
            print("Failed to download the word list.")
            return []

    with open(WORD_LIST_FILENAME, "r") as file:
        all_words = file.read().split()

    return [word.strip().lower() for word in all_words if word.strip() and not word.strip()[0].isupper()]

def preprocess_words(words: list[str]) -> dict[str, list[str]]:
    """Preprocess words into a dict by length and letter counts."""
    processed = defaultdict(list)
    for word in words:
        processed[len(word)].append(word)
    return processed

def starts_with_non_capital(s: str) -> bool:
    return not s.split()[0][0].isupper()


PROCESSED_WORDS = None
@lru_cache
def get_anagrams(base_word: str) -> list[str]:
    """Returns a list of all words in PROCESSED_WORDS that are anagrams of the `base_word` with either
    one more or one fewer letter.
    
    Words must be at least 3 letters in lenth.
    """
    base_counter = Counter(base_word)
    potential_lengths = (
        [len(base_word) + 1] 
        if len(base_word) == 3
        else [len(base_word) - 1, len(base_word) + 1]
    )
    potential_anagrams = []

    for length in potential_lengths:
        for word in PROCESSED_WORDS[length]:
            counter = Counter(word)
            if word in USED_WORDS:
                continue
            if length < len(base_word):
                if not (counter - base_counter):
                    potential_anagrams.append(word)
            else:
                # This is the case where the new word is 1 letter longer than the original
                if (counter - base_counter).total() == 1:
                    potential_anagrams.append(word)
    
    return potential_anagrams

def choose_next_word(current_word: dict[str, list[str]], difficulty: Literal[1, 2, 3]) -> str:
    potential_words = get_anagrams(current_word)
    if not potential_words:
        return None

    if difficulty == 1:
        # Easy: prioritize words with more potential anagrams
        word_difficulties = [(word, len(get_anagrams(word))) for word in potential_words]
        word_difficulties.sort(key=lambda x: -x[1])
    elif difficulty == 3:
        # Hard: prioritize words with fewer potential anagrams
        word_difficulties = [(word, len(get_anagrams(word))) for word in potential_words]
        word_difficulties.sort(key=lambda x: x[1])
    else:
        # Medium: random choice
        word_difficulties = [(word, 0) for word in potential_words]

    choices = [word for word, _ in word_difficulties if word not in USED_WORDS]
    return random.choice(choices) if choices else None

def get_difficulty() -> Literal[1, 2, 3]:
    """Have the user enter a difficulty level
    """
    print("Difficulty levels: 1. Easy, 2. Medium, 3. Hard")
    difficulty = input("Choose difficulty (1-3): ")
    
    if not isinstance(difficulty, int) or difficulty not in [1, 2, 3]:
        print("Invalid difficulty. Defaulting to Medium.")
        difficulty = 2
    
    print(f"Proceeding with difficulty level={difficulty}")
    
    return int(difficulty)

def check_give_up(word: str, potential_words: list[str]) -> bool:
    if word == 'q':
        print(f"You gave up. Remaining Nearagrams were {sorted(potential_words)}")
        return True

def check_used_word(word: str) -> bool:
    if word in USED_WORDS:
        print("This word has already been used. Please try another.")
        return True

def check_too_short(word: str) -> bool:
    if len(word) < 3:
        print("Words must be at least 3 letters.")
        return True

def check_wrong_length(word: str, current_word: str) -> bool:
    if abs(len(word) - len(current_word)) != 1:
        print("Word must have one more or fewer letters than the original.")
        return True

def check_not_recognized(word: str) -> bool:
    if word not in DICTIONARY:
        print("Word is not in dictionary; pick another.")
        return True

def check_all_redos(player_word: str, current_word: str) -> bool:
    """Run all checks that result in a `continue`.
    """
    return (
        check_used_word(player_word) or 
        check_too_short(player_word) or
        check_wrong_length(player_word, current_word) or
        check_not_recognized(player_word)
    )

# Main game loop
def play_game(processed_words: dict[str, list[str]]):
    print(INTRO_TEXT)
    difficulty = get_difficulty()
    
    # Adjust difficulty
    current_length = 4 if difficulty == 1 else 5 if difficulty == 2 else 6
    
    current_word = random.choice(processed_words[current_length])
    potential_words = get_anagrams(current_word)
    score = 0

    while True:
        print(f"\nCurrent word: {current_word}")
        if len(potential_words) == 0:
            print("Game over! There are no more Nearagrams left.")
            break
        
        print(f"There are {len(potential_words)} Nearagrams.")
        player_word = input("Enter an anagram (enter 'q' to quit): ").strip().lower()
        
        if check_give_up(player_word, potential_words):
            break
    
        if check_all_redos(player_word, current_word):
            continue
        
        if player_word in potential_words:
            print("Correct!")
            score += len(player_word)
            print(f"Your score is {score}\n")
            USED_WORDS.append(player_word)
            current_word = choose_next_word(player_word, difficulty)
            USED_WORDS.append(current_word)
            potential_words = get_anagrams(current_word)
        else:
            print("Not a valid Neargram. Try again.")
    
    print(f"Game over. Your score: {score}")

if __name__ == "__main__":
    DICTIONARY = load_words()
    PROCESSED_WORDS = preprocess_words(DICTIONARY)
    play_game(PROCESSED_WORDS)
