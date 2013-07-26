#!/usr/bin/python2

import pyglet
from pyglet.window import key, mouse
from pyglet.gl import *

import ntplib
from numpy import pi, cos, sin, linspace, vstack, angle

import sys
from datetime import datetime, timedelta
from time import timezone, altzone, localtime
import threading

FONT = 'Droid Sans Bold'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
SCALE = 1.0                                 # million km per pixel

DIST_APH = 152.098232 / SCALE
DIST_PER = 147.098290 / SCALE
LONG_PER = 102.94719 / 180 * pi
LBD = DIST_APH + 80


def time_adjustment():
    response = ntplib.NTPClient().request('europe.pool.ntp.org', version=3)
    actual = datetime.utcfromtimestamp(response.tx_time)
    local = datetime.utcnow()
    return actual - local


def get_offset():
    offset = timezone if (localtime().tm_isdst == 0) else altzone
    return -offset


def create_circle(center, radius, N=60):
    th = linspace(0, 2*pi, N, endpoint=False)
    return vstack((center[0]+radius*cos(th), center[1]+radius*sin(th))).T.flatten()


def create_ellipse(center, minor, major, periapsis, N=60):
    a = (major + minor) / 2
    e = (major - minor) / (major + minor)
    th = linspace(0, 2*pi, N, endpoint=False)
    r = a * (1 - e**2) / (1 + e * cos(th - periapsis))
    return vstack((center[0] + r * cos(th), center[1] + r * sin(th))).T.flatten()


class TimekeeperWindow(pyglet.window.Window):

    def __init__(self):
        config = Config(sample_buffers=1, samples=4, depth_size=16, double_buffer=True)
        super(TimekeeperWindow, self).__init__(width=800, height=600, caption='Timekeeper', config=config)

        glEnable(GL_LINE_SMOOTH)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.panel_height = 35
        self.sunx = self.width/2
        self.suny = (self.height-self.panel_height) / 2
        self.angle, self.drag_angle = pi/3, 0.0
        self.labels = True
        self.adjustment = time_adjustment()

        self.utc_label = pyglet.text.Label('', font_name='Monospace', font_size=10,
                                           x=5, y=self.height-15)
        self.loc_label = pyglet.text.Label('', font_name='Monospace', font_size=10,
                                           x=5, y=self.height-30)
        self.jd_label = pyglet.text.Label('', font_name='Monospace', font_size=10,
                                           x=self.width/2+5, y=self.height-15)

        self.update()
        self.construct_system()
        self.recalc_system()

        pyglet.clock.schedule_interval(self.update, 0.5)

    def construct_system(self):
        self.sun_vl = pyglet.graphics.vertex_list(30,
            ('v2f/static', create_circle((self.sunx, self.suny), 20, N=30)),
            ('c3B/static', [255, 255, 0] * 30)
        )

        self.orbit_vl = pyglet.graphics.vertex_list(60, 'v2f', ('c3B', [160, 160, 160] * 60))
        self.helion_vl = pyglet.graphics.vertex_list(2, 'v2f', ('c3B', [70, 70, 70] * 2))
        self.perihelion_label = pyglet.text.Label('Perihelion', font_name=FONT, font_size=10,
            anchor_x='center', anchor_y='center')
        self.aphelion_label = pyglet.text.Label('Aphelion', font_name=FONT, font_size=10,
            anchor_x='center', anchor_y='center')

        self.equinox_vl = pyglet.graphics.vertex_list(2, 'v2f', ('c3B', [70, 70, 70] * 2))
        self.autumnal_label = pyglet.text.Label('Autumnal equinox', font_name=FONT, font_size=10,
            anchor_x='center', anchor_y='center')
        self.vernal_label = pyglet.text.Label('Vernal equinox', font_name=FONT, font_size=10,
            anchor_x='center', anchor_y='center')

        self.solstice_vl = pyglet.graphics.vertex_list(2, 'v2f', ('c3B', [70, 70, 70] * 2))
        self.south_label = pyglet.text.Label('Southern solstice', font_name=FONT, font_size=10,
            anchor_x='center', anchor_y='center')
        self.north_label = pyglet.text.Label('Northern solstice', font_name=FONT, font_size=10,
            anchor_x='center', anchor_y='center')

    def recalc_system(self):
        self.orbit_vl.vertices = create_ellipse((self.sunx, self.suny), 
                                                DIST_PER, DIST_APH, self.angle + LONG_PER)
        self.helion_vl.vertices = (self.sunx - LBD * cos(self.angle + LONG_PER),
                                   self.suny - LBD * sin(self.angle + LONG_PER),
                                   self.sunx + LBD * cos(self.angle + LONG_PER),
                                   self.suny + LBD * sin(self.angle + LONG_PER))
        self.equinox_vl.vertices = (self.sunx - LBD * cos(self.angle),
                                    self.suny - LBD * sin(self.angle),
                                    self.sunx + LBD * cos(self.angle),
                                    self.suny + LBD * sin(self.angle))
        self.solstice_vl.vertices = (self.sunx - LBD * cos(self.angle + pi/2),
                                     self.suny - LBD * sin(self.angle + pi/2),
                                     self.sunx + LBD * cos(self.angle + pi/2),
                                     self.suny + LBD * sin(self.angle + pi/2))
        self.perihelion_label.x = int(self.sunx + LBD * cos(self.angle + LONG_PER))
        self.perihelion_label.y = int(self.suny + LBD * sin(self.angle + LONG_PER))
        self.aphelion_label.x = int(self.sunx - LBD * cos(self.angle + LONG_PER))
        self.aphelion_label.y = int(self.suny - LBD * sin(self.angle + LONG_PER))
        self.autumnal_label.x = int(self.sunx + LBD * cos(self.angle))
        self.autumnal_label.y = int(self.suny + LBD * sin(self.angle))
        self.vernal_label.x = int(self.sunx - LBD * cos(self.angle))
        self.vernal_label.y = int(self.suny - LBD * sin(self.angle))
        self.south_label.x = int(self.sunx + LBD * cos(self.angle + pi/2))
        self.south_label.y = int(self.suny + LBD * sin(self.angle + pi/2))
        self.north_label.x = int(self.sunx - LBD * cos(self.angle + pi/2))
        self.north_label.y = int(self.suny - LBD * sin(self.angle + pi/2))

    def update(self, dt=0.0):
        utc = datetime.utcnow() + self.adjustment

        offset = get_offset()
        loc = utc + timedelta(seconds=offset)

        a = (14 - utc.month) / 12
        y = utc.year + 4800 - a
        m = utc.month + 12*a - 3
        jdn = utc.day + (153*m+2)/5 + 365*y + y/4 - y/100 + y/400 - 32045
        self.jd = jdn + (utc.hour-12)/24. + utc.minute/1440. + utc.second/86400.

        self.utc_label.text = utc.strftime('UTC:   ' + TIME_FORMAT)
        self.loc_label.text = loc.strftime('Local: ' + TIME_FORMAT) + ' (UTC %+05d)' % (offset/36)
        self.jd_label.text = 'Julian date: %.5f' % self.jd

    def on_draw(self):
        self.clear()

        self.utc_label.draw()
        self.loc_label.draw()
        self.jd_label.draw()

        pyglet.graphics.draw(2, GL_LINE_STRIP, ('v2i', (0, self.height-35, self.width, self.height-35)))

        if self.labels:
            self.helion_vl.draw(GL_LINE_STRIP)
            self.equinox_vl.draw(GL_LINE_STRIP)
            self.solstice_vl.draw(GL_LINE_STRIP)
            self.perihelion_label.draw()
            self.aphelion_label.draw()
            self.autumnal_label.draw()
            self.vernal_label.draw()
            self.north_label.draw()
            self.south_label.draw()

        self.orbit_vl.draw(GL_LINE_LOOP)
        self.sun_vl.draw(GL_POLYGON)

    def on_key_press(self, symbol, modifiers):
        if symbol == key.L:
            self.labels = not self.labels
        elif symbol == key.ESCAPE:
            sys.exit(0)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            self.drag_angle = self.angle - angle((x - self.sunx) + (y - self.suny) * 1j)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        if button == mouse.LEFT:
            self.angle = self.drag_angle + angle((x - self.sunx) + (y - self.suny) * 1j)
            self.recalc_system()


window = TimekeeperWindow()
pyglet.app.run()
