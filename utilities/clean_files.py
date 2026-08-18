# clean_files.py
import os


def clean_files(target_dir=None):
    if target_dir is None:
        target_dir = os.getcwd()

    if not os.path.exists(target_dir):
        return

    key_words_to_delete = ["acis", "rpy", ".rec", ".log", ".lck"]

    for file_name in os.listdir(target_dir):
        file_path = os.path.join(target_dir, file_name)

        if os.path.isfile(file_path) and any(palavra in file_name for palavra in key_words_to_delete):
            try:
                os.remove(file_path)
            except Exception:
                pass