"""Plot time or frequency integral.

Inheritance diagram
-------------------

.. inheritance-diagram:: Plot
   :parts: 2

"""

import numpy as np
from tlpipe.timestream import tod_task
from tlpipe.timestream.raw_timestream import RawTimestream
from tlpipe.timestream.timestream import Timestream
from tlpipe.utils.path_util import output_path
import matplotlib.pyplot as plt


class Plot(tod_task.TaskTimestream):
    """Plot time or frequency integral.

    This tasks plots the real, imagery part and the absolute value of the
    time or frequency integrated visibility for each baseline (and also each
    polarization if the input data is a
    :class:`~tlpipe.timestream.timestream.Timestream` instead of a
    :class:`~tlpipe.timestream.raw_timestream.RawTimestream`).

    """

    params_init = {
                    'integral': 'time', # or 'freq'
                    'bl_incl': 'all', # or a list of include (bl1, bl2)
                    'bl_excl': [],
                    'flag_mask': True,
                    'flag_ns': True,
                    'fig_name': 'int/int',
                  }

    prefix = 'pit_'

    def process(self, ts):

        ts.redistribute('baseline')

        if isinstance(ts, RawTimestream):
            func = ts.bl_data_operate
        elif isinstance(ts, Timestream):
            func = ts.pol_and_bl_data_operate

        func(self.plot, full_data=True, keep_dist_axis=False)

        ts.add_history(self.history)

        return ts

    def plot(self, vis, vis_mask, li, gi, bl, ts, **kwargs):
        """Function that does the actual plot work."""

        integral = self.params['integral']
        bl_incl = self.params['bl_incl']
        bl_excl = self.params['bl_excl']
        flag_mask = self.params['flag_mask']
        flag_ns = self.params['flag_ns']
        fig_prefix = self.params['fig_name']
        tag_output_iter = self.params['tag_output_iter']
        iteration= self.iteration

        if isinstance(ts, Timestream): # for Timestream
            pol = bl[0]
            bl = tuple(bl[1])
        elif isinstance(ts, RawTimestream): # for RawTimestream
            pol = None
            bl = tuple(bl)
        else:
            raise ValueError('Need either a RawTimestream or Timestream')

        if bl_incl != 'all':
            bl1 = set(bl)
            bl_incl = [ {f1, f2} for (f1, f2) in bl_incl ]
            bl_excl = [ {f1, f2} for (f1, f2) in bl_excl ]
            if (not bl1 in bl_incl) or (bl1 in bl_excl):
                return vis, vis_mask

        if flag_mask:
            vis1 = np.ma.array(vis, mask=vis_mask)
        elif flag_ns:
            if 'ns_on' in ts.iterkeys():
                vis1 = vis.copy()
                on = np.where(ts['ns_on'][:])[0]
                vis1[on] = complex(np.nan, np.nan)
            else:
                vis1 = vis
        else:
            vis1 = vis

        if integral == 'time':
            ax_val = ts.freq[:]
            vis1 = np.ma.mean(np.ma.masked_invalid(vis1), axis=0)
            xlabel = r'$\nu$ / MHz'
        elif integral == 'freq':
            ax_val = ts.time[:]
            vis1 = np.ma.mean(np.ma.masked_invalid(vis1), axis=1)
            xlabel = r'$t$ / Julian Date'
        else:
            raise ValueError('Unknown integral type %s' % integral)

        plt.figure()
        f, axarr = plt.subplots(3, sharex=True)
        axarr[0].plot(ax_val, vis1.real, label='real')
        axarr[0].legend()
        axarr[1].plot(ax_val, vis1.imag, label='imag')
        axarr[1].legend()
        axarr[2].plot(ax_val, np.abs(vis1), label='abs')
        axarr[2].legend()
        axarr[2].set_xlabel(xlabel)

        if pol is None:
            fig_name = '%s_%s_%d_%d.png' % (fig_prefix, integral, bl[0], bl[1])
        else:
            fig_name = '%s_%s_%d_%d_%s.png' % (fig_prefix, integral, bl[0], bl[1], pol)
        if tag_output_iter:
            fig_name = output_path(fig_name, iteration=iteration)
        else:
            fig_name = output_path(fig_name)
        plt.savefig(fig_name)
        plt.close()

        return vis, vis_mask
