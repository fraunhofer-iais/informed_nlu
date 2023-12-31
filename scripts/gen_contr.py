import json
import tqdm
import random
import pandas as pd
from nltk.corpus import wordnet as wn
from nltk.tokenize import word_tokenize
from utils.create_datalists import read_data
from rule_utils.utils import flatten, read_deps

def create_num_cont(data_labeled):
    f = open("numerals.txt", 'r')
    num_lines = f.readlines()
    numerals = [num.split('\n')[0] for num in num_lines]
    premises = []
    hypotheses = []
    labels = []
    for sentence_pair in tqdm.tqdm(data_labeled):
        premise = sentence_pair[0]
        premise = word_tokenize(premise)
        deps = sentence_pair[3]
        feats = sentence_pair[4]
        premise_new = []
        hypothesis = []
        contradict=False
        for n, (token, dep, feat) in enumerate(zip(premise, deps, feats)):
            if 'nummod' in deps:
                contradict=True                 
                if dep == 'nummod' and token.lower() != 'one':
                    if token.lower() in numerals:
                        numerals.remove(token.lower())
                        if n == 0:
                            numeral = random.choice(numerals)
                            numeral = numeral[0].upper() + numeral[1:]
                            premise_new.append(token)
                            hypothesis.append(numeral)
                        else:
                            numeral = random.choice(numerals)
                            premise_new.append(" " + token)
                            hypothesis.append(" " + numeral)
                else:
                    if n == 0 or dep == 'punct':
                        premise_new.append(token)
                        hypothesis.append(token)
                    else:
                        premise_new.append(" " + token)
                        hypothesis.append(" " + token)

        if len(premise_new) > 0 and len(hypothesis) > 0:
            premises.append("".join(premise_new))
            hypotheses.append("".join(hypothesis))
        
    
    for i in range(len(premises)):
        labels.append('contradiction')

    return labels, premises, hypotheses

def create_neg_cont(data_labeled):
    premises = []
    hypotheses = []
    labels = []
    for sentence_pair in tqdm.tqdm(data_labeled):
        premise = sentence_pair[0]
        premise = word_tokenize(premise)
        deps = sentence_pair[3]         
        feats = sentence_pair[4]
        premise_new = []
        hypothesis = []
        contradict = False
        for n, (token, dep, feat) in enumerate(zip(premise, deps, feats)): 
            if 'root' in deps:                           
                if dep == 'root' and feat != None:
                    if "Number=Sing" in feat and "Tense=Pres" in feat:
                        neg = "does not " + token
                    elif "Number=Plur" in feat and "Tense=Pres" in feat:
                        neg = "do not " + token
                    elif "Tense=Pres|VerbForm=Part" in feat:
                        neg = "not " + token
                    if n == 0:
                        premise_new.append(token)
                        hypothesis.append(neg[0] + neg[1:])
                        contradict=True 
                    else:
                        premise_new.append(" " + token)
                        hypothesis.append(" " + neg)
                        contradict=True 
                else:
                    if n != 0 and dep != "punct":
                        premise_new.append(( " " + token))
                        hypothesis.append(( " " + token))
                        contradict=True
                    else:
                        premise_new.append(token)
                        hypothesis.append(token)
                        contradict=True 
        
        if len(premise_new) > 0 and len(hypothesis) > 0:
            premises.append("".join(premise_new))
            hypotheses.append("".join(hypothesis))                     
    
    for i in range(len(premises)):
        labels.append('contradiction')
        
    return labels, premises, hypotheses
                                    

def create_ant_cont(data_labeled):

    premises = []
    hypotheses = []
    labels = []
    antonym_pairs = []
    for sentence_pair in tqdm.tqdm(data_labeled):
        premise = sentence_pair[0]
        premise = word_tokenize(premise)
        pos = sentence_pair[2]
        deps = sentence_pair[3]
        feats = sentence_pair[4]
        premise_new = []
        hypothesis = []
        antonym_sent = []
        antonym=False  
        if 'obj' in deps:  
            for n, (token, dep, p, feat) in enumerate(zip(premise, deps, pos, feats)):          
                if dep == 'obj' and feat != None and "Number=Sing" in feat and p == "NOUN":
                    ant_obj = []
                    antonyms=[]  
                    for syn in wn.synsets(token, pos=wn.NOUN):
                        for l in syn.lemmas():
                            if l.antonyms():
                                ant_obj.append(l.antonyms()) # get antonyms for the subject
                    ant_obj = list(flatten(ant_obj))
                    ant_synsets = [ant.synset() for ant in ant_obj]
                    antonyms=[]
                    for ant_s in ant_synsets:
                        antonyms.append(ant_s.lemma_names())
                    antonyms = [ant for subl in antonyms for ant in subl if "_" not in ant]
                            
                    if len(antonyms) > 0:
                        if n != 0: 
                            antonym=True
                            premise_new.append((" " + token))
                            hypothesis.append((" " + antonyms[0]))
                            antonym_sent.append((token, antonyms[0]))
                        else:
                            premise_new.append((token))
                            hypothesis.append((antonyms[0]))
                            antonym_sent.append((token, antonyms[0]))
                    elif len(antonyms) == 0:
                        if n != 0:
                            premise_new.append((" " + token))
                            hypothesis.append((" " + token))
                            antonym_sent.append(None)
                        else:
                            premise_new.append((token))
                            hypothesis.append(token)
                            antonym_sent.append(None)
                #save other words from a sentence            
                elif dep != 'obj':
                    if n != 0 or dep != "punct":
                        premise_new.append((" " + token))
                        hypothesis.append((" " + token))
                        antonym_sent.append(None)
                    else:
                        premise_new.append((token))
                        hypothesis.append(token)
                        antonym_sent.append(None)
        
        if len(premise_new) > 0 and len(hypothesis) > 0 and antonym==True and premise_new != hypothesis:
            premises.append("".join(premise_new))
            hypotheses.append("".join(hypothesis))
            antonym_pairs.append(antonym_sent)
                
    for i in range(len(premises)):
        labels.append('contradiction')
                
    return labels, premises, hypotheses, antonym_pairs

def create_adj_ant(data_labeled):
    premises = []
    hypotheses = []
    labels = []
    antonym_pairs = []
    for sentence_pair in tqdm.tqdm(data_labeled):
        premise = sentence_pair[0]
        premise = word_tokenize(premise)
        pos = sentence_pair[2]
        deps = sentence_pair[3]
        feats = sentence_pair[4]
        sent_syn=[]
        for syn in sentence_pair[5]:
            if 'wn:' in syn:
                sent_syn.append(syn)
            else:
                sent_syn.append(None)

        premise_new = []
        hypothesis = []
        antonym_sent = []
        contradict = False
        antonym=False  
        if "ADJ" in pos: 
            for n, (token, dep, p, feat, s) in enumerate(zip(premise, deps, pos, feats, sent_syn)):          
                if p == "ADJ" and dep != "compound": 
                    ant_adj = []
                    antonyms = [] 
                    if s != None: 
                        syn = wn.synset_from_pos_and_offset(s[len(s)-1], int(s[3:len(s)-1]))     
                        for l in syn.lemmas():
                            if l.antonyms():
                                ant_adj.append(l.antonyms())# get antonym for the subject

                    ant_adj = list(flatten(ant_adj))
                    ant_synsets = [ant.synset() for ant in ant_adj]
                    
                    for ant_s in ant_synsets:
                        antonyms.append(ant_s.lemma_names())
                    antonyms = [ant for subl in antonyms for ant in subl if "_" not in ant]
                        
                    if len(antonyms) > 0:
                        if n != 0: 
                            antonym=True
                            premise_new.append((" " + token))
                            hypothesis.append((" " + antonyms[0]))
                            antonym_sent.append((token, antonyms[0]))
                        else:
                            premise_new.append((token))
                            hypothesis.append((antonyms[0]))
                            antonym_sent.append((token, antonyms[0]))
                            
                    elif len(antonyms) == 0:
                        if n != 0: 
                            antonym = True
                            premise_new.append((" " + token))
                            hypothesis.append((" " + token))
                            antonym_sent.append(None)
                        else:
                            premise_new.append((token))
                            hypothesis.append((token))
                            antonym_sent.append(None)            
                elif p != "ADJ":
                    if n != 0 or dep != "punct":
                        premise_new.append((" " + token))
                        hypothesis.append((" " + token))
                        antonym_sent.append(None)
                    else:
                        premise_new.append((token))
                        hypothesis.append(token)
                        antonym_sent.append(None)
        
        if len(premise_new) > 0 and len(hypothesis) > 0 and antonym==True and premise_new != hypothesis:
            premises.append("".join(premise_new))
            hypotheses.append("".join(hypothesis))
            antonym_pairs.append(antonym_sent)
    
    for i in range(len(premises)):
        labels.append('contradiction')
                
    return labels, premises, hypotheses, antonym_pairs

def create_proto(data):
    ant_labels, prem, hypot, ant_list = create_ant_cont(data[:200])
    neg_labels, n_prem, n_hypot = create_neg_cont(data[:200])
    num_labels, num_prem, num_hypot = create_num_cont(data[:200])
    adj_labels, adj_prem, adj_hypot, ant_list = create_adj_ant(data[:200])
    labels = ant_labels + neg_labels + num_labels + adj_labels
    premise = prem + n_prem + num_prem + adj_prem
    hypothese = hypot + n_hypot + num_hypot + adj_hypot
    
    return labels, premise, hypothese, ant_list
        

def write_data_file(path, data_contr, data_labeled):
    labels_gold = []
    premise_gold = []
    hypothese_gold = []
    for s in data_labeled:
        if s[0] != 'contradiction':
            labels_gold.append(s[0])
            premise_gold.append(s[1])
            hypothese_gold.append(s[2])
            
    proto_labels, proto_premise, proto_hypothese, ant_list = create_proto(data_contr)  
    labels = proto_labels+labels_gold[:len(proto_labels)] # comment out to save not only contrad
    premise = proto_premise+premise_gold[:len(proto_premise)] # add the same number of non contradictions 
    hypothese = proto_hypothese+hypothese_gold[:len(proto_hypothese)] 
    
    dict_contr = {'gold_labels': labels, 'sentence1': premise, 'sentence2': hypothese}
    df = pd.DataFrame.from_dict(dict_contr)
    df.to_json(path_or_buf=path, orient="records", lines=True)


if __name__ == "__main__":
    #add paths to snli data
    all_train = ""
    all_dep = ""
    all_test = ""

    train_data = read_data(all_train)
    val_data = read_data(all_dep)
    test_data = read_data(all_test)
   
    train_file = "train_deps_syn.json"
    val_file = "val_deps_syn.json"
    test_file = "test_deps_syn.json"
    
    train_proto = read_deps(train_file)
    val_proto = read_deps(val_file)
    test_proto = read_deps(test_file)
    
    train = write_data_file('train_simple_prototypes.json', data_contr = train_proto, data_labeled = train_data)
    val = write_data_file('val_simple_prototypes.json', data_contr = val_proto, data_labeled = val_data)
    test = write_data_file('test_simple_prototypes.json', data_contr = test_proto, data_labeled = test_data)
