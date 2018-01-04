import json
import argparse
import time
import pygame
import sys
import curses
import random
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt

t2 = """
"""

with open("words.txt",'r') as f:
    WORDS = f.read().split('\n')

def gen_word():
    category = random.randint(0,1)
    if lower_only or ((category or caps_only) and not numbers_only):
        word = random.choice(WORDS)
        mod = random.randint(0,2)
        if lower_only:
            return word
        if mod == 0 or caps_only:
            word = word.upper()
        if mod == 1:
            word = word[0].upper() + word[1:]
    else:
        word = str(random.randint(0,10000))
    return word

def wpm(time, length=10):
    if time == 0:
        return 0
    return length/time*60

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

def get_time(full_history):
    return full_history[-1][2]

def get_n_errors(full_history):
    return sum([f[3] for f in full_history if f[0]=="success"])

def compute_score(full_history):
    n_errors = get_n_errors(full_history)
    time = get_time(full_history)
    max_score = sum([letter_score(f[1]) for f in full_history if f[0]=="success"])
    if time == 0:
        return 0
    return max_score/(n_errors+1)/normalize_time(time)

def save_OLD(save_file, score, time, errors, caps_only, numbers_only, lower_only):
    with open(save_file,'a') as f:
        f.write("{},{},{},{},{},{},{}\n".format(dt.datetime.now(), score, time, errors, caps_only, numbers_only, lower_only))

def save(save_file, full_history, caps_only, numbers_only, lower_only):
    json_line = json.dumps({
        "datetime": "{}".format(dt.datetime.now()),
        "caps_only": caps_only,
        "numbers_only": numbers_only,
        "lower_only": lower_only,
        "full_history": full_history
        })
    with open(save_file,'a') as f:
        f.write(json_line+'\n')

def get_df_from_save(save_file):
    return pd.read_csv(save_file, names=["dt","score","time","errors","caps","numbers","lower"])

def load_saved_data(save_file):
    with open(save_file,'r') as f:
        str_data = f.read()
    return [json.loads(s) for s in str_data.split('\n') if s!='']

def filter_data(data, **kwargs):
    return [d for d in data if all([d.get(k)==v for k,v in kwargs.items()])]

def filter_df(df, caps_only, numbers_only, lower_only):
    new_df = df[(df.caps == caps_only) & (df.numbers == numbers_only) & (df.lower == lower_only)]
    return new_df

def show_history_OLD(df):
    fig, (ax1, ax2, ax3) = plt.subplots(3,1,figsize=(8,8))

    df.score.plot(ax=ax1)
    df.time.apply(wpm).plot(ax=ax2)
    df.errors.plot(ax=ax3)

    plt.show()

def show_history(data):
    
    fig, (ax1, ax2, ax3) = plt.subplots(3,1,figsize=(8,8))

    ax1.plot([compute_score(d.get("full_history")) for d in data])
    ax2.plot([wpm(get_time(d.get("full_history"))) for d in data])
    ax3.plot([get_n_errors(d.get("full_history")) for d in data])

    plt.show()
        
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
    full_history = []
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
            if len(full_history) > 0:
                score = compute_score(full_history)
                save(save_file, full_history, caps_only, numbers_only, lower_only)
            else:
                score = 0
            text = gen_text()
            cursor = 0
            errors = 0
            errors_history = []
            full_history = []

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
        screen.addstr('{:.2f}'.format(wpm(prev_dt)))
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
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_F1:
                    data = load_saved_data(save_file)
                    filtered_data = filter_data(data,
                                              caps_only=caps_only,
                                              numbers_only=numbers_only,
                                              lower_only=lower_only)
                    show_history(filtered_data)
                    continue
                else:
                    if not started:
                        started = True
                        t0 = time.time()
                    if event.unicode == text[cursor]:
                        full_history.append(("success",text[cursor],time.time()-t0,errored))
                        cursor += 1
                        errors_history.append(errored)
                        errored = False
                    elif event.unicode != '' and not errored:
                        full_history.append(("error",event.unicode,time.time()-t0))
                        errors += 1
                        errored = True
                    
        
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet",action="store_true")
    parser.add_argument("--caps-only",action="store_true")
    parser.add_argument("--numbers-only", action="store_true")
    parser.add_argument("--lower-only", action="store_true")
    parser.add_argument("--save-file", default="save.txt", type=str)
    
    args = parser.parse_args()
    quiet = args.quiet
    caps_only = args.caps_only
    numbers_only = args.numbers_only
    lower_only = args.lower_only
    save_file = args.save_file
    
    run()
        
    
