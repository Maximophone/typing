import re
import json
import argparse
import time
import pygame
import sys
import curses
import random
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import datetime as dt

t2 = """
"""

with open("words.txt",'r') as f:
    WORDS = f.read().split('\n')
WORDS = list(set([re.findall("[a-z]*",w)[0] for w in WORDS]))

WORDS_INDEX = {}
for i,word in enumerate(WORDS):
    for letter in word[:8]:
        WORDS_INDEX.setdefault(letter,set())
        WORDS_INDEX[letter].add(i)

LOWER_SYMBOLS = [
    "[{}]",
    "{};",
    "{}'{}",
    "#{}",
    "{},",
    "{}.",
    "{}/{}",
    "{}\{}",
    "{}-{}",
    "{}={}"
    ]

UPPER_SYMBOLS = [
    "({})",
    '"{}"',
    "{}!",
    "${}",
    "{}%",
    "{}&{}",
    "*{}",
    "{}_{}",
    "{}+{}",
    "{{{}}}",
    "@{}",
    "~{}",
    "<{}>",
    "{}?",
    "{}|{}"
    ]

class Modes:
    NUMBERS = "NUMBERS"
    NUMBERS_NO_MIDDLE = "NUMBERS_NO_MIDDLE"
    LOWER = "LOWER"
    CAPS = "CAPS"
    ALL = "ALL"
    ALL_LOWER = "ALL_LOWER"
    NO_SYMBOLS = "NO_SYMBOLS"
    SYMBOLS_ONLY = "SYMBOLS_ONLY"
    SYMBOLS_ONLY_LOWER = "SYMBOLS_ONLY_LOWER"
    SYMBOLS_ONLY_UPPER = "SYMBOLS_ONLY_UPPER"
    CUSTOM = "CUSTOM"

def sample_word(case="lower",cap=8,letters=None,letters_exclusive=False):
    if letters is None:
        indices = range(len(WORDS))
    else:
        if letters_exclusive:
            indices = list(set.intersection(*[WORDS_INDEX[letter] for letter in letters]))
        else:
            indices = list(set.union(*[WORDS_INDEX[letter] for letter in letters]))
    word = WORDS[random.choice(indices)]
    if case == "random":
        case = random.choice(["upper","lower","first"])
    if case == "lower":
        return word[:cap]
    elif case == "upper":
        return word.upper()[:cap]
    elif case == "first":
        return word[0].upper() + word[1:cap]
    else:
        raise Exception("Unknown case type")
    
def gen_symbol(upper=True,lower=True,case="lower",cap=8,letters=None,letters_exclusive=True):
    symbols = []
    if upper:
        symbols += UPPER_SYMBOLS
    if lower:
        symbols += LOWER_SYMBOLS

    return random.choice(symbols).format(sample_word(case=case,cap=cap,letters=letters,letters_exclusive=letters_exclusive),sample_word(case=case,cap=cap,letters=letters,letters_exclusive=letters_exclusive))

def gen_word(mode):
    num_voc = "0123456789"
    num_len = 4
    cap = 8
    letters = None
    letters_exclusive = True
    
    if mode == Modes.ALL:
        category = "random"
        upper_symbols = True
        lower_symbols = True
        case = "random"
    elif mode == Modes.NUMBERS:
        category = "number"
    elif mode == Modes.NUMBERS_NO_MIDDLE:
        category = "number"
        num_voc = "01234789"
    elif mode == Modes.CAPS:
        category = "word"
        upper_symbols = False
        lower_symbols = False
        case = "upper"
    elif mode == Modes.ALL_LOWER:
        category = "random"
        upper_symbols = False
        lower_symbols = True
        case = "lower"
    elif mode == Modes.LOWER:
        category = "word"
        upper_symbols = False
        lower_symbols = False
        case = "lower"
    elif mode == Modes.NO_SYMBOLS:
        category = "random"
        upper_symbols = False
        lower_symbols = False
        case = "random"
    elif mode == Modes.SYMBOLS_ONLY:
        category = "word"
        upper_symbols = True
        lower_symbols = True
        case = "lower"
        cap = 0
    elif mode == Modes.SYMBOLS_ONLY_LOWER:
        category = "word"
        upper_symbols = False
        lower_symbols = True
        case = "lower"
        cap = 0
    elif mode == Modes.SYMBOLS_ONLY_UPPER:
        category = "word"
        upper_symbols = True
        lower_symbols = False
        case = "lower"
        cap = 0
    elif mode == Modes.CUSTOM:
        category = args.category
        upper_symbols = args.upper_symbols
        lower_symbols = args.lower_symbols
        case = args.case
        cap = args.cap
        letters = args.letters
        letters_exclusive = args.exclusive
        num_voc = args.num_voc
        num_len = args.num_len
    else:
        raise Exception("Unknown Mode")

    if category == "random":
        category = random.choice(["word","word","number"])
    if category == "word":
        if upper_symbols or lower_symbols:
            return gen_symbol(upper=upper_symbols,lower=lower_symbols,case=case,cap=cap,letters=letters,letters_exclusive=letters_exclusive)
        else:
            return sample_word(case=case,cap=cap,letters=letters,letters_exclusive=letters_exclusive)
    elif category == "number":
        return ''.join([random.choice(num_voc) for _ in range(num_len)])
            

def gen_word_OLD():
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
        vocabulary = "1234567890"
        length = 4
        word = ''.join([random.choice(vocabulary) for _ in range(length)])
    return word

def wpm(time, length=10):
    if time == 0:
        return 0
    return length/time*60

def gen_text(mode,length=10):
    text = ' '.join([gen_word(mode) for _ in range(length)])
    return text

def letter_score(letter):
    if letter == " ":
        return 0
    if letter in "0123456789":
        return 20
    if letter in "abcdefghijklmnopqrstuvwxyz":
        return 10
    if letter in "abcdefghijklmnopqrstuvwxyz".upper():
        return 20
    return 25

def normalize_time(time):
    return time/30.

def compute_max_score(text):
    return sum([letter_score(letter) for letter in text])

def compute_score(text,errors,time):
    if time==0:
        return 0
    max_score = compute_max_score(text)
    return max_score/(errors+1)/normalize_time(time)

def get_cpm(full_history):
    if len(full_history) == 0:
        return 0.
    length = len([f for f in full_history if f[0] == "success"])
    return length/full_history[-1][2]*60.

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

def save_OLD(save_file, full_history, caps_only, numbers_only, lower_only):
    json_line = json.dumps({
        "datetime": "{}".format(dt.datetime.now()),
        "caps_only": caps_only,
        "numbers_only": numbers_only,
        "lower_only": lower_only,
        "full_history": full_history
        })
    with open(save_file,'a') as f:
        f.write(json_line+'\n')

def save(save_file, full_history, mode):
    json_line = json.dumps({
        "datetime": "{}".format(dt.datetime.now()),
        "caps_only":"-",
        "numbers_only":"-",
        "lower_only":"-",
        "mode":mode,
        "full_history": full_history
        })
    with open(save_file,'a') as f:
        f.write(json_line+'\n')

def old_to_mode(datum):
    if datum.get("caps_only"):
        return Modes.CAPS
    if datum.get("numbers_only"):
        return Modes.NUMBERS
    if datum.get("lower_only"):
        return Modes.LOWER
    else:
        return Modes.NO_SYMBOLS
    
        
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

    full_histories = [d.get("full_history") for d in data]

    x = np.arange(len(full_histories))
    
    scores = np.array([compute_score(fh) for fh in full_histories])
#    wpms = np.array([wpm(get_time(fh)) for fh in full_histories])
    n_errors = np.array([get_n_errors(fh) for fh in full_histories])
    cpms = np.array([get_cpm(fh) for fh in full_histories])

    MSIZE = 10
    ax1.set_title("Score")
    sns.regplot(x,scores,ax=ax1,scatter_kws={"s":MSIZE})
#    sns.regplot(x,wpms,ax=ax2,scatter_kws={"s":MSIZE})
    ax2.set_title("Errors")
    sns.regplot(x,n_errors,ax=ax2,scatter_kws={"s":MSIZE})
    ax3.set_title("CPM")
    sns.regplot(x, cpms, ax=ax3, scatter_kws={"s":MSIZE})
    
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

    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    pygame.display.set_mode((1,1))

    key_effect = pygame.mixer.Sound("keyboard_tap.wav")

    surf = pygame.Surface((32,32))
    pygame.display.set_icon(surf)
    
    running = True

    text = ''
    cursor = 0
    errors = 0
    errored = False
    t0 = 0
    errors_history = []
    full_history = []
    prev_history = []
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
                if not no_save:
                    save(save_file, full_history, mode)
            else:
                score = 0
            text = gen_text(mode)
            cursor = 0
            errors = 0
            errors_history = []
            prev_history = full_history[:]
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
        screen.addstr(' ')
        screen.addstr('{:.2f}'.format(get_cpm(prev_history)))
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
                                                mode=mode)
                    show_history(filtered_data)
                    continue
                else:
                    if not started:
                        started = True
                        t0 = time.time()
                    if event.unicode == text[cursor]:
                        key_effect.play()
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
    # parser.add_argument("--caps-only",action="store_true")
    # parser.add_argument("--numbers-only", action="store_true")
    # parser.add_argument("--lower-only", action="store_true")
    parser.add_argument("--save-file", default="save.txt", type=str)
    parser.add_argument("--no-save", action="store_true")
    parser.add_argument("--mode", default=Modes.ALL, type=str, choices=[Modes.ALL,Modes.LOWER,Modes.ALL_LOWER,Modes.CAPS, Modes.NUMBERS, Modes.SYMBOLS_ONLY, Modes.SYMBOLS_ONLY_UPPER, Modes.SYMBOLS_ONLY_LOWER,Modes.NUMBERS_NO_MIDDLE,Modes.CUSTOM])
    parser.add_argument("--symbols",type=str,default=None,help="Overwrite symbols list")
    parser.add_argument("--letters",type=str,default=None)
    parser.add_argument("--exclusive",type=int,default=1)
    parser.add_argument("--upper-symbols",type=int,default=1)
    parser.add_argument("--lower-symbols",type=int,default=1)
    parser.add_argument("--num-voc",type=str,default="1234567890")
    parser.add_argument("--num-len",type=int,default=4)
    parser.add_argument("--cap",type=int,default=8)
    parser.add_argument("--case",type=str,default="random")
    parser.add_argument("--category",type=str,default="random")
    
    args = parser.parse_args()
    quiet = args.quiet
    # caps_only = args.caps_only
    # numbers_only = args.numbers_only
    # lower_only = args.lower_only
    mode = args.mode
    save_file = args.save_file
    no_save = args.no_save
    
    run()
        
    
