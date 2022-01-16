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

def get_files(path, postfix=None):
    files = []
    if not path or not os.path.exists(path):
        return files
    if os.path.isfile(path):
        files.append(path)
    else:
        for name in os.listdir(path):
            if postfix and not name.endswith(postfix):
                continue
            files.append(os.path.join(path, name))
    return files

def hash_torrent(file):
    info = None
    if not os.path.exists(file) or os.path.isdir(file):
        return None
    try:
        f = open(file, 'rb')
        info = bencode.bdecode(f.read())['info']
        f.close()
    except Exception as e:
        print(f"Error: {e}")
        return None
    return hashlib.sha1(bencode.bencode(info)).hexdigest()
