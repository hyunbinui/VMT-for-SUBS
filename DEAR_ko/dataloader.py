import json
import numpy as np
import os 

import torch 
from torch.utils.data import Dataset, DataLoader
import random
from utils import padding_idx

########################################################################
#결측치 처리
def load_fake_features():
    feats = torch.rand(1, 32, 1024)[0]
    img_mask = torch.rand(1, 32).bool()
    classe = np.array([72, 33,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0])
    final_classes = torch.Tensor(classe).long()
    return feats, img_mask, final_classes

########################################################################


def load_video_features(fpath, max_length, classes):
    feats = np.load(fpath, encoding='latin1')[0]
    if feats.shape[0] <= max_length:
        dis = max_length - feats.shape[0]
        feats = np.lib.pad(feats, ((0, dis), (0, 0)), 'constant', constant_values=0)
        final_classes = np.array(classes.copy())

        if len(final_classes) > max_length:
            final_classes = final_classes[:max_length]
        else:    
            final_classes = np.lib.pad(final_classes, (0, max_length-len(final_classes)), 'constant', constant_values=0)

        final_classes = torch.from_numpy(final_classes)
        img = torch.from_numpy(np.float32(feats))
        # img_mask
        img_mask = (torch.sum(img != 1, dim=1) != 0).unsqueeze(-2)
        img = img * img_mask.squeeze().unsqueeze(-1).expand_as(img).long()

        return img, img_mask, final_classes

    elif feats.shape[0] > max_length:
        inds = sorted(random.sample(range(feats.shape[0]), max_length))
        feats = feats[inds]

        final_classes = np.array([classes[i] for i in inds])
        final_classes = torch.from_numpy(final_classes)
        
        img = torch.from_numpy(np.float32(feats))
        # img_mask
        img_mask = (torch.sum(img != 1, dim=1) != 0).unsqueeze(-2)
        img = img * img_mask.squeeze().unsqueeze(-1).expand_as(img).long()

        return img, img_mask, final_classes


class kesvi_dataset(Dataset):
    def __init__(self, data_dir, file_path, img_dir, split_type, tokenizers, max_vid_len, pair):
        en, ko = pair
        maps = {'en': 'en', 'ko': 'ko'}
        self.data_dir = data_dir
        self.img_dir = img_dir
        # load tokenizer
        self.tok_en, self.tok_ko = tokenizers
        self.max_vid_len = max_vid_len
        self.split_type = split_type
        with open(self.data_dir + 'label/' + 'kesvi_action_label.json', 'r', encoding='utf-8') as file:
            self.vid_classes = json.load(file)

        with open(self.data_dir+file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        self.encaps, self.kocaps = [], []
        self.sent_ids = list(data.keys())
        for i in range(len(list(data.values()))):
            self.encaps.append(list(data.values())[i][maps['en']])
            self.kocaps.append(list(data.values())[i][maps['ko']])

    def __len__(self):
        return len(self.encaps)

    def __getitem__(self, idx):
        # get src en
        str_encap,  sent_id = self.encaps[idx], self.sent_ids[idx]
        encap, ensrccap_mask, entgt_mask, caplen_en = self.tok_en.encode_sentence(str_encap)
        enref = self.tok_en.encode_sentence_nopad_2str(str_encap)

        # get src ko
        str_kocap, sent_id = self.kocaps[idx], self.sent_ids[idx]
        kocap, kosrccap_mask, kotgt_mask, caplen_ko = self.tok_ko.encode_sentence(str_kocap)
        koref = self.tok_ko.encode_sentence_nopad_2str(str_kocap)
        # print(f'[{idx}] / {str_encap} / {str_kocap} / {sent_id}')

        # get video_feature
        vid = sent_id[:-2]
        try: 
            video, video_mask, act_labels = load_video_features(os.path.join('/data/VMT/', self.img_dir, vid + '.npy'), self.max_vid_len, self.vid_classes[vid])
        except KeyError:
            video, video_mask, act_labels = load_fake_features()

        if self.split_type != 'test':
            return (encap, kocap), (ensrccap_mask, kosrccap_mask), (kotgt_mask, entgt_mask), video, video_mask, (caplen_ko, caplen_en), enref, koref, act_labels
        else:
            return (encap, kocap), (ensrccap_mask, kosrccap_mask), video, video_mask, sent_id, (kocap[1:], encap[1:]), enref, koref


def get_loader(data_dir, tokenizers, split_type, batch_size, max_vid_len, pair, num_workers, pin_memory):
    maps = {'train':['kesvi_train.json', 'extracted_features'], 'val': ['kesvi_val.json', 'extracted_features'],
        'test': ['kesvi_test.json', 'extracted_features']}
    file_path, img_dir = maps[split_type]
    mydata = kesvi_dataset(data_dir, file_path, img_dir, split_type, tokenizers, max_vid_len, pair)
    if split_type in ['train']:
        shuffle = True
    elif split_type in ['val', 'test']:
        shuffle = False

    myloader = DataLoader(dataset=mydata, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers, pin_memory=pin_memory)
    return myloader


def create_split_loaders(data_dir, tokenizers, batch_size, max_vid_len, pair, num_workers=0, pin_memory=False):
    train_loader = get_loader(data_dir, tokenizers, 'train', batch_size, max_vid_len, pair, num_workers, pin_memory)
    val_loader = get_loader(data_dir, tokenizers, 'val', batch_size, max_vid_len, pair, num_workers, pin_memory)
    test_loader = get_loader(data_dir, tokenizers, 'test', 1, max_vid_len, pair, num_workers, pin_memory)

    return train_loader, val_loader, test_loader

