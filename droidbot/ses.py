import json
import os
import re


class SES(object):
    def __init__(self, app_path):
        self.app_path = app_path
        self.app_ses_path = os.path.join(app_path, 'semantic_sequence')
        self.utg_nodes = self.get_utg()
        self.ses_out_file_path = os.path.join(app_path, "ses.js")
        self.app_sess = self.get_state_event()



    def get_utg(self):
        with open(f'{self.app_path}/utg.js', 'r') as f:
            utg_content = f.read()
            utg_content = utg_content[utg_content.index("{"):]
            utg_data = json.loads(utg_content)
        nodes = utg_data['nodes']
        return nodes

    def find_state_img(self, id):
        for item in self.utg_nodes:
            if item['id']==id:
                return item["image"]
        return ''

    def state_from_line(self, str, key):
        seq_item = []
        regex_s = r"'state': '(.+?)'"
        regex_a = r"'action': '(.+?)'"
        states = re.findall(regex_s, str)
        actions = re.findall(regex_a,str)
        for i in range(len(states)-1):
            from_img = self.find_state_img(states[i])
            to_img = self.find_state_img(states[i])
            seq_item.append(
                {
                    'from': states[i],
                    'from_img': from_img,
                    'action': actions[i],
                    'action_img': 'views\\view_'+actions[i]+'.png',
                    'to': states[i+1],
                    'to_img': to_img,
                }
            )
        if key != 'DETAIL':
            seq_item.append({'action': actions[-1], 'action_img': 'views\\view_'+actions[-1]+'.png'})
        return seq_item

    def get_unique_ses_list(self, source_list):
        seq_list_unique = []
        for item in source_list:
            if item not in seq_list_unique:
                seq_list_unique.append(item)
        return seq_list_unique

    def get_state_event(self):
        ses = dict()
        for dir in os.listdir(self.app_ses_path):
            seq_name = dir.split('.')[0]
            with open('%s\\%s' % (self.app_ses_path, dir), 'r') as f:
                seq_list = [self.state_from_line(line.strip(), seq_name) for line in f.readlines()]
                seq_list_unique = self.get_unique_ses_list(seq_list)
            ses[seq_name] = seq_list_unique
        self.write_in_js(ses)
        return ses

    def write_in_js(self, ses):
        ses_file = open(self.ses_out_file_path, "w")
        ses_json = json.dumps(ses, indent=2)
        ses_file.write("var ses = \n")
        ses_file.write(ses_json)
        ses_file.write("\n \nfunction showSes() { \n console.log(ses); \n}")
        ses_file.close()

if __name__ == "__main__":
    ses = SES('F:\Applications\\apks\\budgetwatch')