"""RFI flagging by applying the SIR (Scale-Invariant Rank) operator.

Inheritance diagram
-------------------

.. inheritance-diagram:: Sir
   :parts: 2

"""

import numpy as np
import timestream_task
from tlpipe.container.raw_timestream import RawTimestream
from tlpipe.container.timestream import Timestream
from tlpipe.rfi import sir_operator


class Sir(timestream_task.TimestreamTask):
    """RFI flagging by applying the SIR (Scale-Invariant Rank) operator.

    The scale-invariant rank (SIR) operator is a one-dimensional mathematical
    morphology technique that can be used to find adjacent intervals in the
    time or frequency domain that are likely to be affected by RFI.

    """

    params_init = {
                    'eta': 0.2,
                  }

    prefix = 'sir_'

    def process(self, ts):

        ts.redistribute('baseline')

        show_progress = self.params['show_progress']
        progress_step = self.params['progress_step']

        if isinstance(ts, RawTimestream):
            func = ts.bl_data_operate
        elif isinstance(ts, Timestream):
            if ts['vis_mask'].attrs.get('combined_mask', False):
                func = ts.bl_data_operate
            else:
                func = ts.pol_and_bl_data_operate

        func(self.operate, full_data=True, show_progress=show_progress, progress_step=progress_step, keep_dist_axis=False)

        return super(Sir, self).process(ts)

    def operate(self, vis, vis_mask, li, gi, tf, ts, **kwargs):
        """Function that does the actual operation."""

        eta = self.params['eta']

        # has_ns = ('ns_on' in ts.iterkeys())
        # if has_ns:
        #     ns_on = ts['ns_on'][:]
        #     mask_ns_on = vis_mask[ns_on]

        if 'ns_on' in ts.iterkeys():
            has_ns = True
            if len(ts['ns_on'].shape) == 1:
                on = ts['ns_on']
            elif len(ts['ns_on'].shape) == 2:
                on = ts['ns_on'][:, gi[1]]
            else:
                raise RuntimeError('ns_on must be a 1d or 2d array')
        else:
            has_ns = False

        if vis_mask.ndim == 2:
            mask = vis_mask.copy()
            # if has_ns and mask_ns_on.all():
            #     mask[ns_on] = False
            mask = sir_operator.vertical_sir(mask, eta)
            # if has_ns and mask_ns_on.all():
            #     mask[ns_on] = True
            vis_mask[:] = sir_operator.horizontal_sir(mask, eta)
        elif vis_mask.ndim == 3:
            # This shold be done after the combination of all pols
            mask = vis_mask[:, :, 0].copy()
            # if has_ns and mask_ns_on.all():
            #     mask[ns_on] = False
            mask = sir_operator.vertical_sir(mask, eta)
            # if has_ns and mask_ns_on.all():
            #     mask[ns_on] = True
            vis_mask[:] = sir_operator.horizontal_sir(mask, eta)[:, :, np.newaxis]
        else:
            raise RuntimeError('Invalid shape of vis_mask: %s' % vis_mask.shape)

        if has_ns:
            vis_mask[on] = False # undo ns_on mask