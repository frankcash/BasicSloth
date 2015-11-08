#!/usr/bin/env python2
##################################################
# GNU Radio Python Flow Graph
# Title: rx-PSK
# Generated: Sun Nov  8 02:42:38 2015
##################################################

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import wxgui
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.wxgui import constsink_gl
from grc_gnuradio import wxgui as grc_wxgui
from optparse import OptionParser
import osmosdr
import time
import wx


class rxPSK(grc_wxgui.top_block_gui):

    def __init__(self):
        grc_wxgui.top_block_gui.__init__(self, title="rx-PSK")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 24000

        ##################################################
        # Blocks
        ##################################################
        self.wxgui_constellationsink2_0 = constsink_gl.const_sink_c(
        	self.GetWin(),
        	title="Constellation Plot",
        	sample_rate=samp_rate,
        	frame_rate=5,
        	const_size=2048,
        	M=4,
        	theta=0,
        	loop_bw=6.28/100.0,
        	fmax=0.06,
        	mu=0.5,
        	gain_mu=0.005,
        	symbol_rate=samp_rate/4.,
        	omega_limit=0.005,
        )
        self.Add(self.wxgui_constellationsink2_0.win)
        self.osmosdr_source_0 = osmosdr.source( args="numchan=" + str(1) + " " + "" )
        self.osmosdr_source_0.set_sample_rate(samp_rate)
        self.osmosdr_source_0.set_center_freq(415e6, 0)
        self.osmosdr_source_0.set_freq_corr(0, 0)
        self.osmosdr_source_0.set_dc_offset_mode(0, 0)
        self.osmosdr_source_0.set_iq_balance_mode(0, 0)
        self.osmosdr_source_0.set_gain_mode(False, 0)
        self.osmosdr_source_0.set_gain(10, 0)
        self.osmosdr_source_0.set_if_gain(20, 0)
        self.osmosdr_source_0.set_bb_gain(20, 0)
        self.osmosdr_source_0.set_antenna("", 0)
        self.osmosdr_source_0.set_bandwidth(0, 0)
          
        self.digital_psk_demod_0 = digital.psk.psk_demod(
          constellation_points=8,
          differential=True,
          samples_per_symbol=2,
          excess_bw=0.35,
          phase_bw=6.28/100.0,
          timing_bw=6.28/100.0,
          mod_code="gray",
          verbose=True,
          log=True,
          )
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, "/Users/majora/Code/BasicSloth/in.dat", False)
        self.blocks_file_sink_0.set_unbuffered(False)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.digital_psk_demod_0, 0), (self.blocks_file_sink_0, 0))    
        self.connect((self.osmosdr_source_0, 0), (self.digital_psk_demod_0, 0))    
        self.connect((self.osmosdr_source_0, 0), (self.wxgui_constellationsink2_0, 0))    


    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.osmosdr_source_0.set_sample_rate(self.samp_rate)
        self.wxgui_constellationsink2_0.set_sample_rate(self.samp_rate)


if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    tb = rxPSK()
    tb.Start(True)
    tb.Wait()
