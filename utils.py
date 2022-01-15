import json
import hashlib
import bencode
import shutil
import os

def load_file(file, default=None):
    config = None
    try:
        with open(file, 'r', encoding='utf-8') as json_file:
            config = json.load(json_file)
    except IOError:
        print("Error: 没有找到文件或读取文件失败")
        return default
    return config

def save_file(file, body):
    with open(file, 'w', encoding='utf-8') as json_file:
        config = json.dumps(body)
        json_file.write(config)
    return config

def rmfile(path):
    if (os.path.exists(path)):
        shutil.rmtree(path)

def hash_torrent(file):
    info = None
    try:
        f = open(file, 'rb')
        info = bencode.bdecode(f.read())['info']
        f.close()
    except Exception as e:
        print(f"Error: {e}")
        return None
    return hashlib.sha1(bencode.bencode(info)).hexdigest()