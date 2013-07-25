#!/usr/bin/python2

import pyglet
from pyglet.window import key
from pyglet.gl import *

import ntplib
from numpy import pi, cos, sin, linspace, vstack

import sys
from datetime import datetime, timedelta
from time import timezone, altzone, localtime
import threading

TIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'


def get_time():
    return datetime.now()
    #response = ntplib.NTPClient().request('europe.pool.ntp.org', version=3)
    #return datetime.utcfromtimestamp(response.tx_time)


def get_offset():
    offset = timezone if (localtime().tm_isdst == 0) else altzone
    return -offset


def create_circle(center, radius, N=60):
    th = linspace(0, 2*pi, N, endpoint=False)
    return vstack((center[0]+radius*cos(th), center[1]+radius*sin(th))).T.flatten()


def update(dt):
    print 'update'
    pass


class TimekeeperWindow(pyglet.window.Window):

    def __init__(self):
        config = Config(sample_buffers=1, samples=4, depth_size=16, double_buffer=True)
        super(TimekeeperWindow, self).__init__(width=800, height=600, caption='Timekeeper', config=config)

        glEnable(GL_LINE_SMOOTH)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.utc_label = pyglet.text.Label('', font_name='Monospace', font_size=10,
                                           x=5, y=self.height-15)
        self.loc_label = pyglet.text.Label('', font_name='Monospace', font_size=10,
                                           x=5, y=self.height-30)

        self.sun_vl = pyglet.graphics.vertex_list(30,
            ('v2f/static', create_circle((self.width/2, self.height/2), 20, N=30)),
            ('c3B/static', [255, 255, 0] * 30)
        )

        self.interval = 5.0
        pyglet.clock.schedule_interval(update, self.interval)


    def update_times(self):
        utc = get_time()
        offset = get_offset()
        loc = utc + timedelta(seconds=offset)

        self.utc_label.text = utc.strftime('UTC:   ' + TIME_FORMAT)
        self.loc_label.text = loc.strftime('Local: ' + TIME_FORMAT) + ' (UTC %+05d)' % (offset/36)

    def on_draw(self):
        self.clear()

        self.update_times()
        self.utc_label.draw()
        self.loc_label.draw()

        pyglet.graphics.draw(2, GL_LINE_STRIP, ('v2i', (0, self.height-35, self.width, self.height-35)))

        self.sun_vl.draw(GL_POLYGON)

    def on_key_press(self, symbol, modifiers):
        if symbol == key.PLUS or symbol == key.NUM_ADD:
            self.interval += 1.0
            pyglet.clock.unschedule(update)
            pyglet.clock.schedule_interval(update, self.interval)
        elif symbol == key.MINUS or symbol == key.NUM_SUBTRACT:
            self.interval = max(self.interval-1.0, 1.0)
            pyglet.clock.unschedule(update)
            pyglet.clock.schedule_interval(update, self.interval)
        elif symbol == key.ESCAPE:
            sys.exit(0)


window = TimekeeperWindow()
pyglet.app.run()
