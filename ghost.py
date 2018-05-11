import argparse
import pandas as pd
import curses

def run():
    curses.wrapper(main)

def init_curses(screen):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    for i in range(0, curses.COLORS):
        curses.init_pair(i+i, i, -1)

    screen.nodelay(True)
    screen.clear()

def init_sound():
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    pygame.display.set_mode((1,1))

    key_effect = pygame.mixer.Sound("keyboard_tap.wav")

    surf = pygame.Surface((32,32))
    pygame.display.set_icon(surf)

    return key_effect
    
def main(screen):

    init_curses(screen)
    key_effect = init_sound()

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ghost-id",type=int,default=None)

    args = parser.parse_args()

    run()
