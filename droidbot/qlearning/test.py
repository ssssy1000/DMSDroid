from droidbot import utils

app_path = 'F:\Applications\\apks\Tomdroid'
semantic_sequences = utils.get_semantic_sequences(app_path + '\semantic_sequence')
seq_order = []
cur_seqs = ['0f3a62b84039dcd999559a404d507528/Tomdroid/ListView-', '0f3a62b84039dcd999559a404d507528/Tomdroid/RelativeLayout-', '0c8dde96ce606fe94dc3bf5e3ae68fad/Tomdroid/TextView-View', '731dd8d916d3b3340a071df25252df01/ViewNote/TextView-Tomdroid - View Note', '0f3a62b84039dcd999559a404d507528/Tomdroid/RelativeLayout-', '0c8dde96ce606fe94dc3bf5e3ae68fad/Tomdroid/TextView-View', '731dd8d916d3b3340a071df25252df01/ViewNote/TextView-Tomdroid - View Note', '0f3a62b84039dcd999559a404d507528/Tomdroid/RelativeLayout-', '0c8dde96ce606fe94dc3bf5e3ae68fad/Tomdroid/TextView-View', '731dd8d916d3b3340a071df25252df01/ViewNote/TextView-Tomdroid - View Note', '0f3a62b84039dcd999559a404d507528/Tomdroid/RelativeLayout-', '0c8dde96ce606fe94dc3bf5e3ae68fad/Tomdroid/TextView-View', '731dd8d916d3b3340a071df25252df01/ViewNote/TextView-Tomdroid - View Note', '0f3a62b84039dcd999559a404d507528/Tomdroid/RelativeLayout-', '0c8dde96ce606fe94dc3bf5e3ae68fad/Tomdroid/TextView-View', '731dd8d916d3b3340a071df25252df01/ViewNote/TextView-Tomdroid - View Note']
def check_sequence(cur_seqs, sequence):
    # 找到sequence在cur_seqs中出现的第一个位置
    if sequence[0] not in cur_seqs:
        return False
    start = cur_seqs.index(sequence[0])
    for i in range(1, len(sequence)):
        # 如果后面的元素不在当前位置的后面，则返回False
        if sequence[i] not in cur_seqs[start + 1:]:
            return False
        # 否则，更新start的位置为下一个元素在cur_seqs中出现的位置
        start += cur_seqs[start + 1:].index(sequence[i]) + 1
    return True

def check_semantic_sequences(cur_seqs, semantic_sequences):
    left, right = 0, 2
    for key, sequences in semantic_sequences.items():
        for sequence in sequences:
            if check_sequence(cur_seqs, sequence):
                seq_order.append(key)
    return None


def get_seq_semantic_order(cur_seqs, semantic_sequences):
    # 初始化双指针和seq_semantic_order列表
    left, right = 0, 0
    seq_semantic_order = []

    # 遍历cur_seqs，当right指针到达最后一个元素时结束循环
    while right < len(cur_seqs):
        # 当cur_seqs[left:right+1]是semantic_sequences中任意一个序列时，记录对应的键值到seq_semantic_order中
        for key, value in semantic_sequences.items():
            if cur_seqs[left:right + 1] in value:
                seq_semantic_order.append(key)
                break
        else:
            # 当cur_seqs[left:right+1]不是semantic_sequences中任意一个序列时，窗口右移
            right += 1
            continue

        # 当找到一个匹配的序列时，将左右指针同时右移
        left = right + 1
        right = left

    return seq_semantic_order

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

def sliding_window(cur_seqs, semantic_sequences):
    # 初始化双指针
    # 定义双指针的初始位置和窗口大小
    left = 0
    right = 0
    window_size = 1

    seq_semantic_order = []

    while right < len(cur_seqs):

        # 如果当前窗口大小小于语义序列中最长的序列长度，则右指针向右移动
        if window_size < max(len(seq) for subseqs in semantic_sequences.values() for seq in subseqs):
            right += 1
            window_size += 1
        else:
            # 如果当前窗口大小等于语义序列中最长的序列长度，则进行匹配
            matched = False
            for sem_seq in semantic_sequences.keys():
                for subseq in semantic_sequences[sem_seq]:
                    if cur_seqs[left:right] == subseq:
                        seq_semantic_order.append(sem_seq)
                        left += len(subseq)
                        right = left
                        window_size = 1
                        matched = True
                        break
                if matched:
                    break

            if not matched:
                left += 1
                right = left
                window_size = 1
    return seq_semantic_order

# check_semantic_sequences(cur_seqs, semantic_sequences)
# cur_seqs = ['a', 'b', 'd', 'e', 'a', 'b', 'c', 'a', 'b', 'c', 'a', 'b', 'c']
# semantic_sequences = {'DETAIL': [['a', 'b', 'c'], ['a', 'd', 'b']], 'DELETE': [['b', 'd'], ['d', 'e']]}
# seq_order = sliding_window(cur_seqs, semantic_sequences)
# print(seq_order)
# cur_seqs = ['a', 'b', 'd', 'e', 'a', 'b', 'c', 'a', 'b', 'c', 'a', 'b', 'c']
# semantic_sequences = {'DETAIL': [['a', 'b', 'c'], ['a', 'd', 'b']], 'DELETE': [['b', 'd'], ['d', 'e']]}
seq_semantic_order = []

# 定义窗口大小
window_size = 3

# 双指针初始化
left = 0
right = window_size

while right <= len(cur_seqs):
    # 当前窗口内的子序列
    window = cur_seqs[left:right]
    # 遍历语义序列，判断当前窗口是否符合语义序列中的任意一个子序列
    for key, value in semantic_sequences.items():
        for subseq in value:
            subseq_index = kmp_search(subseq, window)
            if subseq_index != -1:
                seq_semantic_order.append(key)
                left = left+subseq_index+1  # 左指针向右移动，减小窗口
                break
    # 右指针向右移动, 增大窗口
    right += 1

print(seq_semantic_order)