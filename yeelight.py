import re
import socket


def _format_element(value):
    return f'"{value}"' if isinstance(value, str) else str(value)


def _format_params(params):
    return ', '.join([_format_element(v) for v in params])


def _format_message(cmd_id, method, params):
    return f'{{"id": {cmd_id},"method":"{method}","params":[{_format_params(params)}]}}\r\n'


def _check_duration(duration):
    if not isinstance(duration, int):
        raise "invalid duration - must be an integer type"
    if duration < 30:
        raise "duration must be at least 30ms"


def _check_effect(effect):
    if not (effect == "smooth" or effect == "sudden"):
        raise "invalid effect - must be 'smooth' or 'sudden'"


def _check_int_range(value_name, value, min_value, max_value):
    if not isinstance(value, int):
        raise f'{value_name} should be an integer'
    if value < min_value:
        raise f'{value_name} should be at least {min_value}'
    if max_value and value > max_value:
        raise f'{value_name} should not be larger than {max_value}'


POWERON_MODE_DEFAULT: int = 0
POWERON_MODE_CT: int = 1
POWERON_MODE_RGB: int = 2
POWERON_MODE_HSV: int = 3
POWERON_MODE_CF: int = 4

EFFECT_SMOOTH = 'smooth'
EFFECT_SUDDEN = 'sudden'

COLORFLOW_MODE_RECOVER: int = 0
COLORFLOW_MODE_RETAIN: int = 1
COLORFLOW_MODE_POWEROFF: int = 2

REPEAT_COUNT_INFINITE: int = 0


class Bulb:
    def __init__(self, bulb_ip, *, port=55443, cmd_id=0):
        self.bulb_ip = bulb_ip
        self.port = port
        self.cmd_id = cmd_id

        if isinstance(self.port, str):
            self.port = int(self.port)

        if not isinstance(self.bulb_ip, str):
            raise "bulb_ip must be a valid IP address"

        if not re.match(r'^([0-2]?[0-9]{1,2}\.){3}([0-2]?[0-9]{1,2})$', self.bulb_ip):
            raise "bulb_ip must be a valid IP address"

    def __str__(self):
        return f'YeelightBulb@{self.bulb_ip}:{self.port}'

    def __exec(self, command, params):
        self.cmd_id += 1
        try:
            msg = _format_message(self.cmd_id, command, params)
            tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp.connect((self.bulb_ip, self.port))
            try:
                print(msg)
                tcp.send(msg.encode('ascii'))
                resp = tcp.recv(2048)
                resp_str = resp.decode('ascii')
                print(resp_str)
            finally:
                tcp.close()
            return resp_str
        except Exception as e:
            raise "Unhandled error when attempting to send command"

    def toggle(self):
        self.__exec("toggle", [])

    def set_brightness(self, brightness):
        _check_int_range('brightness', brightness, 1, 100)
        self.__exec("set_bright", [brightness])

    def power_on(self, *, mode=POWERON_MODE_DEFAULT, effect=EFFECT_SMOOTH, duration=500):
        _check_duration(duration)
        _check_effect(effect)
        if mode not in [POWERON_MODE_DEFAULT, POWERON_MODE_CT, POWERON_MODE_HSV, POWERON_MODE_RGB, POWERON_MODE_CF]:
            raise "invalid poweron mode - must be POWERON_MODE_DEFAULT, POWERON_MODE_CT, POWERON_MODE_HSV, POWERON_MODE_RGB, or POWERON_MODE_CF"
        self.__exec("set_power", ['on', effect, duration, mode])

    def power_off(self, *, effect=EFFECT_SMOOTH, duration=500):
        _check_duration(duration)
        _check_effect(effect)
        self.__exec("set_power", ['off', effect, duration, POWERON_MODE_DEFAULT])

    def set_color_temp(self, ct_value, *, effect=EFFECT_SMOOTH, duration=500):
        _check_duration(duration)
        _check_effect(effect)
        _check_int_range('ct_value', ct_value, 1700, 6500)
        self.__exec("set_ct_abx", [ct_value, effect, duration])

    def set_color(self, red, green, blue, *, effect=EFFECT_SMOOTH, duration=500):
        _check_int_range('red', red, 0, 255)
        _check_int_range('green', green, 0, 255)
        _check_int_range('blue', blue, 0, 255)
        _check_effect(effect)
        _check_duration(duration)
        color_code = red * 65536 + green * 256 + blue
        self.__exec("set_rgb", [color_code, effect, duration])

    def set_hsv(self, hue, sat, *, effect=EFFECT_SMOOTH, duration=500):
        _check_int_range('hue', hue, 0, 359)
        _check_int_range('sat', sat, 0, 100)
        _check_effect(effect)
        _check_duration(duration)
        self.__exec("set_hsv", [hue, sat, effect, duration])

    def set_name(self, name):
        if not isinstance(name, str):
            raise 'invalid name - should be a string object'
        if not re.match(r'^[@A-Za-z0-9_][@A-Za-z0-9_ !&%()\[\]\-]*$', name):
            raise 'invalid name - should be name-like string'
        self.__exec("set_name", [name])

    def save_default(self):
        self.__exec("set_default", [])

    def cycle_color(self):
        self.__exec("set_adjust", ['circle', 'color'])

    def cycle_brightness(self):
        self.__exec("set_adjust", ['circle', 'bright'])

    def incr_brightness(self, *, up=True):
        if not isinstance(up, bool):
            raise 'up value must be a boolean value of True or False'
        self.__exec("set_adjust", ['increase' if up else 'decrease', 'bright'])

    def cycle_color_temp(self):
        self.__exec("set_adjust", ['circle', 'ct'])

    def incr_color_temp(self, *, up=True):
        if not isinstance(up, bool):
            raise 'up value must be a boolean value of True or False'
        self.__exec("set_adjust", ['increase' if up else 'decrease', 'ct'])

    def adjust_brightness(self, percent, *, duration=500):
        _check_int_range('percent', percent, -100, 100)
        _check_duration(duration)
        self.__exec("adjust_bright", [percent, duration])

    def adjust_color_temp(self, percent, *, duration=500):
        _check_int_range('percent', percent, -100, 100)
        _check_duration(duration)
        self.__exec("adjust_ct", [percent, duration])

    def adjust_color(self, percent, *, duration=500):
        _check_int_range('percent', percent, -100, 100)
        _check_duration(duration)
        self.__exec("adjust_color", [percent, duration])

    def run_color_flow(self, color_flow):
        if not isinstance(color_flow, ColorFlow):
            raise "color flow must be an instance of ColorFlow from this module"
        self.__exec("start_cf", color_flow.make_params())

    def stop_color_flow(self):
        self.__exec("stop_cf", [])

    def set_color_brightness(self, red, green, blue, brightness):
        _check_int_range('red', red, 0, 255)
        _check_int_range('green', green, 0, 255)
        _check_int_range('blue', blue, 0, 255)
        _check_int_range('brightness', brightness, 1, 100)
        color = red * 65536 + green * 256 + blue
        self.__exec("set_scene", ['color', color, brightness])

    def set_hsv_brightness(self, hue, sat, brightness):
        _check_int_range('hue', hue, 0, 359)
        _check_int_range('sat', sat, 0, 100)
        _check_int_range('brightness', brightness, 1, 100)
        self.__exec("set_scene", ['hsv', hue, sat, brightness])

    def set_color_temp_brightness(self, ct_value, brightness):
        _check_int_range('ct_value', ct_value, 1700, 6500)
        _check_int_range('brightness', brightness, 1, 100)
        self.__exec("set_scene", ['ct', ct_value, brightness])

    def set_brightness_and_delay_off(self, delay_in_minutes, brightness):
        _check_int_range('delay_in_minutes', delay_in_minutes, 1, None)
        _check_int_range('brightness', brightness, 1, 100)
        self.__exec("set_scene", ['auto_delay_off', brightness, delay_in_minutes])

    def set_delay_off(self, delay_in_minutes):
        _check_int_range('delay_in_minutes', delay_in_minutes, 1, None)
        self.__exec('cron_add', [0, delay_in_minutes])

    def cancel_delay_off(self):
        self.__exec('cron_del', [0])


class ColorFlow:
    def __init__(self, *, repeat_count=REPEAT_COUNT_INFINITE, action=COLORFLOW_MODE_RECOVER):
        _check_int_range('repeat_count', repeat_count, 0, None)
        if action not in [COLORFLOW_MODE_RECOVER, COLORFLOW_MODE_RETAIN, COLORFLOW_MODE_POWEROFF]:
            raise "invalid colorflow action - must be COLORFLOW_MODE_RECOVER, COLORFLOW_MODE_RETAIN, or COLORFLOW_MODE_POWEROFF"

        self.repeat_count = repeat_count
        self.action = action
        self.steps = []

    def add_color_step(self, red, green, blue, duration=500, brightness=None):
        _check_int_range('red', red, 0, 255)
        _check_int_range('green', green, 0, 255)
        _check_int_range('blue', blue, 0, 255)
        _check_duration(duration)
        if brightness is None:
            brightness = -1
        else:
            _check_int_range('brightness', brightness, 1, 100)

        mode = 1  # 'color' mode
        color = red * 65536 + green * 256 + blue
        self.steps.extend([duration, mode, color, brightness])

    def add_color_temp_step(self, ct_value, duration=500, brightness=None):
        _check_int_range('ct_value', ct_value, 1700, 6500)
        _check_duration(duration)
        if brightness is None:
            brightness = -1
        else:
            _check_int_range('brightness', brightness, 1, 100)

        mode = 2  # 'color temp' mode
        self.steps.extend([duration, mode, ct_value, brightness])

    def add_sleep_step(self, duration=500):
        _check_duration(duration)
        mode = 7  # 'sleep' mode
        self.steps.extend([duration, mode, 0, 0])

    def make_params(self):
        return [self.repeat_count, self.action, ','.join([str(s) for s in self.steps])]
