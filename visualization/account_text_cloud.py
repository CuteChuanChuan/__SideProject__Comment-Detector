import jieba
import jieba.analyse

DICT_FILE = "tc_dict.txt"
STOP_FILE = "stopwords.txt"
TC_FONT_PATH = "NotoSerifTC-Regular.otf"

jieba.set_dictionary(DICT_FILE)
jieba.analyse.set_stop_words(STOP_FILE)



