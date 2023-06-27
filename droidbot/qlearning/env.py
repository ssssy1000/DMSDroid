import datetime
import time

from droidbot import utils


class Env(object):
    """
        Description:
            An app under test is running in an Android device.
            The agent will observe:
                1. the UI
                2. the current process status, e.g. listening broadcast receivers,
                    recently executed APIs, recently printed logs, etc.
            The agent can interact with the device by:
                1. sending a gesture
                2. sending a broadcast intent
                3. pressing a key
            The goal is to trigger as many sensitive behaviors in the app as possible in one episode.

        Observation: defined in observation.py

        Action: defined in action.py

        Reward:
            Reward is 1 for every sensitive behavior detected.
            A sensitive behavior is uniquely identified based on the API name (and the stack trace?).

        Starting State:
            All initial observations are obtained right after the app is installed and started.

        Episode Termination:
            Step limit is exceeded.
            Timeout.
        """
    metadata = {
        'episode.step_limit': 20,          # maximum number of steps in an episode
        'episode.timeout': 60,             # maximum duration of an episode
        'step.n_events': 1,                 # number of events per step
        'step.wait': 0,                     # time in seconds to wait after each input event
    }

    def __init__(self, device, app, output):
        self.device = device
        self.output = output
        # change follow the diver
        self.package = app.get_package_name()
        self.activity = app.get_main_activity()

    def stop_app(self, package):
        cmd = 'adb -s ' + self.device.serial + ' shell am force-stop ' + package
        utils.execute_cmd(cmd)

    def start_app(self):
        cmd = 'adb -s ' + self.device.serial + " shell am start " + self.package + "/" + self.activity
        utils.execute_cmd(cmd)
        time.sleep(1)

    # 重启app
    def restart_app(self, cur_app):
        self.stop_app(cur_app)
        self.start_app()
        time.sleep(1)

    def step(self, action):
        # 执行操作action
        self.device.send_event(action)
        time.sleep(1)

    def exit(self):
        print('探索结束')
