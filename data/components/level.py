import os
import sys
import pygame as pg

from operator import attrgetter
from .. import prepare,tools
from . import enemy


if sys.version_info[0] < 3:
    import yaml
else:
    import yaml3 as yaml


#Location on animsheet : number of frames in animation.
ANIMATED_TILES = {(0,0) : 2}


class Tile(pg.sprite.Sprite):
    """A basic tile."""
    def __init__(self, sheet, source, target, make_mask=False):
        """If the player can collide with it pass make_mask=True."""
        pg.sprite.Sprite.__init__(self)
        self.rect = pg.Rect(target, prepare.CELL_SIZE)
        self.sheet = prepare.GFX["mapsheets"][sheet]
        self.image = self.sheet.subsurface(pg.Rect(source, prepare.CELL_SIZE))
        if make_mask:
            self.mask = pg.mask.from_surface(self.image)


class Animated_Tile(Tile):
    """
    An animated tile. Animated tiles must be on the "animsheet" map sheet.
    """
    def __init__(self, source, target, frames, make_mask=False, fps=4.0):
        """
        The frames argument is the number of frames in the animation, and
        fps is the desired framerate of the animation.
        Currently only used for water.
        """
        Tile.__init__(self, "animsheet", source, target, make_mask)
        frames = tools.strip_from_sheet(self.sheet, source,
                                        prepare.CELL_SIZE, frames)
        self.anim = tools.Anim(frames, fps)

    def update(self, current_time):
        """Check if the image should change frame."""
        self.image = self.anim.get_next_frame(current_time)


class Level(object):
    """Class representing an individual map."""
    def __init__(self, player, map_name):
        self.player = player
        self.enemies = pg.sprite.Group()
        self.main_sprites = pg.sprite.Group(self.player)
        enemy.Cabbage((500,500), 0, "walk", self.enemies, self.main_sprites)
        enemy.Zombie((50,300), 200, "walk", self.enemies, self.main_sprites)
        enemy.Snake((850,300), 120, "walk", self.enemies, self.main_sprites)

        self.map_dict = self.load_map(map_name)
        self.background = self.make_background()
        self.layer_groups, self.solid_group = self.make_all_layer_groups()

    def load_map(self, map_name):
        """Load the map data from a resource file."""
        path = os.path.join(".", "resources", "map_data", map_name)
        with open(path) as myfile:
            return yaml.load(myfile)

    def make_background(self):
        """Create the background as one big surface."""
        background = pg.Surface((1000,700)).convert()
        background.fill(self.map_dict["BG Colors"]["fill"])
        for target in self.map_dict["BG Colors"]:
            if target != "fill":
                color = self.map_dict["BG Colors"][target][1]
                background.fill(color, pg.Rect(target, prepare.CELL_SIZE))
        self.map_dict.pop("BG Colors")
        return background

    def make_all_layer_groups(self):
        """Create sprite groups for all layers."""
        layer_groups = {}
        solid_group = pg.sprite.Group()
        for layer in ("Foreground", "BG Tiles"):
            layer_groups[layer] = self.make_tile_group(layer)
        for layer in ("Solid/Fore", "Solid", "Water"):
            layer_groups[layer] = self.make_tile_group(layer, True)
            solid_group.add(layer_groups[layer])
        return layer_groups, solid_group

    def make_tile_group(self, layer, make_mask=False):
        """
        Create a single sprite group for the selected layer.  Pass
        make_mask=True to create collision masks for the tiles.
        """
        group = pg.sprite.Group()
        for target in self.map_dict[layer]:
            sheet, source = self.map_dict[layer][target]
            if sheet == "animsheet":
                frames = ANIMATED_TILES[source]
                group.add(Animated_Tile(source, target, frames, make_mask))
            else:
                group.add(Tile(sheet, source, target, make_mask))
        return group

    def update(self, current_time, dt):
        """
        Update all tiles (currently only affects animated water).
        Then check any collisions that may have occured.
        """
        for layer in self.layer_groups:
            self.layer_groups[layer].update(current_time)
        self.enemies.update(current_time, dt, self.solid_group)
        self.check_collisions()

    def check_collisions(self):
        """
        Check collisions and call the appropriate functions of the affected
        sprites.
        """
        hits = pg.sprite.spritecollide(self.player, self.solid_group, False)
        collidable = pg.sprite.collide_mask
        if pg.sprite.spritecollideany(self.player, hits, collidable):
            self.player.collide_with_solid()
        enemy_collision = pg.sprite.spritecollideany(self.player, self.enemies)
        if enemy_collision:
            enemy_collision.collide_with_player(self.player)

    def draw(self,surface):
        """
        Draw all sprites and layers to the surface.  This may be greatly
        simplified if I implement layered sprite groups.
        """
        surface.fill(pg.Color("black"),(1000,0,200,700)) ###Until sidebar.
        surface.blit(self.background, (0,0))
        for layer in ("BG Tiles", "Water"):
            self.layer_groups[layer].draw(surface)
        for sprite in self.main_sprites:
            sprite.shadow.draw(surface)
        self.layer_groups["Solid"].draw(surface)
        for sprite in sorted(self.main_sprites, key=attrgetter("rect.y")):
            sprite.draw(surface)
        for layer in ("Solid/Fore", "Foreground"):
            self.layer_groups[layer].draw(surface)