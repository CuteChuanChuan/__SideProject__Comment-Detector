from src.crawler.dags.dag_crawling import decide_ptt_board


def test_returns_gossip_if_gossiping_in_url():
    url = "https://www.ptt.cc/bbs/Gossiping/M.1695226744.A.B77.html"
    assert decide_ptt_board(url) == "gossip"


def test_returns_politics_if_hatepolitics_in_url():
    url = "https://www.ptt.cc/bbs/HatePolitics/M.1695225366.A.8F4.html"
    assert decide_ptt_board(url) == "politics"
