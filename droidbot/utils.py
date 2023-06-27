import json
import os
import random
import re
import functools
from datetime import datetime

LOGCAT_THREADTIME_RE = re.compile('^(?P<date>\S+)\s+(?P<time>\S+)\s+(?P<pid>[0-9]+)\s+(?P<tid>[0-9]+)\s+'
                                  '(?P<level>[VDIWEFS])\s+(?P<tag>[^:]*):\s+(?P<content>.*)$')

# input setting #避免输入有误无法顺利运行
EDIT_TEXT = {
        'default': [12, 123, 1234, 12345, 124, 1235],
        'note': ['test12', 'test123', 'test1234', 'test1235'],
        'pass': ['testTEST1234!'],
        'email': ['1127281406@qq.com'],
        'search': ['12'],
        'ISBN': ['9787553812403', '0764526448', '316148410X', '0306406152'],
}

def lazy_property(func):
    attribute = '_lazy_' + func.__name__

    @property
    @functools.wraps(func)
    def wrapper(self):
        if not hasattr(self, attribute):
            setattr(self, attribute, func(self))
        return getattr(self, attribute)

    return wrapper


def parse_log(log_msg):
    """
    parse a logcat message
    the log should be in threadtime format
    @param log_msg:
    @return:
    """
    m = LOGCAT_THREADTIME_RE.match(log_msg)
    if not m:
        return None
    log_dict = {}
    date = m.group('date')
    time = m.group('time')
    log_dict['pid'] = m.group('pid')
    log_dict['tid'] = m.group('tid')
    log_dict['level'] = m.group('level')
    log_dict['tag'] = m.group('tag')
    log_dict['content'] = m.group('content')
    datetime_str = "%s-%s %s" % (datetime.today().year, date, time)
    log_dict['datetime'] = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")

    return log_dict


def get_available_devices():
    """
    Get a list of device serials connected via adb
    :return: list of str, each str is a device serial number
    """
    import subprocess
    r = subprocess.check_output(["adb", "devices"])
    if not isinstance(r, str):
        r = r.decode()
    devices = []
    for line in r.splitlines():
        segs = line.strip().split()
        if len(segs) == 2 and segs[1] == "device":
            devices.append(segs[0])
    return devices


def weighted_choice(choices):
    import random
    total = sum(choices[c] for c in list(choices.keys()))
    r = random.uniform(0, total)
    upto = 0
    for c in list(choices.keys()):
        if upto + choices[c] > r:
            return c
        upto += choices[c]


def safe_re_match(regex, content):
    if not regex or not content:
        return None
    else:
        return regex.match(content)

def execute_cmd(cmd):
    with os.popen(cmd) as console:
        result = console.read()
    return result

def md5(input_str):
    import hashlib
    return hashlib.md5(input_str.encode('utf-8')).hexdigest()

def get_state_str_list(str):
    import re
    regex = r"'event_str': '(.+?)'"
    event_str_list = re.findall(regex, str)
    state_str_list = []
    pattern = r'state=([\w]+).*?\(([\w/ -]+)\)'
    for item in event_str_list:
        match = re.search(pattern, item)
        if match:
            state = match.group(1) or ''
            activity = match.group(2) or ''
            state_str_list.append(state + '/' + activity)

    return state_str_list

def get_event_str_list(str):
    regex = r"'event_str': '(.+?)'"
    event_str_list = re.findall(regex, str)
    return event_str_list

def kmp_search(pattern, text):
    n, m = len(text), len(pattern)
    if m == 0:
        return 0
    lps = [0] * m
    compute_lps(pattern, lps)
    i, j = 0, 0
    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1
        if j == m:
            return i - j
        elif i < n and pattern[j] != text[i]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    return -1

def compute_lps(pattern, lps):
    m = len(pattern)
    i, j = 1, 0
    while i < m:
        if pattern[i] == pattern[j]:
            j += 1
            lps[i] = j
            i += 1
        elif j != 0:
            j = lps[j - 1]
        else:
            lps[i] = 0
            i += 1

def get_semantic_sequences(app_path):
    semantic_sequences = {}
    if os.path.exists(app_path):
        for dir in os.listdir(app_path):
            seq_name = dir.split('.')[0]
            with open('%s\\%s'%(app_path, dir), 'r') as f:
                seq_list = [get_state_str_list(line.strip()) for line in f.readlines()]
                semantic_sequences[seq_name] = seq_list
    return semantic_sequences

def get_semantic_event_sequences(app_path):
    semantic_event_sequences = {}
    if os.path.exists(app_path):
        for dir in os.listdir(app_path):
            seq_name = dir.split('.')[0]
            with open('%s\\%s'%(app_path, dir), 'r') as f:
                seq_list = [get_event_str_list(line.strip()) for line in f.readlines()]
                semantic_event_sequences[seq_name] = seq_list
    return semantic_event_sequences

if __name__ == "__main__":
    semantic_sequences = get_semantic_sequences('F:\Applications\\apks\Tomdroid\semantic_sequence')
    print(semantic_sequences)
