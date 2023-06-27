import os
import time
from .agent import Agent
from .env import Env
from droidbot import device, utils

STAGE_ONE_TIME = 1800

class QExploration(object):
    def __init__(self, device, app, explor_path):
        self.device = device
        self.env = Env(self.device, app, explor_path)

        self.app_path = explor_path
        self.app = app
        self.app_package = app.get_package_name()
        self.semantic_sequences = utils.get_semantic_sequences(explor_path + '\semantic_sequence')
        self.semantic_event_sequences = utils.get_semantic_event_sequences(explor_path + '\semantic_sequence')
        self.agent = Agent(device, self.semantic_sequences, self.semantic_event_sequences, explor_path)
        # self.logcat_thread = Thread(target=self.logcat_tasks.run)
        # self.coverage_thread = Thread(target=self.coverage_tasks.run)

    def start(self):
        print('qlearning start')
        self.env.restart_app(self.app_package)
        # step1: observe state and sample action in state
        state_t = self.agent.observe_env()
        action_t = self.agent.choose_action(state_t)
        # record the state sequence
        seq = [self.generate_state_semantic_str(state_t, action_t)]
        seq_state = [state_t.structure_str]
        test_case = []

        self.start_time = time.time()
        while time.time() - self.start_time <= STAGE_ONE_TIME:
            self.check_current_app()
            # 如果测试用例太长（100个action），重新开始
            if len(test_case) >= 100:
                self.env.restart_app(self.app_package)
                state_t = self.agent.observe_env()
                action_t = self.agent.choose_action(state_t)
                test_case = []
                seq = [self.generate_state_semantic_str(state_t, action_t)]
                self.agent.seq_type_order = seq

            # action is none
            if action_t == None:
                # self.agent.clean_action_value(state_t, action_t)
                self.env.restart_app()
                state_t = self.agent.observe_env()
                action_t = self.agent.choose_action(state_t)
                seq = [self.generate_state_semantic_str(state_t, action_t)]
                test_case = []
            # step2: execute action
            self.env.step(action_t)
            test_case.append(action_t)
            # step3: jump to new state
            state_t1 = self.agent.observe_env()
            # no actions in state_t1,terminal state
            if state_t1 == None:
                self.agent.clean_action_value(state_t, action_t)
                self.env.restart_app(self.app_package)
                state_t1 = self.agent.observe_env()
                action_t = self.agent.choose_action(state_t)
                test_case = []
                continue
            action_t1 = self.agent.choose_action(state_t1)
            seq_state.append(state_t1.structure_str)
            seq.append(self.generate_state_semantic_str(state_t, action_t))
            print('seq', seq)
            # step4: update Q-table
            basic_reward = self.agent.get_basic_reward(action_t, state_t, state_t1, seq_state)
            semantic_reward = self.agent.get_semantic_reward(seq)
            print('basic_reward', basic_reward)
            print('semantic_reward', semantic_reward)
            self.agent.updateQ_table(state_t, action_t, state_t1, basic_reward + semantic_reward)

            # step5: recycle
            state_t = state_t1
            action_t = action_t1

        # stop server connection
        self.env.exit()

    def generate_state_semantic_str(self, state, action):
        if not hasattr(action, 'view'):
            return action.get_event_str(state)
        view = action.view
        view_class = view['class'].split('.')[-1]
        view_text = view['text'].replace('\n', '\\n') if 'text' in view and view['text'] else ''
        return f'{state.structure_str}/{state.activity_short_name}/{view_class}-{view_text[:10]}'

    def get_current_app(self):
        # 获取窗口信息
        window_info = os.popen('adb shell dumpsys window w | findstr \/ | findstr name=').read()
        # 从窗口信息中提取包名
        package_name_start = window_info.find('name=') + len('name=')
        package_name_end = window_info.find('/', package_name_start)
        package_name = window_info[package_name_start:package_name_end]
        return package_name

    def check_current_app(self):
        current_app_package = self.get_current_app()
        if self.app_package != current_app_package:
            self.env.restart_app(current_app_package)

if __name__ == "__main__":
    device = device.Device(device_serial='emulator-5554', is_emulator=True, output_dir="F:\Applications\\apks\Tomdroid")
    explor = QExploration(device, "F:\Applications\\apks\Tomdroid")
    explor.start()