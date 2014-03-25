"""
Contains class for creating a new player and registering their name.
"""

import os
import sys
import copy
import pygame as pg

from .. import prepare, tools, state_machine


if sys.version_info[0] < 3:
    import yaml
else:
    import yaml3 as yaml


FONT = pg.font.Font(prepare.FONTS["Fixedsys500c"], 60)

MAX_LETTERS = 8

CURSOR = pg.Rect(292, 141, 41, 45)
CURSOR_SPACER = 82

HIGHLIGHT = pg.Rect(80, 270, 80, 85)
HIGHLIGHT_SPACER = (80, 75)
HIGHLIGHT_COLOR = pg.Color("darkslateblue")

ALPHAGRID = ["ABCDEFGHIJKLM",
             "NOPQRSTUVWXYZ",
             "abcdefghijklm",
             "nopqrstuvwxyz",
             "0123456789-"]

END_CELL = [12, 4]
BACKSPACE_CELL = [11, 4]


class Register(state_machine._State):
    """
    This State is updated while our game shows the name registration screen.
    """
    def __init__(self):
        state_machine._State.__init__(self)
        self.next = "SELECT"
        self.timer = tools.Timer(333)
        self.blink = True
        self.letter_images = {}

    def startup(self, now, persistant):
        """
        When this state is switched to, turn key-repeat on; set the alpha
        select cursor to the first position; and clear name.
        """
        state_machine._State.startup(self, now, persistant)
        pg.key.set_repeat(200,100)
        self.index = [0,0]
        self.name = []

    def save_new(self):
        """
        Save newly created player to the save data file.
        If the file doesn't exist it will be created.
        """
        player_data = copy.deepcopy(prepare.DEFAULT_PLAYER)
        player_data["name"] = "".join(self.name)
        try:
            with open(prepare.SAVE_PATH) as my_file:
                players = yaml.load(my_file)
        except IOError:
            players = ["EMPTY", "EMPTY", "EMPTY"]
        save_slot = self.persist["save_slot"]
        players[save_slot] = player_data
        with open(prepare.SAVE_PATH, 'w') as my_file:
            yaml.dump(players, my_file)

    def move_on_grid(self, event):
        """Called when user moves the selection cursor with the arrow keys."""
        direction = prepare.DEFAULT_CONTROLS[event.key]
        vector = prepare.DIRECT_DICT[direction]
        self.index[0] = (self.index[0]+vector[0])%len(ALPHAGRID[0])
        self.index[1] = (self.index[1]+vector[1])%len(ALPHAGRID)

    def select_from_grid(self):
        """Called if the user selects an item with the enter key(s)."""
        if self.index == END_CELL:
            if self.name:
                self.save_new()
                self.pressed_exit()
        elif self.index == BACKSPACE_CELL:
            if self.name:
                self.name.pop()
        elif len(self.name) < MAX_LETTERS:
            i, j = self.index
            letter = ALPHAGRID[j][i]
            self.name.append(ALPHAGRID[j][i])
            self.render_letter(letter)

    def pressed_exit(self):
        """
        Turn key-repeat off and return to menu.
        """
        self.done = True
        pg.key.set_repeat()

    def render_letter(self, letter):
        """
        If selected letter has not been cached, render it and place it
        in the letter_images dictionary.
        """
        if letter not in self.letter_images:
            rendered = FONT.render(letter, 0, pg.Color("yellow"))
            self.letter_images[letter] = rendered

    def render(self, surface):
        """
        Draw highlighter (in two parts); base screen; letter cursor; and
        currently entered name.
        """
        surface.fill(prepare.BACKGROUND_COLOR)
        move = [HIGHLIGHT_SPACER[i]*self.index[i] for i in (0,1)]
        surface.fill(HIGHLIGHT_COLOR, HIGHLIGHT.move(*move))
        surface.blit(prepare.GFX["misc"]["register"], (0,0))
        pg.draw.rect(surface, pg.Color("yellow"), HIGHLIGHT.move(*move), 5)
        if self.blink and len(self.name) < MAX_LETTERS:
            rect = CURSOR.move(CURSOR_SPACER*len(self.name), 0)
            surface.fill(pg.Color("white"), rect)
        for i,letter in enumerate(self.name):
            rect = CURSOR.move(CURSOR_SPACER*i, 0)
            surface.fill(prepare.BACKGROUND_COLOR, rect)
            surface.blit(self.letter_images[letter], rect)

    def get_event(self, event):
        """
        Navigate grid with arrow keys; confirm selections with enter keys;
        Cancel and return to previous menu with X or Escape.
        """
        if event.type == pg.KEYDOWN:
            if event.key in prepare.DEFAULT_CONTROLS:
                self.move_on_grid(event)
            elif event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                self.select_from_grid()
            elif event.key in (pg.K_x, pg.K_ESCAPE):
                self.pressed_exit()

    def update(self, surface, keys, now, dt):
        """
        Update cursor blink timer and draw the screen.
        """
        if self.timer.check_tick(now):
            self.blink = not self.blink
        self.render(surface)
