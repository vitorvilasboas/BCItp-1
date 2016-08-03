############################## DEPENDENCIES ##########################
# KIVY modules:
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, ListProperty
from kivy.clock import Clock
from kivy.lang import Builder

# KV file:
Builder.load_file('screens/game/barsstart.kv')

# Generic:
import math
import numpy as np

# Project's:
from SampleManager import *
from standards import *
from approach import Approach
######################################################################

class BarsStart(Screen):

    inst_prob_left = NumericProperty(0)
    accum_prob_left = NumericProperty(0)
    accum_color_left = ListProperty([1,0,0,1])

    inst_prob_right = NumericProperty(0)
    accum_prob_right = NumericProperty(0)
    accum_color_right = ListProperty([0,0,1,1])

    label_on_toggle_button = StringProperty('Start')

    current_label = NumericProperty(None)

    label_position = NumericProperty(-1)

    label_color = ListProperty([0,0,0,1])

    def __init__ (self, session_header,**kwargs):
        super (BarsStart, self).__init__(**kwargs)
        self.sh = session_header

        self.stream_flag = False

        self.U = 0.0

    # BUTTON CALLBACKS    
    # ----------------------
    def change_to_game(self,*args):

        self.manager.current = 'GameMenu'
        self.manager.transition.direction = 'right'

    def toogle_stream(self,*args):
        if self.stream_flag:
            self.stream_stop()
        else:
            self.stream_start()

    # ----------------------

    def stream_stop(self):
        self.sm.stop_flag = True
        self.stream_flag = False
        self.sm.join()
        self.label_on_toggle_button = 'Start'
        self.clock_unscheduler()
        self.set_bar_default()

    def stream_start(self):
        self.load_approach()
        self.sm = SampleManager(self.sh.com_port, self.sh.baud_rate, self.sh.channels,
            self.sh.buf_len, daisy=self.sh.daisy, mode = self.sh.mode, path = self.sh.path_to_file,
            labels_path = self.sh.path_to_labels_file)
        self.sm.daemon = True  
        self.sm.stop_flag = False
        self.sm.start()
        self.label_on_toggle_button = 'Stop'
        self.stream_flag = True
        self.clock_scheduler()


    def clock_scheduler(self):
        Clock.schedule_interval(self.get_probs, self.sh.window_overlap)
        Clock.schedule_interval(self.update_current_label, 1./20.)

    def clock_unscheduler(self):
        Clock.unschedule(self.get_probs)
        Clock.unschedule(self.update_current_label)


    def get_probs(self, dt):

        t, buf = self.sm.GetBuffData()

        if buf.shape[0] == self.sh.buf_len:

            p = self.ap.applyModelOnEpoch(buf.T, 'prob')[0]

            u = p[0] - p[1]

            self.U += u
 
            U1 = 100 * (self.U + self.sh.game_threshold) / (2. * self.sh.game_threshold)

            U2 = 100 - U1

            U1, U2 = self.map_probs(U1, U2)

            self.update_accum_bars(U1, U2)

            self.update_inst_bars(u)

            # print 'U: ', self.U
            # print 'U1: ', U1
            # print 'U2: ', U2
            # print 'u: ', u

    def update_inst_bars(self, u):
        if u > 0:
            self.inst_prob_left = int(math.floor(u * 100))
            self.inst_prob_right = 0
        else:
            self.inst_prob_right = int(math.floor(abs(u) * 100))
            self.inst_prob_left = 0

    def update_accum_bars(self, U1, U2):

        U1_n = int(math.floor(U1))
        U2_n = int(math.floor(U2))

        if U1_n > self.sh.warning_threshold:
            self.accum_color_left = [1,1,0,1]
        elif U2_n > self.sh.warning_threshold:
            self.accum_color_right = [1,1,0,1]
        else:
            self.accum_color_left = [1,0,0,1]
            self.accum_color_right = [0,0,1,1]

        self.accum_prob_left = U1_n
        self.accum_prob_right = U2_n

    def map_probs(self, U1, U2):

        if U1 > 100:
            self.set_bar_default()
            return 0,0

        elif U2 > 100:
            self.set_bar_default()
            return 0,0
            
        else:
            return U1, U2

            # dont send any cmd

    def set_bar_default(self):

        self.accum_prob_left = 0
        self.accum_prob_right = 0

        self.inst_prob_left = 0
        self.inst_prob_right = 0

        self.U = 0.0

    def update_current_label(self, dt):

        current_label_pos = int(self.sm.current_playback_label[1]) - self.sh.buf_len/2
        current_label = int(self.sm.current_playback_label[0])
        
        next_label_pos = int(self.sm.next_playback_label[1]) - self.sh.buf_len/2
        next_label = int(self.sm.next_playback_label[0])

        self.current_label = current_label

        tbuff, d = self.sm.GetBuffData()

        # print label_pos, min(tbuff), max(tbuff)
        if (next_label_pos in tbuff):
            idx = np.where(next_label_pos == tbuff)[0][0]
            ratio = float(idx) / float(self.sh.buf_len)
            self.label_position = ratio

            if next_label == 1:
                self.label_color = [1,0,0,1]
            elif next_label == 2:
                self.label_color = [0,0,1,1]
            else:
                self.label_color = [0,1,1,1]

        elif  current_label_pos in tbuff:
            idx = np.where(current_label_pos == tbuff)[0][0]
            ratio = float(idx) / float(self.sh.buf_len)
            self.label_position = ratio

            if current_label == 1:
                self.label_color = [1,0,0,1]
            elif current_label == 2:
                self.label_color = [0,0,1,1]
            else:
                self.label_color = [0,1,1,1]

        else:
            self.label_position = -1

    def load_approach(self):

        self.ap = Approach()
        self.ap.loadFromPkl(PATH_TO_SESSION + self.sh.name)






    


        