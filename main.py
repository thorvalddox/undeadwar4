import pygcurse
from collections import namedtuple
from math import floor, sqrt
from random import randrange
import json
from textwrap import wrap


class Graph:
    def __init__(self):
        self.window = pygcurse.PygcurseWindow(40, 30, 'Undead war')
        self.field = Field(self)
        self.log = Logger(self.window)
        self.infobox = Infobox(self.window)
        self.menu = Selectionbox(self.window)
        self.entities = []
        self.mana = [0, 50, 50]

    def end_turn(self):
        self.mana[1] += 5
        self.mana[2] += 5
        for e in self.entities:
            e.end_turn()
            if not e.unittype in (UnitTypes.mortal, UnitTypes.necromancer, UnitTypes.spirit) and e.team != 0:
                if self.mana[e.team] > 0:
                    self.mana[e.team] -= 1
                else:
                    e.kill()
            e.has_moved = False

    def update(self):
        self.field.draw(self.entities)
        self.field.surface.blitto(self.window._surfaceobj, self.window.gettopleftpixel(0, 0, True))
        self.window.update()

    def get_entities(self, x, y):
        for e in self.entities:
            if e.x == x and e.y == y:
                yield e

    def choose(self, choices):
        return self.menu.get_result(choices)

    def perform_player(self):
        while not all(e.has_moved for e in self.entities if e.team == 1):
            select = self.field.select_entity(1)
            select.perform_action()

    def turn(self):
        self.perform_player()
        self.end_turn()
        self.update()


class Logger:
    def __init__(self, parent):
        self.textbox = pygcurse.PygcurseTextbox(parent, (0, 20, 20, 30), 'white', 'maroon', "TEST", wrap=False,
                                                border=None)
        self.messages = []

    def message(self, text):
        self.messages.append(text)
        self.textbox.text = "\n".join(self.messages[-7:])
        self.textbox.update()


class Infobox:
    def __init__(self, parent):
        self.textbox = pygcurse.PygcurseTextbox(parent, (20, 0, 40, 20), 'white', 'maroon', "TEST", wrap=False,
                                                border=None)

    def set_info(self, text):
        self.textbox.text = "\n".join(text)
        self.textbox.update()


class Selectionbox:
    def __init__(self, parent):
        self.parent = parent
        self.textbox = pygcurse.PygcurseTextbox(parent, (20, 20, 20, 10), 'white', 'maroon', "TEST", wrap=False,
                                                border=None)

    def get_result(self, options):
        selection = 0
        key = ""
        while key != " ":
            if key == "w":
                selection -= 1
            elif key == "s":
                selection += 1
            selection = (selection + len(options)) % len(options)
            self.textbox.text = "\n".join(("> " if i == selection else "  ") + o for i, o in enumerate(options))
            self.textbox.update()
            self.parent.update()
            key = pygcurse.waitforkeypress()
        self.textbox.text = ""
        self.textbox.update()
        self.parent.update()
        return selection


def always_false(x, y):
    return False


class Field:
    def __init__(self, parent):
        self.parent = parent
        self.surface = pygcurse.PygcurseSurface(20, 20)
        self.surface.fill(" ", "black", (128, 255, 128))
        self.selx = 1
        self.sely = 1
        self.redcode = always_false

    def draw(self, entities):
        self.surface.fill(" ", "black", (128, 255, 128))

        for x in range(20):
            for y in range(20):
                if self.redcode(x, y):
                    self.surface.fill(" ", bgcolor=(255, 128, 128), region=(x, y, 1, 1))
        self.surface.fill(" ", bgcolor=(128, 128, 255), region=(self.selx, self.sely, 1, 1))
        for e in entities:
            self.surface.putchar(e.display(), e.x, e.y, ["gray", "blue", "red"][e.team])

    def select_tile(self, redcode=always_false):
        self.redcode = redcode
        key = ""
        while key != " ":

            if key == "w":
                self.sely -= 1
            elif key == "s":
                self.sely += 1
            elif key == "a":
                self.selx -= 1
            elif key == "d":
                self.selx += 1
            for e in self.parent.get_entities(self.selx, self.sely):
                e.show_right()
            self.parent.update()
            key = pygcurse.waitforkeypress()
        return (self.selx, self.sely)

    def select_entity(self, team,redcode=always_false):
        while True:
            self.select_tile(redcode=redcode)
            for e in self.parent.get_entities(self.selx, self.sely):
                if e.team == team and not e.has_moved:
                    return e

    def select_close_tile(self, entity, range_):
        return self.select_tile(redcode=lambda x,y:entity.can_move(x,y,range_))

    def select_close_entity(self, entity, range_):
        return self.select_entity(redcode=lambda x,y:entity.can_move(x,y,range_))

Stats = namedtuple("Stats", "hp,spd,degen")
Corps = namedtuple("Corps", "name,display,next,normal,special,void")

Unittype = namedtuple("Unittype", "name,display,stats")


class UnitTypes:
    mortal = Unittype("mortal", "A", Stats(20, 6, 0))
    necromancer = Unittype("necromancer", "N", Stats(20, 6, 0))
    vampire = Unittype("vampire", "v", Stats(20, 6, 0))
    moobane = Unittype("moonbane", "m", Stats(20, 6, 0))
    zombie = Unittype("zombie", "z", Stats(20, 5, 1))
    jianshi = Unittype("jianshi", "j", Stats(40, 2, 1))
    ghoul = Unittype("ghoul", "z", Stats(20, 3, 1))
    quell = Unittype("quell", "j", Stats(20, 3, 1))
    skeleton = Unittype("skeleton", "s", Stats(20, 5, 2))
    headless = Unittype("headless", "h", Stats(20, 6, 2))

    wraith = Unittype("wraith", "w", Stats(20, 6, 3))
    ghost = Unittype("ghost", "h", Stats(20, 6, 3))
    draugr = Unittype("draugr", "D", Stats(15, 3, 3))
    phantom = Unittype("phantom", "p", Stats(5, 2, 3))
    spirit = Unittype("spirit", "+", Stats(40, 7, 3))
    shadow = Unittype("ghost", "o", Stats(20, 8, 3))

    wright = Unittype("wright", "W", Stats(20, 6, 2))
    spectre = Unittype("spectre", "S", Stats(10, 7, 2))

    droughtling = Unittype("droughtling", "d", Stats(20, 4, 0))
    ashenhulk = Unittype("ashen hulk", "a", Stats(40, 2, 0))
    mummy = Unittype("mummy", "m", Stats(30, 5, 0))
    tangler = Unittype("tangler", "t", Stats(15, 7, 0))

    wreckspawn = Unittype("wreckspawn","V",Stats(5,2,0))


class Corpses:
    energy = Corps("Energy", "*", None, UnitTypes.spirit, UnitTypes.shadow, UnitTypes.spectre)
    smoke = Corps("Smoke", "p", energy, UnitTypes.phantom, UnitTypes.draugr, UnitTypes.spectre)
    dust = Corps("Dust", "w", smoke, UnitTypes.wraith, UnitTypes.ghost, UnitTypes.spectre)
    skeleton = Corps("Skeleton", "s", dust, UnitTypes.skeleton, UnitTypes.headless, UnitTypes.wright)
    fleshpile = Corps("Flesh pile", "g", skeleton, UnitTypes.ghoul, UnitTypes.quell, UnitTypes.wright)
    rotten = Corps("Rotten Corps", "z", fleshpile, UnitTypes.zombie, UnitTypes.jianshi, UnitTypes.wright)
    fresh = Corps("Fresh Corps", "v", rotten, UnitTypes.vampire, UnitTypes.moobane, UnitTypes.wright)
    burned = Corps("Burned Corps", "d", None, UnitTypes.vampire, UnitTypes.moobane, UnitTypes.mummy)
    bound = Corps("Bound Corps", "m", None, UnitTypes.vampire, UnitTypes.moobane, UnitTypes.tangler)


ELNAMES = ['piercing', 'bludgeoning', 'fire', 'magic']
DEGENERATION = ['intact', 'rotting', 'degenerated', 'incorporal']
BODYPARTS = ['arm', 'leg', 'upper body', 'lower body', 'head', 'critical']
OWNER = ['none', 'player', 'enemy']
INFO = json.load(open("lore.json"))


class Armor:
    def __init__(self, name, arm, leg, body, head):
        self.name = name
        self.defence = (arm, leg, body, body, head)
        self.degenmod = (1, 0.75, 0.5, 0)

    def get_degen_armor(self, degen):
        return ([floor(d * self.degenmod[degen]) for d in self.defence])

    def calculate_damage(self, raw_damage, bodypart, degen):
        if bodypart == 5:  # critical hit
            return 2 * raw_damage
        else:
            return max(1, raw_damage - self.get_degen_armor(degen)[bodypart])


class Weapon:
    def __init__(self, name, pierce, blud, fire):
        self.name = name
        self.damage = pierce, blud, fire
        self.degenmod = (1, 0.75, 0.5, 0)

    def get_degen_damage(self, degen):
        st_degen_damage = [floor(i * self.degenmod[degen]) for i in self.damage]
        tot_damage = sum(st_degen_damage)
        if tot_damage < 3:
            st_degen_damage[1] += 3 - tot_damage
        return st_degen_damage

    def calculate_raw_damage(self, weakness, degen, is_incorporal=False):
        if is_incorporal:
            return self.get_degen_damage(degen)[2] * 2
        st_degen_damage = self.get_degen_damage(degen)
        return sum(st_degen_damage) + st_degen_damage[weakness]


class Arsenal:
    pitchfork = Weapon("pitchfork", 6, 0, 0)
    club = Weapon("club", 0, 6, 0)
    torch = Weapon("torch", 0, 0, 6)
    tunic = Armor("tunic", 0, 0, 2, 0)


class Unit:
    def __init__(self, system, team, x, y, weapon, armor):
        self.has_moved = False
        self.system = system
        self.system.entities.append(self)
        self.team = team
        self.x = x
        self.y = y
        self.weapon = weapon
        self.armor = armor
        self.unittype = UnitTypes.mortal
        self.corpstype = Corpses.fresh
        self.alive = True
        self.damage = 0
        self.log = system.log.message

    @property
    def hp(self):
        return self.unittype.stats.hp - self.damage

    def is_alive(self):
        return self.alive and self.hp > 0

    def update(self):
        if self.alive and not self.is_alive():
            self.kill()

    def kill(self):
        self.alive = False
        self.unittype = None
        self.damage = 0
        self.team = 0

    def end_turn(self):
        self.update()
        self.perform_ability(Ability.on_end)
        if not self.alive:
            if randrange(6) == 0:
                self.decay

    def decay(self):
        if self.corpstype.next is not None:
            self.corpstype = self.corpstype.next

    def necro(self, team, special=False, void=False, forstype=None):
        self.team = team
        if forstype is not None:
            self.unittype = forstype
        elif void:
            self.unittype = self.corpstype.void
        elif special:
            self.unittype = self.corpstype.special
        else:
            self.unittype = self.corpstype.normal
        self.damage = 0
        self.perform_ability(Ability.on_summon)
        self.alive = True

    @property
    def weakness(self):
        return (0, 1, 1, 2)[self.degen]

    @property
    def is_incorporal(self):
        return self.degen == 3

    def attack(self, other, forseDamage=0):
        if forseDamage:
            damage = forseDamage
        else:
            damage = self.weapon.calculate_raw_damage(other.weakness, self.degen, other.is_incorporal)
        bodypart = randrange(6)
        realdamage = other.armor.calculate_damage(damage, bodypart, other.degen)
        self.log("{} hits {} in the {} ({})".format(self.unittype.name, other.unittype.name, BODYPARTS[bodypart],
                                                    realdamage))
        data = {"dam":realdamage}
        self.perform_ability(Ability.on_attack, other,data)
        other.perform_ability(Ability.on_defence, self,data)
        self.update()
        other.update()
        if not other.is_alive():
            self.perform_ability(Ability.on_kill,data)

    def perform_ability(self, type_, other=...):
        if other == ...:
            other = self
        type_.get(self.unittype, Unit.donothing)(self, other)

    def donothing(self, other):
        pass

    @property
    def degen(self):
        return self.unittype.stats.degen

    def get_armor(self):
        return self.armor.get_degen_armor(self.degen)

    def get_weapon(self):
        return self.weapon.get_degen_damage(self.degen)

    def unit_info(self):
        if self.alive:
            yield self.unittype.name
            yield "  {}".format(OWNER[self.team])
            yield "hp {:02}/{:02} spd {:01}".format(self.hp, self.unittype.stats.hp, self.unittype.stats.spd)
            yield "mana {:02}/{:02}".format(self.system.mana[self.team], 50)
            yield "{}".format(DEGENERATION[self.degen])
            yield "{}\n  {} {} {}".format(self.weapon.name, *self.get_weapon())
            yield "{}\n  {} {} {} {} {}".format(self.armor.name, *self.get_armor())
            yield from wrap(INFO.get(self.unittype.name, "no info availiable"), 20)
        else:
            yield self.corpstype.name

    def display(self):
        if self.alive:
            return self.unittype.display
        else:
            return self.corpstype.display

    def show_right(self):
        self.system.infobox.set_info(self.unit_info())

    def can_move(self, x, y, spd=...):
        if spd == ...:
            spd = self.unittype.stats.spd
        return distance((self.x, self.y), (x, y)) < spd

    def perform_action(self):
        if self.unittype != UnitTypes.necromancer:
            result = self.system.choose(("move", "attack"))
        else:
            result = self.system.choose(("move", "attack","cast spell"))
        if result == 0:
            newtile = self.system.field.select_close_tile(self,...)
            if self.can_move(*newtile):
                self.x, self.y = newtile
                self.has_moved = True
            self.log("{} has moved".format(self.unittype.name))
        elif result == 1:
            target = self.system.field.select_close_entity(self,1)
            if distance((self.x,self.y),(target.x,target.y)) <= 1:
                self.attack(target)
        elif result == 2:
            spells = list(Spell.all_.values())
            names = [i.name for i in spells]
            spell = spells[self.system.choose(names)]
            target_tile = self.system.field.select_close_tile(self, spell.range)
            if spell.can_cast(self,target_tile):
                spell.cast(self.system,self,target_tile)


class Ability:
    on_summon = {}
    on_activate = {}
    on_kill = {}
    on_defence = {}
    on_attack = {}
    on_end = {}

    @classmethod
    def create(cls, type_, name):
        def decorator(func):
            type_[name] = func
            return func

        return decorator


@Ability.create(Ability.on_kill, UnitTypes.vampire)
def ability(attacker: Unit, defender: Unit, data={}):
    if defender.unittype == UnitTypes.mortal:
        defender.necro(attacker.team, forstype=UnitTypes.vampire)

@Ability.create(Ability.on_kill, UnitTypes.jianshi)
def ability(attacker: Unit, defender: Unit, data={}):
    attacker.damage = 0

@Ability.create(Ability.on_attack, UnitTypes.zombie)
def ability(attacker: Unit, defender: Unit, data={}):
    defender.damage += 3

@Ability.create(Ability.on_attack, UnitTypes.moonbane)
def ability(attacker: Unit, defender: Unit, data={}):
    attacker.damage -= data["dam"]


class Spell:
    all_ = {}

    def __init__(self, name, manacost, range_, radius, targettype, onhit):
        self.name = name
        self.manacost = manacost
        self.range = range_
        self.radius = radius
        self.targettype = targettype
        self.onhit = onhit
        Spell.all_[self.name] = self

    def can_cast(self, caster, to_tile):
        return caster.system.mana[caster.team] > self.manacost and distance((caster.x, caster.y), to_tile) < self.range

    def cast(self, system, caster, target):
        assert self.can_cast(caster, target), 'Invalid spell casted'
        system.mana[caster.team] -= self.manacost
        x, y = target
        for e in system.entities:
            if distance((e.x, e.y), target) <= self.radius and \
                            self.targettype == ((0, 0, 0), (0, 1, 2), (0, 2, 1))[caster.team][e.team]:
                self.onhit(caster, e)

    @classmethod
    def create(cls, name, manacost, range_, radius, targettype):
        def decorator(func):
            return cls(name, manacost, range_, radius, targettype, func)

        return decorator


@Spell.create("summon", 10, 8, 0, 0)
def summon(self, target):
    target.necro(self.team)


@Spell.create("raise", 20, 8, 0, 0)
def summon_special(self, target):
    target.necro(self.team, special=True)

@Spell.create("voidshape", 10, 8, 0, 0)
def summon_special(self, target):
    target.necro(self.team, void=True)

def distance(f, t):
    fx, fy = f
    tx, ty = t
    return sqrt((tx - fx) * (tx - fx) + (ty - fy) * (ty - fy))


if __name__ == "__main__":
    g = Graph()

    s = Unit(g, 1, 5, 5, Arsenal.torch, Arsenal.tunic)
    s.unittype = UnitTypes.necromancer
    for _ in range(8):
        s = Unit(g, 2, randrange(20), randrange(20), Arsenal.torch, Arsenal.tunic)
        s.kill()

    while True:
        g.turn()
