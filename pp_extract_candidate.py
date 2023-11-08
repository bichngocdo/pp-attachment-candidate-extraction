import argparse
import sys


class Token:
    def __init__(self):
        self.id = None
        self.word = None
        self.tag = None
        self.head = None
        self.label = None
        self.tf = None

    @classmethod
    def parse(cls, parts):
        token = cls()
        token.id = parts[0]
        token.word = parts[1]
        token.pos = parts[4]
        token.head = int(parts[6])
        token.label = parts[7]
        token.tf = parts[-1]
        return token

    @classmethod
    def parse_sentence(cls, block):
        tokens = list()
        for line in block:
            parts = line.split('\t')
            token = cls.parse(parts)
            tokens.append(token)
        return tokens


class CoNLLFile:
    def __init__(self, f):
        self.file = f
        self.sentence = list()

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            line = self.file.readline()
            if not line:
                if not self.sentence:
                    raise StopIteration
                else:
                    sentences = self.sentence
                    self.sentence = []
                    return sentences
            else:
                line = line.rstrip()
                if not line and self.sentence:
                    sentences = self.sentence
                    self.sentence = []
                    return sentences
                if line:
                    self.sentence.append(line)

    def close(self):
        self.file.close()


WORD_COL = 1
POS_COL = 3
PPOS_COL = 4
HEAD_COL = 6
LABEL_COL = 7
PHEAD_COL = 8
PLABEL_COL = 9
TF_COL = -1

PPS = {'APPR', 'APPRART', 'APPO'}


def find_left(block, i, field):
    j = i - 1
    while j >= 0 and block[j][TF_COL] != field:
        j -= 1
    return j if j >= 0 else None


def find_right(block, i, field):
    j = i + 1
    while j < len(block) and block[j][TF_COL] != field:
        j += 1
    return j if j < len(block) else None


def is_in_sub_clause(block, i):
    j = i - 1
    while j >= 0:
        if block[j][TF_COL] == 'C':
            return True
        if block[j][TF_COL] == 'LK':
            break
        j -= 1
    return False


def find_noun_candidates_MF(block, pp_pos):
    candidates = list()
    k = pp_pos - 1
    while k >= 0:
        if block[k][TF_COL] != 'MF':
            break
        if block[k][PPOS_COL].startswith('N'):
            candidates.append(k)
        k -= 1
    return candidates


def find_noun_candidates_VF(block, pp_pos):
    candidates = list()
    k = pp_pos - 1
    while k >= 0:
        if block[k][TF_COL] != 'VF':
            break
        if block[k][PPOS_COL].startswith('N'):
            candidates.append(k)
        k -= 1
    return candidates


def find_noun_candidates_VF_MF(block, pp_pos):
    candidates = list()
    k = pp_pos + 1
    while k < len(block) and block[k][TF_COL] != 'MF':
        k += 1
    while k < len(block):
        if block[k][TF_COL] != 'MF':
            break
        if block[k][PPOS_COL].startswith('N'):
            candidates.append(k)
        k += 1
    return candidates


def find_noun_candidates_NF(block, pp_pos):
    candidates = list()
    k = pp_pos - 1
    while k >= 0:
        if block[k][TF_COL] != 'NF':
            break
        if block[k][PPOS_COL].startswith('N'):
            candidates.append(k)
        k -= 1
    return candidates


def find_noun_candidates_NF_MF(block, pp_pos):
    candidates = list()
    k = pp_pos - 1
    while k >= 0 and block[k][TF_COL] != 'MF':
        k -= 1
    while k >= 0:
        if block[k][TF_COL] != 'MF':
            break
        if block[k][PPOS_COL].startswith('N'):
            candidates.append(k)
        k -= 1
    return candidates


def find_main_verb(block, pos):
    k = pos
    max_tries = len(block)
    num_tries = 0
    while True:
        num_tries += 1
        if num_tries > max_tries:
            print('Error: Circle at ', block[pos][0], file=sys.stderr)
            return None
        if block[k][PPOS_COL].startswith('V'):
            return k
        if block[k][PHEAD_COL] == '0':
            return None
        k = int(block[k][PHEAD_COL]) - 1


def pp_candidate_extract_rule(block, pp_pos):
    parts = block[pp_pos]
    assert parts[PPOS_COL] in PPS

    noun_candidates = None
    verb_candidate = None
    pp_topo = parts[TF_COL]
    ########################################################################
    if pp_topo == 'MF':
        noun_candidates = find_noun_candidates_MF(block, pp_pos)
    ########################################################################
    elif pp_topo == 'VF':
        lk_pos = find_right(block, pp_pos, 'LK')
        if pp_pos > 0 \
                and block[pp_pos - 1][TF_COL] == 'VF' \
                and block[pp_pos - 1][PPOS_COL].startswith('N'):
            # Preposition is preceded by a noun
            noun_candidates = find_noun_candidates_VF(block, pp_pos)
        else:
            noun_candidates = find_noun_candidates_VF(block, pp_pos) \
                              + find_noun_candidates_VF_MF(block, pp_pos)
    ########################################################################
    elif pp_topo == 'NF':
        if pp_pos > 0 \
                and block[pp_pos - 1][TF_COL] == 'NF' \
                and block[pp_pos - 1][PPOS_COL].startswith('N'):
            # Preposition is preceded by a noun
            noun_candidates = find_noun_candidates_NF(block, pp_pos)
        else:
            noun_candidates = find_noun_candidates_NF(block, pp_pos) \
                              + find_noun_candidates_NF_MF(block, pp_pos)
    else:
        print('Unknown topological field of PP:', pp_topo, file=sys.stderr)
        print('\t'.join(block[pp_pos]), file=sys.stderr)
        return None

    verb_candidate = find_main_verb(block, pp_pos)

    candidates = list()
    if noun_candidates is not None:
        candidates.extend(noun_candidates)
    if verb_candidate is not None:
        candidates.append(verb_candidate)
    return candidates


def get_pp_info(block, pp_pos):
    return block[pp_pos][WORD_COL], block[pp_pos][PPOS_COL], block[pp_pos][TF_COL]


def get_obj_info(block, pp_pos, use_gold=False):
    head_col = HEAD_COL if use_gold else PHEAD_COL

    obj_pos = None
    for k, parts in enumerate(block):
        if int(parts[head_col]) - 1 == pp_pos:
            obj_pos = k
            break
    if obj_pos is None:
        print('No object', file=sys.stderr)
        print('\t'.join(block[pp_pos]), file=sys.stderr)
        return '-1', '_', '_', '_'
    return block[obj_pos][WORD_COL], block[obj_pos][PPOS_COL], block[obj_pos][TF_COL]


def get_can_info(block, pp_pos, candidates):
    candidates.sort()
    correct_head = int(block[pp_pos][HEAD_COL])
    results = list()
    for c in candidates:
        abs_dist = c - pp_pos
        rel_dist = 1 if pp_pos < c else -1
        for o in candidates:
            if pp_pos < o < c:
                rel_dist += 1
            elif c < o < pp_pos:
                rel_dist -= 1
        clazz = 1 if c == correct_head - 1 and block[pp_pos][POS_COL] in PPS else 0
        results.append([block[c][WORD_COL], block[c][PPOS_COL],
                        block[c][TF_COL], str(abs_dist), str(rel_dist), str(clazz)])
    return results


def pp_candidate_extract(fp_in, fp_out, use_gold_obj=False, add_gold_head=False, count_nv=False):
    with open(fp_in, 'r') as f_in, open(fp_out, 'w') as f_out:
        f_in = CoNLLFile(f_in)
        num_gold = 0
        num_retrieved = 0
        num_found = 0
        num_covered = 0
        num_correct_head = 0

        err_tf = 0
        err_no_can = 0
        err_no_obj = 0

        for block in f_in:
            for i in range(len(block)):
                block[i] = block[i].split('\t')

            for pp_pos, parts in enumerate(block):
                # If the current token is a preposition
                gold_head = int(parts[HEAD_COL])
                gold_head_gold_pos = block[gold_head - 1][POS_COL]
                if parts[POS_COL] in PPS:
                    if not count_nv or gold_head_gold_pos[0] in {'N', 'V'}:
                        num_gold += 1
                if parts[PPOS_COL] in PPS:
                    num_retrieved += 1

                    if parts[POS_COL] in PPS:
                        if not count_nv or gold_head_gold_pos[0] in {'N', 'V'}:
                            num_found += 1

                    candidates = pp_candidate_extract_rule(block, pp_pos)
                    if candidates is None:
                        if parts[POS_COL] in PPS:
                            if not count_nv or gold_head_gold_pos[0] in {'N', 'V'}:
                                err_tf += 1
                        continue

                    correct_head_id = int(block[pp_pos][HEAD_COL]) - 1

                    if add_gold_head:
                        if correct_head_id not in candidates:
                            candidates.append(correct_head_id)
                        if not (parts[POS_COL] in PPS and gold_head_gold_pos[0] in {'N', 'V'}):
                            continue
                        if len(candidates) <= 1:
                            continue
                    else:
                        if len(candidates) <= 0:
                            if parts[POS_COL] in PPS:
                                if not count_nv or gold_head_gold_pos[0] in {'N', 'V'}:
                                    err_no_can += 1
                            print('Cannot find candidates', file=sys.stderr)
                            continue

                    sentence_id = parts[0]
                    pp_info = ' '.join(get_pp_info(block, pp_pos))
                    obj_info = ' '.join(get_obj_info(block, pp_pos, use_gold=use_gold_obj))
                    can_info = ' '.join([' '.join(info) for info in get_can_info(block, pp_pos, candidates)])

                    if obj_info.startswith('-1'):
                        if parts[POS_COL] in PPS:
                            if not count_nv or gold_head_gold_pos[0] in {'N', 'V'}:
                                err_no_obj += 1
                        continue

                    if parts[POS_COL] in PPS:
                        if not count_nv or gold_head_gold_pos[0] in {'N', 'V'}:
                            if len(candidates) > 0:
                                num_covered += 1
                            if correct_head_id in candidates:
                                num_correct_head += 1

                    f_out.write(' '.join([sentence_id, pp_info, obj_info, can_info]))
                    f_out.write('\n')

        print('No. gold     : %5d (%5.2f) i.e., no. true prepositions (gold POS tags are prepositions)'
              % (num_gold, 100))
        print('No. retrieved: %5d i.e., no. predicted prepositions (predicted POS tags are prepositions)'
              % num_retrieved)
        print('No. found    : %5d (%5.2f) i.e., no. instances that both true and predicted POS tags are prepositions'
              % (num_found, 100. * num_found / num_gold))
        print('No. covered  : %5d (%5.2f) i.e. no. true prepositions that have some head candidates'
              % (num_covered, 100. * num_covered / num_gold))
        print('No. correct  : %5d (%5.2f) i.e. no. true prepositions of which the true head is among the candidates'
              % (num_correct_head, 100. * num_correct_head / num_gold))
        print()

        print('Non attachment cases')
        print('  wrong TF     :', err_tf)
        print('  no candidates:', err_no_can)
        print('  no object    :', err_no_obj)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('--use_gold_obj', action='store_true',
                        help='Use gold trees to find preposition objects')
    parser.add_argument('--add_gold_head', action='store_true',
                        help='Add the gold head to the list of candidates')
    parser.add_argument('--only_gold', action='store_true',
                        help='Data contain only gold trees, i.e., no data at columns PHEAD and PLABEL')
    parser.add_argument('--only_nv', action='store_true',
                        help='Only extract preposition candidates of which the true heads are nouns or verbs')
    args = parser.parse_args()

    if args.only_gold:
        PHEAD_COL = HEAD_COL
        PLABEL_COL = LABEL_COL

    pp_candidate_extract(args.input, args.output,
                         use_gold_obj=args.use_gold_obj,
                         add_gold_head=args.add_gold_head,
                         count_nv=args.only_nv)
