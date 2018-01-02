import argparse
import time
import pygame
import sys
import curses
import random

t2 = """
"""

with open("words.txt",'r') as f:
    WORDS = f.read().split('\n')

def gen_word():
    category = random.randint(0,1)
    if (category or caps_only) and not numbers_only:
        word = random.choice(WORDS)
        mod = random.randint(0,2)
        if mod == 0 or caps_only:
            word = word.upper()
        if mod == 1:
            word = word[0].upper() + word[1:]
    else:
        word = str(random.randint(0,10000))
    return word

    
def gen_text(length=10):
    text = ' '.join([gen_word() for _ in range(length)])
    return text

def letter_score(letter):
    if letter == " ":
        return 5
    if letter in "0123456789":
        return 12
    if letter in "abcdefghijklmnopqrstuvwxyz":
        return 10
    if letter in "abcdefghijklmnopqrstuvwxyz":
        return 14
    return 16

def normalize_time(time):
    return time/30.

def compute_max_score(text):
    return sum([letter_score(letter) for letter in text])

def compute_score(text,errors,time):
    if time==0:
        return 0
    max_score = compute_max_score(text)
    return max_score/(errors+1)/normalize_time(time)

def run():
    curses.wrapper(main)

def main(screen):

    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, i, -1)

    screen.nodelay(True)
    screen.clear()

    pygame.init()
    pygame.display.set_mode((1,1))

    running = True

    text = ''
    cursor = 0
    errors = 0
    errored = False
    t0 = 0
    errors_history = []
    started = False

    prev_errors = 0
    dt = 0
    prev_dt = 0
    score = 0

    while running:
        if cursor == len(text):
            started = False
            prev_errors = errors
            prev_dt = dt
            score = compute_score(text,prev_errors,prev_dt)
            text = gen_text()
            cursor = 0
            errors = 0
            errors_history = []

        dt = time.time()-t0
        progress_string = ''.join(['*' if error else ' ' for error in errors_history])
        progress_string += '*' if errored else '|'
#         progress_string = ''.join(['|' if i==cursor else ' '  for i in range(len(text))])
        screen.erase()
        if quiet:
            screen.addstr(text[:cursor])
        else:
            screen.addstr(text[:cursor],curses.A_BOLD)
        screen.addstr(text[cursor:])
        screen.addstr('\n')
        screen.addstr(progress_string)
        screen.addstr('\n')
        screen.addstr(str(prev_errors))
        screen.addstr(' ')
        screen.addstr('{:.2f}'.format(prev_dt))
        screen.addstr(' ')
        screen.addstr(str(score))
        if not quiet:
            screen.addstr('\n')
            screen.addstr('{:.1f}'.format(dt))
        if quiet:
            screen.addstr('\n')
            screen.addstr(t2)
        screen.refresh()
        events = pygame.event.get()

        for event in events:
            if event.type==pygame.KEYDOWN:
                if not started:
                    started = True
                    t0 = time.time()
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.unicode == text[cursor]:
                    cursor += 1
                    errors_history.append(errored)
                    errored = False
                elif event.unicode != '' and not errored:
                    errors += 1
                    errored = True
                # print event
                # print event.unicode
        
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet",action="store_true")
    parser.add_argument("--caps-only",action="store_true")
    parser.add_argument("--numbers-only", action="store_true")

    args = parser.parse_args()
    quiet = args.quiet
    caps_only = args.caps_only
    numbers_only = args.numbers_only
    
    run()
        
    
