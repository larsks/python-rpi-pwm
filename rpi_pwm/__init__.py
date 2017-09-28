import os
from threading import Thread, RLock
import time

sysfs_pwm_base = '/sys/class/pwm'


class Player(Thread):
    def __init__(self, pwm, tune, callback=None, **kwargs):
        super().__init__(**kwargs)

        self.pwm = pwm
        self.tune = tune
        self.callback = callback

    def run(self):
        with self.pwm:
            try:
                self.pwm.stopflag = False
                for freq, pitch in self.tune:
                    self.pwm.play_tone(freq, pitch)
                    if self.pwm.stopflag:
                        break
            finally:
                self.pwm.disable()

            if self.callback is not None:
                self.callback(self)


class PWM(object):
    _pwms = {}

    def __new__(class_, chip, pwm):
        if not chip.startswith('/'):
            chip = os.path.join(sysfs_pwm_base, chip)

        key = (chip, pwm)
        if key in class_._pwms:
            return class_._pwms[key]

        class_._pwms[key] = object.__new__(class_)
        return class_._pwms[key]

    def __init__(self, chip, pwm):
        if not chip.startswith('/'):
            chip = os.path.join(sysfs_pwm_base, chip)

        self.chip = chip
        self.pwm = int(pwm)
        self.lock = RLock()
        self.is_playing = False

    def __enter__(self):
        self.lock.acquire()

    def __exit__(self, *args):
        self.lock.release()

    @property
    def path(self):
        return '{}/pwm{}'.format(self.chip, self.pwm)

    def export(self):
        if not self.is_exported():
            with open('{}/export'.format(self.chip), 'wb') as fd:
                fd.write(b'%d\n' % self.pwm)

    def unexport(self):
        if self.is_exported():
            with open('{}/unexport'.format(self.chip), 'wb') as fd:
                fd.write(b'%d\n' % self.pwm)

    def is_exported(self):
        return os.path.isdir(self.path)

    def play_tone(self, freq, duration):
        '''Play a single tone using pwm'''
        freq, duration = float(freq), float(duration)

        if freq == 0:
            time.sleep(duration)
            return

        self.set_frequency(freq)

        try:
            self.enable()
            time.sleep(duration)
        finally:
            self.disable()

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

    def stop(self):
        self.stopflag = True

    def play(self, tune, wait=False, callback=None):
        t = Player(self, tune)
        t.start()

        if wait:
            t.join()


def play(chip, pwm, tune):
    pwm = PWM(chip, pwm)
    pwm.play(tune, wait=True)
