import logging
import os
from threading import Thread, RLock
import time

LOG = logging.getLogger(__name__)
sysfs_pwm_base = '/sys/class/pwm'


class PWM(object):
    _pwms = {}

    def __new__(cls, chip, pwm):
        if not chip.startswith('/'):
            chip = os.path.join(sysfs_pwm_base, chip)

        key = (chip, pwm)
        if key in cls._pwms:
            return cls._pwms[key]

        cls._pwms[key] = object.__new__(cls)
        return cls._pwms[key]

    def __init__(self, chip, pwm):
        if not chip.startswith('/'):
            chip = os.path.join(sysfs_pwm_base, chip)

        self.chip = chip
        self.pwm = int(pwm)
        self.lock = RLock()

    def __str__(self):
        return '<PWM @ {0.chip}/pwm{0.pwm}>'.format(self)

    def __enter__(self):
        LOG.debug('entering context for %s', self)
        self.lock.acquire()

    def __exit__(self, *args):
        LOG.debug('leaving context for %s', self)
        self.lock.release()

    @property
    def path(self):
        return '{}/pwm{}'.format(self.chip, self.pwm)

    @property
    def is_exported(self):
        return os.path.isdir(self.path)

    def export(self):
        LOG.debug('exporting %s', self)
        if not self.is_exported:
            with open('{}/export'.format(self.chip), 'wb') as fd:
                fd.write(b'%d\n' % self.pwm)

    def unexport(self):
        LOG.debug('unexporting %s', self)
        if self.is_exported:
            with open('{}/unexport'.format(self.chip), 'wb') as fd:
                fd.write(b'%d\n' % self.pwm)

    def enable(self):
        '''Enable pwm output'''
        with open(os.path.join(self.path, 'enable'), 'wb') as fd:
            fd.write(b'1\n')

    def disable(self):
        '''Disable pwm output'''
        with open(os.path.join(self.path, 'enable'), 'wb') as fd:
            fd.write(b'0\n')

    def set_period(self, period, duty_cycle=0.5):
        '''Set pwm period (specified in ns)'''

        period_bytes = bytes('%s' % int(period), 'ascii')

        try:
            # try to reset duty_cycle, but ignore any errors (which
            # probably mean both period and duty_cycle were already
            # 0)
            self.set_duty_cycle(0, 0)
        except OSError:
            pass

        with open(os.path.join(self.path, 'period'), 'wb') as fd:
            fd.write(period_bytes)
        self.set_duty_cycle(period, duty_cycle)

    def set_duty_cycle(self, period, duty_cycle=0.5):
        if duty_cycle > 1 or duty_cycle < 0:
            raise ValueError('0 <= duty_cycle <= 1')

        duty_cycle = duty_cycle * period
        duty_cycle_bytes = bytes('%s' % int(duty_cycle), 'ascii')
        with open(os.path.join(self.path, 'duty_cycle'), 'wb') as fd:
            fd.write(duty_cycle_bytes)

    def set_frequency(self, freq, **kwargs):
        '''Convert a frequency in Hz to a period in ns'''

        period = (1.0 / freq) * 1e+9
        self.set_period(period, **kwargs)
