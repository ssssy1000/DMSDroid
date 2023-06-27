"""
This part of code is the Q learning agent.
All decisions are made in here.
"""
import json
import random

import numpy as np
import pandas as pd

from droidbot import utils

from ..input_event import KeyEvent

Q_TABLE_INITVALUE = 50.00

KEYCODE_HOME = 3
KEYCODE_BACK = 4
KEYCODE_MENU = 82
KEYCODE_DPAD_UP = 19
KEYCODE_VOLUME_UP = 24
KEYCODE_VOLUME_DOWN = 25
SYSTEM_ACTIONS = [KEYCODE_HOME, KEYCODE_BACK, KEYCODE_MENU, KEYCODE_DPAD_UP, KEYCODE_VOLUME_UP, KEYCODE_VOLUME_DOWN]


class Agent(object):
    def __init__(self, device, semantic_seqs, semantic_event_seqs, app_path, learning_rate=0.01, reward_decay=0.9,
                 e_greedy=0.9):
        self.device = device  # 可执行操作列表
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.semantic_seqs = semantic_seqs
        self.semantic_event_seqs = semantic_event_seqs
        self.seq_type_order = []
        self.q_table = dict()
        self.action_frequency_table = dict()
        self.initQ_table(app_path)

    # 随机系统事件生成
    def random_system_events(self):
        index = random.randint(0, len(SYSTEM_ACTIONS) - 1)
        action = KeyEvent(name=SYSTEM_ACTIONS[index])
        return action

    def observe_env(self):
        state = self.device.get_current_state()
        print('获取环境')
        return state

    # 操作选择
    def choose_action(self, state):
        if state is None:
            return None
        state.get_possible_input()
        self.check_state_exist(state)
        # action selection
        probility = np.random.uniform()
        if probility < self.epsilon:
            # select ui action with max value  from Q-table
            selected_actions = []
            cur_val = 0.0
            for event in state.possible_events:
                key = event.get_event_str(state)
                event_value = self.q_table[state.structure_str][key]
                print(key, '--', event_value)
                if event_value > cur_val:
                    selected_actions.clear()
                    selected_actions.append(event)
                    cur_val = event_value
                elif event_value == cur_val:
                    selected_actions.append(event)
                else:
                    continue
            if len(selected_actions) == 0:
                return None
            action = random.choice(selected_actions)
        # 选择系统事件
        elif probility < 0.9:
            action = self.random_system_events()
        else:
            # choose random action
            action = np.random.choice(state.possible_events)
        return action

    def get_basic_reward(self, action, state_t, state_t1, state_seq):
        state_diff = 0
        action_key = action.get_event_str(state_t)
        if action_key not in self.action_frequency_table:
            self.action_frequency_table[action_key] = 1
        else:
            self.action_frequency_table[action_key] += 1
        # system action do not consider
        if action.event_type == 'key':
            return 0
        if state_t.structure_str == state_t1.structure_str:
            state_diff -= 1
        if state_t.structure_str not in state_seq:
            state_diff += 1
        return 1 / self.action_frequency_table[action_key] + state_diff

    # 有哪些语义事件（种类）
    def get_seq_types(self, cur_seqs):
        # 滑动窗口探索语义事件数量，尽可能多类型，滑动窗口时间复杂度更低O(N)
        seq_semantic_order = []
        # 定义初始窗口大小
        window_size = 2
        # 双指针初始化
        left = 0
        right = window_size
        while right <= len(cur_seqs):
            # 当前窗口内的子序列
            window = cur_seqs[left:right]
            # 遍历语义序列，判断当前窗口是否符合语义序列中的任意一个子序列
            for key, value in self.semantic_seqs.items():
                for subseq in value:
                    subseq_index = utils.kmp_search(subseq, window)
                    if subseq_index != -1:
                        seq_semantic_order.append(key)
                        left = left + subseq_index + 1  # 左指针向右移动，减小窗口
                        break
            # 右指针向右移动, 增大窗口
            right += 1
        return seq_semantic_order

    def compute_one_seq_reward(self, seq_type_order):
        count_dict = {}
        if len(seq_type_order) == 0:
            return
        for element in seq_type_order:
            if element in count_dict:
                count_dict[element] += 1
            else:
                count_dict[element] = 1
        # Compute the reward based on the counts
        reward = 0
        for count in count_dict.values():
            reward += 5 / count
        return reward

    # 语义序列顺序是否在我们已设置的易错序列中？很有希望找到Promising-to-
    def get_fallible_seq_nums(self, seq_type_order):
        if len(seq_type_order) == 0:
            return
        fallible_seq = [['DELETE', 'ADD'], ['DELETE', 'DETAIL']]
        nums = 0
        for item in fallible_seq:
            if item in seq_type_order:
                nums += 1
        return nums

    # 获取语义事件奖励
    def get_semantic_reward(self, seq):
        seq_type_order = self.seq_type_order
        self.seq_type_order = self.get_seq_types(seq)
        print('seq_type_order_new', self.seq_type_order)
        if len(self.seq_type_order) == 0 or seq_type_order == self.seq_type_order:
            return 0
        fallible_seq_nums = self.get_fallible_seq_nums(self.seq_type_order) or 0
        # 序列奖励
        seq_reward = self.compute_one_seq_reward(self.seq_type_order) or 0
        # 序列类型奖励, 如果序列类型第一次出现，奖励1
        seq_type_reward = 1 if self.seq_type_order[-1] not in seq_type_order else 0
        # 易错序列发现奖励
        fallible_seq_reward = fallible_seq_nums
        return (seq_reward + seq_type_reward + fallible_seq_reward)

    def get_first_semantic_item(self):
        print('获取所有语义事件序列中的第一个事件行为')
        first_seq_items = set()
        for values in self.semantic_event_seqs.values():
            for value in values:
                first_seq_items.add(value[0])
        return first_seq_items

    def initQ_table(self, app_path):
        print('Q-table init')
        first_semantic_items = self.get_first_semantic_item()
        # 读取JSON文件内容到Python对象
        with open(f'{app_path}/utg.js', 'r') as f:
            utg_content = f.read()
            utg_content = utg_content[utg_content.index("{"):]
            utg_data = json.loads(utg_content)
        nodes = utg_data['nodes']
        edges = utg_data['edges']
        node_dict = dict()
        for node in nodes:
            self.q_table[node['structure_str']] = dict()  # 将结构字符串作为Q表键值，其中存储每个action的奖赏
            node_dict[node['state_str']] = node['structure_str']
        for edge in edges:
            for event in edge['events']:
                self.q_table[node_dict[edge['from']]][event['event_str']] = Q_TABLE_INITVALUE
                if event['event_str'] in first_semantic_items:
                    self.q_table[node_dict[edge['from']]][event['event_str']] += 10  # 如果是语义事件序列的第一个事件行为，额外+10
                else:
                    self.q_table[node_dict[edge['from']]][event['event_str']] += 5
        print(self.q_table)

    # Q_table update 更新Q表
    def updateQ_table(self, state_t, action_t, state_t1, reward):
        # get max target value in state_t1
        target = max(self.q_table[state_t1.structure_str].values())
        # get value of action_t in state_t
        source_key = action_t.get_event_str(state_t)
        # system action 初始值
        if source_key not in self.q_table.keys():
            self.q_table[state_t.structure_str][source_key] = Q_TABLE_INITVALUE

        # update
        self.q_table[state_t.structure_str][source_key] = self.q_table[state_t.structure_str][source_key] + self.lr * (
                reward + self.gamma * target - self.q_table[state_t.structure_str][source_key]
        )

    def check_state_exist(self, state):
        if state.structure_str not in self.q_table.keys():
            self.q_table[state.structure_str] = dict()
        for event in state.possible_events:
            key = event.get_event_str(state)
            if key not in self.q_table[state.structure_str].keys():
                self.q_table[state.structure_str][key] = Q_TABLE_INITVALUE

    # clean one action value to 0 行为奖励值还原为0
    def clean_action_value(self, state_t, action_t):
        key = action_t.get_event_str(state_t)
        self.q_table[state_t.structure_str][key] = 0.0


if __name__ == "__main__":
    print('Q-table init')
    first_seq_items = set()
    app_path = 'F:\Applications\\apks\Tomdroid'
    semantic_sequences = utils.get_semantic_sequences(app_path + '\semantic_sequence')
    for values in semantic_sequences.values():
        for value in values:
            first_seq_items.add(value[0])
    # 读取JSON文件内容到Python对象
    with open(f'{app_path}/utg.js', 'r') as f:
        utg_content = f.read()
        utg_content = utg_content[utg_content.index("{"):]
        utg_data = json.loads(utg_content)
    nodes = utg_data['nodes']
    edges = utg_data['edges']
    node_dict = dict()
    q_table = dict()
    for node in nodes:
        q_table[node['structure_str']] = dict()  # 将结构字符串作为Q表键值，其中存储每个action的奖赏
        node_dict[node['state_str']] = node['structure_str']
    for edge in edges:
        for event in edge['events']:
            q_table[node_dict[edge['from']]][event['event_str']] = Q_TABLE_INITVALUE+10  # 语义相关的事件初始值额外+10
            # if event['event_str'] in first_seq_items:
            #     q_table[node_dict[edge['from']]][event['event_str']] += 10  # 如果是语义事件序列的第一个事件行为，额外+50

    max_value = max(q_table['0f3a62b84039dcd999559a404d507528'].values())
    max_keys = [k for k, v in q_table['0f3a62b84039dcd999559a404d507528'].items() if v == max_value]
    max_key = random.choice(max_keys)
    print(max_key)
