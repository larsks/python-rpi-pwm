import os
from threading import Thread
import time


def play_tone(pwm, freq, duration):
    '''Play a single tone using pwm'''
    freq, duration = float(freq), float(duration)

    if freq == 0:
        time.sleep(duration)
        return

    set_frequency(pwm, freq)

    try:
        enable_output(pwm)
        time.sleep(duration)
    finally:
        disable_output(pwm)


def enable_output(pwm):
    '''Enable pwm output'''

    with open(os.path.join(pwm, 'enable'), 'wb') as fd:
        fd.write(b'1\n')


def disable_output(pwm):
    '''Disable pwm output'''
    with open(os.path.join(pwm, 'enable'), 'wb') as fd:
        fd.write(b'0\n')


def set_period(pwm, period, duty_cycle=0.5):
    '''Set pwm period (specified in ns)'''

    period_bytes = bytes('%s' % int(period), 'ascii')

    try:
        # try to reset duty_cycle, but ignore any errors (which
        # probably mean both period and duty_cycle were already
        # 0)
        set_duty_cycle(pwm, 0, 0)
    except OSError:
        pass

    with open(os.path.join(pwm, 'period'), 'wb') as fd:
        fd.write(period_bytes)
    set_duty_cycle(pwm, period, duty_cycle)


def set_duty_cycle(pwm, period, duty_cycle=0.5):
    if duty_cycle > 1 or duty_cycle < 0:
        raise ValueError('0 <= duty_cycle <= 1')

    duty_cycle = duty_cycle * period
    duty_cycle_bytes = bytes('%s' % int(duty_cycle), 'ascii')
    with open(os.path.join(pwm, 'duty_cycle'), 'wb') as fd:
        fd.write(duty_cycle_bytes)


def set_frequency(pwm, freq, **kwargs):
    '''Convert a frequency in Hz to a period in ns'''

    period = (1.0 / freq) * 1e+9
    set_period(pwm, period, **kwargs)


def play(pwm, tune, wait=False):
    def play_thread(pwm, tune):
        for freq, duration in tune:
            freq = float(freq)
            duration = float(duration)
            play_tone(pwm, freq, duration)

    t = Thread(target=play_thread, args=(pwm, tune))
    t.start()

    if wait:
        t.join()
