import os


class Configuration(object):
    # semantic setting
    SEMANTIC_TYPE = ['add', 'delete', 'edit', 'search', 'detail']
    # 构造规则列表字典
    RULE_DICT = {
        'ADD': [{'state': 'listView', 'action': [['touch', 'long-touch'], 'add_btn']},
                {'state': 'inputView', 'action': [['set_text', 'touch'], 'inputView']},
                {'state': 'inputView', 'action': [['touch', 'long-touch'], 'submit_btn']}
                ],
        'ADD2': [{'state': 'textView', 'action': [['touch', 'long-touch'], 'labelled_btn']}],
        'DELETE': [{'state': 'textView', 'action': [['touch', 'long-touch'], 'delete_btn'], 'get_content': True},
                   {'state': 'textView', 'action': [['touch', 'long-touch'], 'submit_btn']}
                   ],
        'SEARCH': [{'state': 'listView', 'action': [['touch', 'long-touch'], 'search_btn']},
                   {'state': 'inputView', 'action': ['set_text', 'inputView'], 'get_content': True}],
        'EDIT': [{'state': 'textView', 'action': [['touch', 'long-touch'], 'edit_btn']},
                 {'state': 'inputView', 'action': ['set_text', 'inputView'], 'get_content': True},
                 {'state': 'inputView', 'action': [['touch', 'long-touch'], 'submit_btn']}
                 ],
        'DETAIL': [{'state': 'listView', 'action': [['touch', 'long-touch'], 'listItem_btn'], 'get_content': True},
                   {'state': 'textView', 'action': None}]
    }
    # 定义列表控件标签名
    LIST_TAGS = ['ListView', 'GridView', 'Spinner', 'ExpandableListView', 'RecyclerView']
    # 定义输入控件标签名
    INPUT_TAGS = ['EditText', 'CheckBox', 'CheckedTextView', 'ToggleButton', 'SeekBar', 'RadioButton']
    # 不同类型的按钮
    BTN_TYPES = {
        'add_btn': ['add', 'new', 'create', '+'],
        'labelled_btn': ['download', 'subscribe', 'collect', 'like'],
        'edit_btn': ['edit', 'change', 'rename', 'update', 'modify'],
        'delete_btn': ['remove', 'delete', 'clear'],
        'search_btn': ['search', 'find', 'filter', 'look up'],
        'submit_btn': ['save', 'ok', 'submit', 'yes', 'confirm', 'done'],
    }


class SemanticsEvents(object):
    def __init__(self, device):
        # type语义类型，list操作序列，包括state和action，
        # state为0时cur_eventlist清空重新记录，state大于0记录当前页面在RULE_xxx中的进度
        self.cur_eventlist = {'type': '', 'list': [], 'state': 0}
        self.device = device
        self.prev_structure_str = ''
        self.prev_eventlist = dict()

    def save2dir(self, event_list, semantic_type):
        if self.device.output_dir is None:
            return
        else:
            output_dir = os.path.join(self.device.output_dir, "semantic_sequence")
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            semantic_event_file_path = "%s/%s.txt" % (output_dir, semantic_type)
            with open(semantic_event_file_path, 'a') as f:
                f.write(str(event_list['list'])+'\n')

        except Exception as e:
            self.device.logger.warning("Saving event to dir failed.")
            self.device.logger.warning(e)

    def is_eventlist_over(self, state_index, semantic_type):
        if state_index == len(Configuration.RULE_DICT[semantic_type]):
            print('one eventlist over: ', self.cur_eventlist['list'])
            self.prev_eventlist = self.cur_eventlist
            self.cur_eventlist = {'type': '', 'list': [], 'state': 0}
        else:
            return

    # record the number of widget type
    def record_widget_type(self, v, wtl):
        try:
            if v['class']:
                # 判断当前元素类名
                if v['class'] == 'android.widget.TextView':
                    wtl['textView'] += 1
                elif v['class'] == 'android.widget.ImageView':
                    wtl['imageView'] += 1
                elif any(word.lower() in v['class'].lower() for word in Configuration.LIST_TAGS):
                    wtl['listView'] += 1
                elif any(word.lower() in v['class'].lower() for word in Configuration.INPUT_TAGS):
                    wtl['inputView'] += 1
                else:
                    for key, word_list in Configuration.BTN_TYPES.items():
                        if any(word.lower() in v['signature'].lower() for word in word_list):
                            wtl['buttonCnt'][key] += 1
            else:
                return
        except Exception as e:
            self.device.logger.warning("record_widget_type failed.")
            self.device.logger.warning(e)
        return wtl

    def get_semantic_widgets(self, appState):
        widget_type_list = {
            'textView': 0,
            'imageView': 0,
            'listView': 0,
            'inputView': 0,
            'buttonCnt': {
                'add_btn': 0,
                'labelled_btn': 0,
                'edit_btn': 0,
                'delete_btn': 0,
                'search_btn': 0,
                'submit_btn': 0
            },
            'md5Value': appState.state_str
        }
        for view in appState.views:
            widget_type_list = self.record_widget_type(view, widget_type_list)
        return widget_type_list

    # 判断是否为列表中的子元素
    def is_list_item(self, state, event):
        parent_id = event['parent']
        if parent_id <= 6:
            return False
        parent_widget = state.views[parent_id]
        if any(word.lower() in parent_widget['class'].lower() for word in Configuration.LIST_TAGS):
            return True
        else:
            self.is_list_item(state, parent_widget)

    def get_semantic_event(self, state, event):
        if hasattr(event, 'view'):
            if any(word.lower() in event.view['class'].lower() for word in Configuration.INPUT_TAGS):
                return 'inputView'
            elif 'button' not in event.view['signature'].lower() and self.is_list_item(state, event.view):
                return 'listItem'
            else:
                for key, word_list in Configuration.BTN_TYPES.items():
                    if any(word.lower() in event.view['signature'].lower() for word in word_list):
                        return key
                return 'normal'
        else:
            return None

    def first_semantic_page(self, widget_type_list, appState, appAction):
        # 添加
        if appAction.event_type == 'touch' and appAction.element_type == 'add_btn':
            print(widget_type_list['md5Value'] + ' may be the first state of add state')
            cur_eventlist = {"type": "ADD", "list": [{'state': widget_type_list['md5Value'], 'action': appAction.view['view_str'], 'event_str': appAction.get_event_str(appState)}], "state": 1}
        # 修改
        elif widget_type_list['textView'] > 2 and appAction.event_type == 'touch' and appAction.element_type == 'edit_btn':
            print(widget_type_list['md5Value'] + ' may be the first state of edit state')
            cur_eventlist = {"type": "EDIT", "list": [{'state': widget_type_list['md5Value'], 'action': appAction.view['view_str'], 'event_str': appAction.get_event_str(appState)}], "state": 1}

        # 删除
        elif appAction.event_type == 'touch' and appAction.element_type == 'delete_btn':
            print(widget_type_list['md5Value'] + ' may be the first state of delete state')
            cur_eventlist = {"type": "DELETE", "list": [{'state': widget_type_list['md5Value'], 'action': appAction.view['view_str'], 'event_str': appAction.get_event_str(appState)}], "state": 1}

        # 搜索
        elif widget_type_list['listView'] > 0 and appAction.element_type == 'search_btn':
            print(widget_type_list['md5Value'] + ' may be the first state of search state')
            cur_eventlist = {"type": "SEARCH", "list": [{'state': widget_type_list['md5Value'], 'action': appAction.view['view_str'], 'event_str': appAction.get_event_str(appState)}], "state": 1}

        # 进入详情
        elif widget_type_list['listView'] > 0 and appAction.element_type == 'listItem':
            print(widget_type_list['md5Value'] + ' may be the first state of detail state')
            cur_eventlist = {"type": "DETAIL", "list": [{'state': widget_type_list['md5Value'], 'action': appAction.view['view_str'], 'event_str': appAction.get_event_str(appState)}], "state": 1}
        else:
            return None
        return cur_eventlist

    # 定义语义事件序列抽取
    def get_semantic_state(self, appState, appAction):
        print('self.cur_eventlist', self.cur_eventlist)
        state = self.cur_eventlist['state']
        state_widget_type_list = self.get_semantic_widgets(appState)
        self.check_semantic_state(appState)
        appAction.element_type = self.get_semantic_event(appState, appAction)
        # 判断state
        # 开始语义探索
        if self.cur_eventlist['state'] > 0:
            semantic_type = self.cur_eventlist['type']
            target_el = Configuration.RULE_DICT[semantic_type][state]
            # 回到了初始状态(考虑文字)
            if len(self.cur_eventlist['list']) > 1 and appState.state_str == self.cur_eventlist['list'][0]['state']:
                print('loop, record again')
                self.cur_eventlist = {'type': '', 'list': [], 'state': 0}
                # 序列过长
            elif len(self.cur_eventlist['list']) > 20:
                self.cur_eventlist = {'type': '', 'list': [], 'state': 0}
            # 确认为目标状态
            elif state_widget_type_list[target_el['state']] > 0 and target_el['action'] != None and appAction.event_type in target_el['action'][0] \
                    and (appAction.element_type == target_el['action'][1] or semantic_type in appAction.view['signature'].upper()):
                if hasattr(target_el, 'get_content') and target_el['get_content'] == True and (not hasattr(self.cur_eventlist, 'content')):
                    self.cur_eventlist['content'] = appAction.view['text']
                self.cur_eventlist['state'] += 1
                self.cur_eventlist['list'].append({'state': appState.state_str, 'action': appAction.view['view_str'], 'event_str': appAction.get_event_str(appState)})
                # 序列完成，写入待检验事件序列
                self.is_eventlist_over(self.cur_eventlist['state'], semantic_type)

            # 重新获取语义序列
            elif self.first_semantic_page(state_widget_type_list, appState, appAction):
                self.cur_eventlist = self.first_semantic_page(state_widget_type_list, appState, appAction)

            # 确认为目标状态，detail容易与其它行为重叠，因此放在最后
            elif state_widget_type_list[target_el['state']] > 0 and appState.structure_str != self.prev_structure_str and target_el['action'] == None and appAction.element_type == 'normal':
                print('over, action: None')
                self.cur_eventlist['state'] += 1
                self.cur_eventlist['list'].append({'state': appState.state_str, 'action': appAction.view['view_str'], 'event_str': appAction.get_event_str(appState)})
                # 如果序列完成，语义序列完成并写入对应txt文件
                self.is_eventlist_over(self.cur_eventlist['state'], semantic_type)

            # 不匹配任何一条规则
            else:
                print('不匹配任何一条规则，暂存')
                new_eventlist = self.first_semantic_page(state_widget_type_list, appState, appAction)
                if new_eventlist is not None:
                    self.cur_eventlist = self.first_semantic_page(state_widget_type_list, appState, appAction)
                else:
                    self.cur_eventlist['list'].append(
                        {'state': appState.state_str, 'action': appAction.view['view_str'],
                         'event_str': appAction.get_event_str(appState)})
        # state为0时，当前语义探索列表为空
        else:
            new_eventlist = self.first_semantic_page(state_widget_type_list, appState, appAction)
            if new_eventlist is not None:
                self.cur_eventlist = self.first_semantic_page(state_widget_type_list, appState, appAction)
        self.prev_structure_str = appState.structure_str
        return appState.state_str

    # 语义事件序列校验
    def check_semantic_state(self, appState_t1):
        if len(self.prev_eventlist) == 0:
            return
        semantic_type = self.prev_eventlist['type']
        content_check = ''
        if hasattr(self.cur_eventlist,'content'):
            content_check = self.cur_eventlist['content']

        if semantic_type=='':
            return
        if semantic_type == 'SEARCH' or semantic_type == 'DELETE':
            self.save2dir(self.prev_eventlist, semantic_type)
            self.prev_eventlist = {}
        elif semantic_type == 'ADD' or semantic_type == 'EDIT':
            if self.content_in_all(content_check, appState_t1):
                # 满足规则，写入txt文件中
                self.save2dir(self.prev_eventlist, semantic_type)
                self.prev_eventlist = {}
        elif semantic_type == 'DETAIL':
            if self.content_in_all(content_check, appState_t1):
                self.save2dir(self.prev_eventlist, semantic_type)
                self.prev_eventlist = {}
        else:
            # 不写入
            self.prev_eventlist = {}

    def content_in_list(self, content, appState_t1):
        for view in appState_t1.views:
            if any(word.lower() in view['class'].lower() for word in Configuration.LIST_TAGS):
                if content in view['signature']:
                    return True
        return True

    def content_in_all(self, content, appState_t1):
        for view in appState_t1.views:
            if content in view['signature']:
                return True
        return False






