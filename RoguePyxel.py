"""
RoguePyxel
Pyxel-based roguelike game with a dedicated sidebar.
Right sidebar shows stats, messages, and a legend.
The left (game) area centers the grid.
This version now:
  1) Clears the initial instructions upon the first move.
  2) Progresses through enough stages so that you eventually meet the merchant 
     and face the high–level enemy (necromancer/dragon).
  3) When the player's health reaches 0, displays Game Over and prompts the user 
     to either exit (RETURN) or restart (R).
  4) The merchant shop no longer causes premature termination.
  5) All occurrences of "Ratsauyap" have been changed to "Payuwitta."
  6) When an enemy attacks the player, it moves back to its previous cell.
  7) In the merchant shop, only the M key is used to exit.
  8) When exiting the merchant shop, the player is repositioned to the grid center.
"""

# github.com/payu-witta

import pyxel
import random
import math

# ---------------------------
# Entity Classes
# ---------------------------
class Gate:
    def __init__(self):
        self.x = 0
        self.y = 0

class Stats:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.Level = 1
        self.Hits = 12
        self.MaxHits = 12
        self.Str = 8
        self.MaxStr = 8
        self.Gold = 0
        self.Armor = 5
        self.Exp = 0
        self.ExpCap = 1
        self.Inventory = []
        self.EquippedItems = []
        self.StatusEffect = ""
        self.Satiety = 100
        self.MoveCounter = 0

    def renew_stats(self):
        renew_point = 5
        if self.Hits <= int(0.5 * self.MaxHits):
            renew_point = 3
        if self.MoveCounter >= renew_point:
            if self.Hits < self.MaxHits:
                self.Hits += 1
            if self.Str < self.MaxStr:
                self.Str += 1
            if self.Satiety > 0:
                self.Satiety -= 1
            self.MoveCounter = 0
        if self.Satiety > 100:
            self.Satiety = 100
        elif 5 <= self.Satiety < 10:
            self.Hits -= 1
        elif 0 <= self.Satiety < 5:
            self.Hits -= 2

class Enemy:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.prev_x = 0   # Store previous x before moving
        self.prev_y = 0   # Store previous y before moving
        self.type = "Slime"
        self.MaxHits = 4
        self.Hits = 4
        self.Str = 1
        self.Armor = 1
        self.Level = 1

class Item:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.name = ""
        self.type = ""   # For example: ")", "[", "=", ":", "*", "?"
        self.Description = ""
        self.Hits = 0
        self.Str = 0
        self.Armor = 0
        self.Satiety = 30

# ---------------------------
# Main Game Class
# ---------------------------
class Game:
    def __init__(self):
        # Game state: "title", "game", "inventory", "merchant", "help", "gameover", "win"
        self.state = "title"
        self.messages = []  # Message log
        self.player_name = "Hero"
        self.player = Stats()

        # Flag to clear initial instructions upon the first move.
        self.first_move_done = False

        # Grid parameters (in cells)
        self.grid_width = 15
        self.grid_height = 10

        # Graphics parameters
        self.cell_size = 16  # each cell is 16x16 pixels

        # Sidebar parameters (fixed text area on the right)
        self.sidebar_width = 150

        # Define a left “game area” that is at least 400x300 pixels.
        self.game_area_width = max(self.grid_width * self.cell_size, 400)
        self.game_area_height = max(self.grid_height * self.cell_size, 300)

        # Total window dimensions: game area (left) + sidebar (right)
        self.window_width = self.game_area_width + self.sidebar_width
        self.window_height = self.game_area_height

        # Level management:
        self.level = 0
        self.level_sizes = []
        self.level_sizes.append([self.grid_width, self.grid_height])
        self.make_grid(self.grid_width, self.grid_height)
        self.gate_x, self.gate_y = self.make_dungeon_gate_coords()
        self.grid[self.gate_y][self.gate_x] = "𖡄"  # Gate symbol

        # Place player at the center of the grid.
        self.player.x = self.grid_width // 2
        self.player.y = self.grid_height // 2

        # Lists for enemies and items
        self.enemies = []
        self.items = []

        # Merchant store variables
        self.merchant_items = []
        self.merchant_selection = 0

        # Inventory selection cursor
        self.inventory_cursor = 0

        pyxel.init(self.window_width, self.window_height, title="RoguePyxel")
        pyxel.mouse(True)
        pyxel.run(self.update, self.draw)

    # ---------------------------
    # Grid and Level Creation
    # ---------------------------
    def make_grid(self, width, height):
        self.grid_width = width
        self.grid_height = height
        self.grid = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append(".")
            self.grid.append(row)
        # Place a gold coin ("G") at a random location (not at the center)
        gold_x, gold_y = width // 2, height // 2
        while (gold_x == width // 2 and gold_y == height // 2) or ((gold_x, gold_y) == (2, 0)):
            gold_x = random.randint(0, width - 1)
            gold_y = random.randint(0, height - 1)
        self.grid[gold_y][gold_x] = "G"

    def make_dungeon_gate_coords(self):
        gate = Gate()
        gate.x = self.grid_width // 2
        gate.y = self.grid_height // 2
        while self.grid[gate.y][gate.x] != "." or (gate.x == self.grid_width // 2 and gate.y == self.grid_height // 2):
            gate.x = random.randint(0, self.grid_width - 1)
            if gate.x == 0 or gate.x == self.grid_width - 1:
                gate.y = random.randint(0, self.grid_height - 1)
            else:
                gate.y = random.choice([0, self.grid_height - 1])
        return gate.x, gate.y

    # ---------------------------
    # Pyxel Update (60 fps)
    # ---------------------------
    def update(self):
        if self.state == "title":
            self.update_title()
        elif self.state == "game":
            self.update_game()
        elif self.state == "inventory":
            self.update_inventory()
        elif self.state == "merchant":
            self.update_merchant()
        elif self.state == "help":
            self.update_help()
        elif self.state == "gameover":
            if pyxel.btnp(pyxel.KEY_RETURN):
                pyxel.quit()
            elif pyxel.btnp(pyxel.KEY_R):
                self.restart_game()
        elif self.state == "win":
            if pyxel.btnp(pyxel.KEY_RETURN):
                pyxel.quit()
            elif pyxel.btnp(pyxel.KEY_R):
                self.restart_game()

    def update_title(self):
        if pyxel.btnp(pyxel.KEY_RETURN):
            self.state = "game"
            self.messages = []
            self.messages.append("Welcome, {}! Use arrow keys to move. (I: Inventory, H: Help)".format(self.player_name))

    def update_game(self):
        moved = False
        direction = ""
        if pyxel.btnp(pyxel.KEY_LEFT):
            direction = "LEFT"
            moved = True
        elif pyxel.btnp(pyxel.KEY_RIGHT):
            direction = "RIGHT"
            moved = True
        elif pyxel.btnp(pyxel.KEY_UP):
            direction = "UP"
            moved = True
        elif pyxel.btnp(pyxel.KEY_DOWN):
            direction = "DOWN"
            moved = True
        elif pyxel.btnp(pyxel.KEY_SPACE):
            direction = "NONE"
            moved = True

        if moved and not self.first_move_done:
            self.messages = []
            self.first_move_done = True

        if moved:
            self.move_player(direction)
            self.check_enemy_collision(player_move=True, direction=direction)
            dead = self.check_enemies_dead()
            for enemy in dead:
                self.messages.append("You defeated a {}!".format(enemy.type))
                self.player.Exp += enemy.Level
                drop_type = self.kill_enemy_reward(enemy)
                if drop_type:
                    item = self.generate_item([enemy.x, enemy.y], drop_type)
                    if item:
                        self.items.append(item)
            self.collect_items()
            self.player.renew_stats()
            self.player_level_up()
            if self.win_condition():
                self.state = "win"
            self.move_enemies()
            self.check_enemy_collision(player_move=False, direction="")
            if self.check_and_remove_object("G"):
                gold_found = random.randint(10, 50)
                self.player.Gold += gold_found
                self.messages.append("You found {} gold!".format(gold_found))
            # --- Gate & Stage Progression ---
            if self.player.x == self.gate_x and self.player.y == self.gate_y:
                self.level += 1
                new_width = random.randint(8, 15)
                new_height = random.randint(8, 15)
                self.level_sizes.append([new_width, new_height])
                self.make_grid(new_width, new_height)
                if self.level < 4:
                    self.gate_x, self.gate_y = self.make_dungeon_gate_coords()
                    self.grid[self.gate_y][self.gate_x] = "𖡄"
                if self.level == 3:
                    self.state = "merchant"
                    self.setup_merchant()
                    return
                self.enemies = self.generate_enemies(self.level)
                self.random_place_enemies()
                self.player.x = self.grid_width // 2
                self.player.y = self.grid_height // 2

        if self.player.Hits <= 0:
            self.state = "gameover"

        if pyxel.btnp(pyxel.KEY_I):
            self.state = "inventory"
        if pyxel.btnp(pyxel.KEY_H):
            self.state = "help"

    def move_player(self, direction):
        orig_x, orig_y = self.player.x, self.player.y
        if direction == "LEFT":
            self.player.x -= 1
        elif direction == "RIGHT":
            self.player.x += 1
        elif direction == "UP":
            self.player.y -= 1
        elif direction == "DOWN":
            self.player.y += 1

        if self.player.x < 0 or self.player.x >= self.grid_width or self.player.y < 0 or self.player.y >= self.grid_height:
            self.messages.append("You hit a wall!")
            self.player.x, self.player.y = orig_x, orig_y
        else:
            self.messages.append("Player moved to ({}, {})".format(self.player.x, self.player.y))
        self.player.MoveCounter += 1

    def check_and_remove_object(self, obj_symbol):
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.grid[y][x] == obj_symbol:
                    if self.player.x == x and self.player.y == y:
                        self.grid[y][x] = "."
                        return True
        return False

    # ---------------------------
    # Enemy Creation and Movement
    # ---------------------------
    def generate_enemies(self, level):
        enemy_list = []
        if level == 1:
            enemy_list.append(self.create_enemy("S"))
        elif level == 2:
            count = random.randint(2, 3)
            for i in range(count):
                enemy_list.append(self.create_enemy(random.choice(["S", "E", "Z", "B"])))
        elif level == 3:
            if random.randint(0, 1) == 0:
                enemy_list.append(self.create_enemy("I"))
                enemy_list.append(self.create_enemy("I"))
            else:
                for i in range(random.randint(2, 3)):
                    enemy_list.append(self.create_enemy(random.choice(["S", "E", "Z", "B"])))
                enemy_list.append(self.create_enemy("I"))
        elif level == 4:
            enemy_list.append(self.create_enemy("D"))
        return enemy_list

    def create_enemy(self, enemy_type):
        enemy = Enemy()
        if enemy_type == "S":
            enemy.type = "Slime"
        elif enemy_type == "E":
            enemy.type = "Emu"
            enemy.MaxHits = enemy.Hits = 6
            enemy.Str = 3
            enemy.Armor = 2
        elif enemy_type == "Z":
            enemy.type = "Zombie"
            enemy.MaxHits = enemy.Hits = random.randint(4, 7)
            enemy.Str = 3
            enemy.Level = 2
        elif enemy_type == "B":
            enemy.type = "Bat"
            enemy.Str = 3
        elif enemy_type == "I":
            enemy.type = "Ice Monster"
            enemy.Str = 5
            enemy.MaxHits = enemy.Hits = 12
            enemy.Armor = 4
            enemy.Level = 4
        elif enemy_type == "C":
            enemy.type = "Centaur"
            enemy.Str = random.randint(4, 6)
            enemy.MaxHits = enemy.Hits = 18
            enemy.Armor = 10
            enemy.Level = 5
        elif enemy_type == "R":
            enemy.type = "Rattlesnake"
            enemy.Str = 3
            enemy.MaxHits = enemy.Hits = random.randint(12, 16)
            enemy.Armor = 4
            enemy.Level = 4
        elif enemy_type == "D":
            enemy.type = "Dragon"
            enemy.Str = random.randint(15, 25)
            enemy.MaxHits = enemy.Hits = random.randint(30, 40)
            enemy.Armor = random.randint(10, 15)
            enemy.Level = 10
        else:
            enemy.type = "Necromancer"
            enemy.Str = random.randint(5, 8)
            enemy.MaxHits = enemy.Hits = random.randint(15, 22)
            enemy.Armor = random.randint(20, 25)
            enemy.Level = 10
        return enemy

    def random_place_enemies(self):
        for enemy in self.enemies:
            enemy.x, enemy.y = self.player.x, self.player.y
            while (enemy.x == self.player.x and enemy.y == self.player.y) or self.grid[enemy.y][enemy.x] != ".":
                enemy.x = random.randint(0, self.grid_width - 1)
                enemy.y = random.randint(0, self.grid_height - 1)

    def move_enemies(self):
        for enemy in self.enemies:
            enemy.prev_x = enemy.x
            enemy.prev_y = enemy.y
            direction = ""
            radius = int(5 / 9 * enemy.Level + 22 / 9)
            if enemy.x - radius <= self.player.x <= enemy.x + radius and enemy.y - radius <= self.player.y <= enemy.y + radius:
                if enemy.x < self.player.x and enemy.y == self.player.y and self.is_cell_empty(enemy.x+1, enemy.y):
                    direction = "RIGHT"
                elif enemy.x > self.player.x and enemy.y == self.player.y and self.is_cell_empty(enemy.x-1, enemy.y):
                    direction = "LEFT"
                elif enemy.x == self.player.x and enemy.y < self.player.y and self.is_cell_empty(enemy.x, enemy.y+1):
                    direction = "DOWN"
                elif enemy.x == self.player.x and enemy.y > self.player.y and self.is_cell_empty(enemy.x, enemy.y-1):
                    direction = "UP"
                elif enemy.x < self.player.x and enemy.y < self.player.y:
                    choices = []
                    if self.is_cell_empty(enemy.x+1, enemy.y):
                        choices.append("RIGHT")
                    if self.is_cell_empty(enemy.x, enemy.y+1):
                        choices.append("DOWN")
                    if choices:
                        direction = random.choice(choices)
                elif enemy.x > self.player.x and enemy.y < self.player.y:
                    choices = []
                    if self.is_cell_empty(enemy.x-1, enemy.y):
                        choices.append("LEFT")
                    if self.is_cell_empty(enemy.x, enemy.y+1):
                        choices.append("DOWN")
                    if choices:
                        direction = random.choice(choices)
                elif enemy.x < self.player.x and enemy.y > self.player.y:
                    choices = []
                    if self.is_cell_empty(enemy.x+1, enemy.y):
                        choices.append("RIGHT")
                    if self.is_cell_empty(enemy.x, enemy.y-1):
                        choices.append("UP")
                    if choices:
                        direction = random.choice(choices)
                else:
                    choices = []
                    if self.is_cell_empty(enemy.x-1, enemy.y):
                        choices.append("LEFT")
                    if self.is_cell_empty(enemy.x, enemy.y-1):
                        choices.append("UP")
                    if choices:
                        direction = random.choice(choices)
            else:
                choices = []
                if enemy.x > 0 and self.is_cell_empty(enemy.x-1, enemy.y):
                    choices.append("LEFT")
                if enemy.x < self.grid_width - 1 and self.is_cell_empty(enemy.x+1, enemy.y):
                    choices.append("RIGHT")
                if enemy.y > 0 and self.is_cell_empty(enemy.x, enemy.y-1):
                    choices.append("UP")
                if enemy.y < self.grid_height - 1 and self.is_cell_empty(enemy.x, enemy.y+1):
                    choices.append("DOWN")
                if choices:
                    direction = random.choice(choices)
            if direction == "LEFT":
                enemy.x -= 1
            elif direction == "RIGHT":
                enemy.x += 1
            elif direction == "UP":
                enemy.y -= 1
            elif direction == "DOWN":
                enemy.y += 1

    def is_cell_empty(self, x, y):
        if x < 0 or x >= self.grid_width or y < 0 or y >= self.grid_height:
            return False
        return self.grid[y][x] == "."

    def check_enemy_collision(self, player_move, direction):
        for enemy in self.enemies:
            if enemy.x == self.player.x and enemy.y == self.player.y:
                if player_move:
                    self.messages.append("Player attacked {}!".format(enemy.type))
                    player_damage = math.ceil(self.player.Str * random.randint(50, 100) / 100)
                    damage_to_enemy = math.ceil(player_damage * (100 / (100 + enemy.Armor)))
                    enemy.Hits -= damage_to_enemy
                    self.messages.append("Dealt {} damage to {}.".format(damage_to_enemy, enemy.type))
                    if direction == "LEFT":
                        self.player.x += 1
                    elif direction == "RIGHT":
                        self.player.x -= 1
                    elif direction == "UP":
                        self.player.y += 1
                    elif direction == "DOWN":
                        self.player.y -= 1
                else:
                    self.messages.append("{} attacked Player!".format(enemy.type))
                    enemy_damage = math.ceil(enemy.Str * random.randint(50, 100) / 100)
                    damage_to_player = math.ceil(enemy_damage * (100 / (100 + self.player.Armor)))
                    self.player.Hits -= damage_to_player
                    self.messages.append("Player took {} damage.".format(damage_to_player))
                    # Revert enemy to previous position after attack.
                    enemy.x = enemy.prev_x
                    enemy.y = enemy.prev_y

    def check_enemies_dead(self):
        dead = []
        for enemy in self.enemies[:]:
            if enemy.Hits <= 0:
                dead.append(enemy)
                self.enemies.remove(enemy)
        return dead

    def kill_enemy_reward(self, enemy):
        if enemy.type[0] not in ["N", "D"]:
            drop_chance = random.randint(0, 40 + 3 * enemy.Level + self.level)
            if random.randint(0, 100) <= drop_chance:
                return random.choice([")", "[", "=", ":"])
        else:
            return "?"
        return None

    def generate_item(self, coord, item_type):
        x, y = coord
        if x is None or y is None:
            x, y = self.player.x, self.player.y
            enemy_coords = [(e.x, e.y) for e in self.enemies]
            while (x == self.player.x and y == self.player.y) or ((x, y) in enemy_coords) or self.grid[y][x] != ".":
                x = random.randint(0, self.grid_width - 1)
                y = random.randint(0, self.grid_height - 1)
        item = Item()
        item.x, item.y = x, y
        if item_type == ")":
            item.name = random.choice(["Dagger", "Mace", "Shortsword", "Axe"])
            item.type = item_type
            item.Str = random.randint(2, 5)
            self.grid[y][x] = item.type
        elif item_type == "[":
            item.name = random.choice(["Buckler shield", "Kite shield", "Light shield"])
            item.type = item_type
            item.Armor = random.randint(5, 10)
            self.grid[y][x] = item.type
        elif item_type == "=":
            item.name = random.choice(["Vitality ring", "Blood ring", "Ring of zen"])
            item.type = item_type
            if item.name == "Vitality ring":
                item.Hits = random.randint(4, 6)
            elif item.name == "Blood ring":
                item.Hits = random.randint(7, 10)
            elif item.name == "Ring of zen":
                item.Hits = 20
            self.grid[y][x] = item.type
        elif item_type == "*":
            item.name = random.choice(["Frost gem", "Ruby gem", "Sky gem"])
            item.type = item_type
            if item.name == "Frost gem":
                item.Description = "A rare item worth many gold"
            elif item.name == "Ruby gem":
                item.Description = "Exceptionally scarce"
            elif item.name == "Sky gem":
                item.Description = "???"
            self.grid[y][x] = item.type
        elif item_type == ":":
            item.name = "Food"
            item.type = ":"
            self.grid[y][x] = item.type
        elif item_type == "?":
            item.name = "Amulet of Payuwitta"
            item.type = "?"
            self.grid[y][x] = item.type
        return item

    def collect_items(self):
        for item in self.items[:]:
            if self.player.x == item.x and self.player.y == item.y:
                self.player.Inventory.append(item)
                self.messages.append("You picked up {}!".format(item.name))
                self.items.remove(item)
                self.grid[item.y][item.x] = "."

    def player_level_up(self):
        while self.player.Exp >= self.player.ExpCap:
            self.player.Exp -= self.player.ExpCap
            self.player.Level += 1
            self.player.ExpCap += 1
            stat_to_increase = random.choice(["max hits", "max strength"])
            bonus = random.randint(3, 5)
            if stat_to_increase == "max hits":
                self.player.MaxHits += bonus
            else:
                self.player.MaxStr += bonus
            self.messages.append("Level up! {} increased by {}.".format(stat_to_increase, bonus))

    def win_condition(self):
        for item in self.player.Inventory:
            if item.type == "?":
                return True
        return False

    # ---------------------------
    # Inventory Management (state "inventory")
    # ---------------------------
    def update_inventory(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.inventory_cursor = max(0, self.inventory_cursor - 1)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.inventory_cursor = min(len(self.player.Inventory) - 1, self.inventory_cursor + 1)
        if pyxel.btnp(pyxel.KEY_U):
            if 0 <= self.inventory_cursor < len(self.player.Inventory):
                item = self.player.Inventory[self.inventory_cursor]
                if item.type == ":":
                    self.messages.append("You ate {}.".format(item.name))
                    self.player.Satiety += item.Satiety
                    self.player.Inventory.pop(self.inventory_cursor)
                elif item.type == "*":
                    self.messages.append("You equipped {} but nothing happened.".format(item.name))
                else:
                    if item not in self.player.EquippedItems:
                        if item.type == ")":
                            self.player.MaxStr += item.Str
                            self.player.Str += item.Str
                        elif item.type == "[":
                            self.player.Armor += item.Armor
                        else:
                            self.player.MaxHits += item.Hits
                            self.player.Hits += item.Hits
                        self.player.EquippedItems.append(item)
                        self.player.Inventory.pop(self.inventory_cursor)
                        self.messages.append("Equipped {}.".format(item.name))
        if pyxel.btnp(pyxel.KEY_O):
            if self.player.EquippedItems:
                item = self.player.EquippedItems.pop(0)
                self.player.Inventory.append(item)
                if item.type == ")":
                    self.player.MaxStr -= item.Str
                    self.player.Str -= item.Str
                elif item.type == "[":
                    self.player.Armor -= item.Armor
                else:
                    self.player.MaxHits -= item.Hits
                    self.player.Hits -= item.Hits
                self.messages.append("Unequipped {}.".format(item.name))
        if pyxel.btnp(pyxel.KEY_D):
            if 0 <= self.inventory_cursor < len(self.player.Inventory):
                item = self.player.Inventory.pop(self.inventory_cursor)
                self.messages.append("Discarded {}.".format(item.name))
                item.x, item.y = self.player.x, self.player.y
                self.grid[item.y][item.x] = item.type
                self.items.append(item)
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_I):
            self.state = "game"

    # ---------------------------
    # Merchant Store (state "merchant")
    # ---------------------------
    def setup_merchant(self):
        self.merchant_items = []
        sword = Item()
        sword.name = "Nightingale blade"
        sword.type = ")"
        sword.Str = random.randint(10, 18)
        shield = Item()
        shield.name = "Daedric shield"
        shield.type = "["
        shield.Armor = random.randint(15, 22)
        ring = Item()
        ring.name = "Havel's ring"
        ring.type = "="
        ring.Hits = random.randint(25, 30)
        self.merchant_items.extend([sword, shield, ring])
        self.merchant_selection = 0

    def update_merchant(self):
        if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT):
            self.merchant_selection = (self.merchant_selection + 1) % len(self.merchant_items)
        if pyxel.btnp(pyxel.KEY_RETURN):
            item = self.merchant_items[self.merchant_selection]
            if self.player.Gold >= 100:
                self.player.Gold -= 100
                self.player.Inventory.append(item)
                self.messages.append("Purchased {} with gold.".format(item.name))
                self.merchant_items.pop(self.merchant_selection)
            else:
                gem_found = False
                for inv_item in self.player.Inventory:
                    if "gem" in inv_item.name.lower():
                        self.player.Inventory.remove(inv_item)
                        gem_found = True
                        break
                if gem_found:
                    self.player.Inventory.append(item)
                    self.messages.append("Purchased {} with a gem.".format(item.name))
                    self.merchant_items.pop(self.merchant_selection)
                else:
                    self.messages.append("Not enough gold or gem!")
        if pyxel.btnp(pyxel.KEY_M):
            # Reposition the player to the grid center when exiting the merchant.
            self.player.x = self.grid_width // 2
            self.player.y = self.grid_height // 2
            self.state = "game"

    # ---------------------------
    # Help Screen (state "help")
    # ---------------------------
    def update_help(self):
        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_H):
            self.state = "game"

    # ---------------------------
    # Drawing (Pyxel's draw() function)
    # ---------------------------
    def draw(self):
        pyxel.cls(0)
        if self.state == "title":
            self.draw_title()
        elif self.state == "game":
            self.draw_game()
        elif self.state == "inventory":
            self.draw_inventory()
        elif self.state == "merchant":
            self.draw_merchant()
        elif self.state == "help":
            self.draw_help()
        elif self.state == "gameover":
            self.draw_gameover()
        elif self.state == "win":
            self.draw_win()

    def draw_title(self):
        pyxel.text(50, 50, "RoguePyxel", pyxel.COLOR_YELLOW)
        pyxel.text(40, 70, "Press RETURN to start", pyxel.COLOR_WHITE)

    def draw_game(self):
        # --- Draw the left game area ---
        grid_pixel_width = self.grid_width * self.cell_size
        grid_pixel_height = self.grid_height * self.cell_size
        grid_offset_x = (self.game_area_width - grid_pixel_width) // 2
        grid_offset_y = (self.window_height - grid_pixel_height) // 2
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                ch = self.grid[y][x]
                if self.player.x == x and self.player.y == y and self.player.Hits > 0:
                    ch = "P"
                else:
                    for enemy in self.enemies:
                        if enemy.x == x and enemy.y == y:
                            ch = enemy.type[0]
                    for item in self.items:
                        if item.x == x and item.y == y:
                            ch = item.type
                pyxel.text(grid_offset_x + x * self.cell_size + 4,
                           grid_offset_y + y * self.cell_size + 4,
                           ch, pyxel.COLOR_WHITE)
        pyxel.rectb(grid_offset_x, grid_offset_y, grid_pixel_width, grid_pixel_height, pyxel.COLOR_GREEN)

        # --- Draw the right sidebar ---
        sidebar_x = self.game_area_width
        pyxel.rect(sidebar_x, 0, self.sidebar_width, self.window_height, 0)
        pyxel.rectb(sidebar_x, 0, self.sidebar_width, self.window_height, pyxel.COLOR_WHITE)
        stats_lines = [
            "Stats:",
            "Lvl: {} ".format(self.player.Level),
            "Hits: {}/{}".format(self.player.Hits, self.player.MaxHits),
            "Str: {}/{}".format(self.player.Str, self.player.MaxStr),
            "Gold: {}".format(self.player.Gold),
            "Armor: {}".format(self.player.Armor),
            "Satiety: {}%".format(self.player.Satiety),
            "Exp: {}/{}".format(self.player.Exp, self.player.ExpCap)
        ]
        y_text = 4
        for line in stats_lines:
            pyxel.text(sidebar_x + 4, y_text, line, pyxel.COLOR_YELLOW)
            y_text += 10
        y_text += 4
        pyxel.text(sidebar_x + 4, y_text, "Messages:", pyxel.COLOR_CYAN)
        y_text += 10
        for msg in self.messages[-5:]:
            pyxel.text(sidebar_x + 4, y_text, msg, pyxel.COLOR_CYAN)
            y_text += 10
        legend_lines = [
            "Legend:",
            "P: Player",
            "G: Gold",
            "): Sword",
            "[: Shield",
            "=: Ring",
            ": : Food",
            "*: Jewelry",
            "𖡄: Gate",
            "A-Z: Enemy"
        ]
        legend_y = self.window_height - (len(legend_lines) * 10) - 4
        for line in legend_lines:
            pyxel.text(sidebar_x + 4, legend_y, line, pyxel.COLOR_ORANGE)
            legend_y += 10

    def draw_inventory(self):
        pyxel.cls(0)
        pyxel.text(10, 10, "Inventory (U: Use/Equip, O: Unequip, D: Discard, Esc/I: Exit)", pyxel.COLOR_WHITE)
        y = 30
        for idx, item in enumerate(self.player.Inventory):
            prefix = "-> " if idx == self.inventory_cursor else "   "
            text = "{}{}".format(prefix, item.name)
            pyxel.text(10, y, text, pyxel.COLOR_YELLOW)
            y += 10
        y += 10
        pyxel.text(10, y, "Equipped:", pyxel.COLOR_WHITE)
        y += 10
        for item in self.player.EquippedItems:
            pyxel.text(10, y, item.name, pyxel.COLOR_GREEN)
            y += 10

    def draw_merchant(self):
        pyxel.cls(0)
        pyxel.text(10, 10, "Merchant's Shop (RETURN: Buy, Left/Right: Choose, M: Exit)", pyxel.COLOR_WHITE)
        y = 30
        for i, item in enumerate(self.merchant_items):
            prefix = "-> " if i == self.merchant_selection else "   "
            text = "{}{}".format(prefix, item.name)
            pyxel.text(10, y, text, pyxel.COLOR_YELLOW)
            y += 10
        pyxel.text(10, y + 10, "Your Gold: {}".format(self.player.Gold), pyxel.COLOR_CYAN)

    def draw_help(self):
        pyxel.cls(0)
        help_lines = [
            "Arrow keys: Move",
            "Space: Wait",
            "I: Inventory",
            "H: Help",
            "Inventory: U = Use/Equip, O = Unequip, D = Discard, Esc/I = Exit",
            "Merchant: RETURN = Buy, Left/Right = Select, M = Exit"
        ]
        y = 30
        for line in help_lines:
            pyxel.text(10, y, line, pyxel.COLOR_WHITE)
            y += 10
        pyxel.text(10, y + 10, "Press Esc or H to return", pyxel.COLOR_CYAN)

    def draw_gameover(self):
        pyxel.cls(0)
        pyxel.text(50, 100, "Game Over!", pyxel.COLOR_RED)
        pyxel.text(20, 120, "Press RETURN to quit or R to restart", pyxel.COLOR_WHITE)

    def draw_win(self):
        pyxel.cls(0)
        pyxel.text(40, 100, "You found the Amulet of Payuwitta!", pyxel.COLOR_GREEN)
        pyxel.text(20, 120, "Press RETURN to quit or R to restart", pyxel.COLOR_WHITE)
        pyxel.text(20, 160, "github.com/payu-witta", pyxel.COLOR_WHITE)

    def restart_game(self):
        self.reset_state()

    def reset_state(self):
        # Reinitialize game variables without reinitializing Pyxel.
        self.state = "title"
        self.messages = []
        self.player_name = "Hero"
        self.player = Stats()
        self.first_move_done = False

        self.grid_width = 15
        self.grid_height = 10
        self.cell_size = 16
        self.sidebar_width = 150
        self.game_area_width = max(self.grid_width * self.cell_size, 400)
        self.game_area_height = max(self.grid_height * self.cell_size, 300)
        self.window_width = self.game_area_width + self.sidebar_width
        self.window_height = self.game_area_height

        self.level = 0
        self.level_sizes = []
        self.level_sizes.append([self.grid_width, self.grid_height])
        self.make_grid(self.grid_width, self.grid_height)
        self.gate_x, self.gate_y = self.make_dungeon_gate_coords()
        self.grid[self.gate_y][self.gate_x] = "𖡄"
        self.player.x = self.grid_width // 2
        self.player.y = self.grid_height // 2

        self.enemies = []
        self.items = []
        self.merchant_items = []
        self.merchant_selection = 0
        self.inventory_cursor = 0

# ---------------------------
# Start the Game
# ---------------------------
if __name__ == "__main__":
    Game()
