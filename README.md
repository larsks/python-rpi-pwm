# Support for Raspberry Pi hardware PWM

This module provides an interface to the hardware PWM support
available on the Raspberry Pi.  This will give you far more precise
output than you can get using a software PWM driver.

## Example

This example will play a three-note tune on a piezo buzzer attached to
`pwn0` (pin 18):

    import rpi_pwm

    pwm = rpi_pwm.PWM('pwmchip0', 0)
    pwm.set_frequency(440)

You will probably need to be `root` for this to work, barring some
additional system configuration.
