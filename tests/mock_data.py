import bs4
from datetime import datetime

mock_old_data_for_checking_updating = {
  "article_page_idx": 39211,
  "article_url": "https://www.ptt.cc/bbs/Gossiping/M.1695226745.A.B50.html",
  "article_data": {
    "author": "chun0303 (chun)",
    "ipaddress": "111.71.78.224",
    "title": "[新聞] 高雄2023萬年季國慶連假登場 重頭戲300",
    "time": 1695226743,
    "main_content": "\n1.媒體來源:\n\n自由時報\n\n2.記者署名:\n\n陳文嬋\n\n3.完整新聞標題:\n\n高雄2023萬年季國慶連假登場 重頭戲300人迓巨型火獅大遊行  \n\n4.完整新聞內文:\n\n〔記者陳文嬋／高雄報導〕2023萬年季「高雄迎火獅」將於國慶連假10月7日至9日在左營蓮\n池潭孔廟廣場登場，今年打造逾5公尺高巨型火獅，重頭戲迓火獅首度開放民眾參與，推出3\n00人迓火獅大遊行，節目也改以馬戲團、火舞等動態演出為主，還保留攻炮城等傳統特色文\n化迎賓，一起祈福保平安。\n\n高市府民政局長閻青智表示，左營萬年季今年邁入第23年，去年活動吸引30萬人潮，為地方\n商圈帶來廣大商機，今年為傳統民俗活動增添新元素，結合親子喜愛的表演，歡迎親子共襄\n盛舉。\n\n民政局今年不同以往，打造高逾5公尺、重達700多公斤的巨型火獅，壯觀更顯氣勢，更首度\n推出眾人迓火獅，開放300位民眾參與地方習俗，一起迓火獅祈福保平安，將於9月23日中午\n12時開放線上報名，報名至額滿為止。\n\n活動於國慶連假首日7日下午4時開始，由十鼓擊樂團演出揭開序幕，應援女神壯壯與柯大堡\n聯手主持開幕大戲，戊己劇團鄭子墉導演與藝想台灣團隊編製「家將大秀」接力登場。\n\n重頭戲迓火獅將於8日下午3時登場，300位民眾將於龍虎塔旁勝利、蓮潭路口空地集結，一\n路迓火獅大遊行至左營蓮池潭孔廟廣場，全長超過1公里，PLG夢想家啦啦隊隊長梓梓，也將\n率啦啦隊Formosa Sexy加入隊伍，體驗傳統火獅出巡樂趣。\n\n民政局表示，今年主舞台節目不同以往大多是演唱，改以動態表演為主，包括FOCA福爾摩沙\n馬戲團、即將成真火舞團等，輪番上陣演出，並結合在地10間廟宇，請吃紅龜粿、珠算餅、\n請喝青草茶等，民眾走廟巡禮，品嚐傳統美食。\n\n此外，國慶連假4天下午3時至晚上9時，孔廟及蓮池潭周邊也設有市集，融合古早味童玩及\n品牌商家、嚴選美食及質感小物，結合傳統習俗攻炮城、文化導覽等，讓民眾好逛、好吃又\n好玩。\n\n5.完整新聞連結 (或短網址)不可用YAHOO、LINE、MSN等轉載媒體:\n\nhttps://art.ltn.com.tw/article/breakingnews/4432801\n\n6.備註:\n\n",
    "last_crawled_datetime": 1695287890.569793,
    "num_of_comment": 2,
    "num_of_favor": 1,
    "num_of_against": 0,
    "num_of_arrow": 1,
    "comments": [
      {
        "commenter_id": "Healine",
        "commenter_ip": "1.200.36.97",
        "comment_time": 1695226919,
        "comment_type": "推",
        "comment_content": "大家一起出門被蚊子叮 一起登革熱～"
      },
      {
        "commenter_id": "kbten",
        "commenter_ip": "101.10.8.58",
        "comment_time": 1695227279,
        "comment_type": "→",
        "comment_content": "暖"
      },
    ]
  }
}

mock_new_data_for_checking_updating = {
    "author": "chun0303 (chun)",
    "ipaddress": "111.71.78.224",
    "title": "[新聞] 高雄2023萬年季國慶連假登場 重頭戲300",
    "time": 1695226743,
    "main_content": "\n1.媒體來源:\n\n自由時報\n\n2.記者署名:\n\n陳文嬋\n\n3.完整新聞標題:\n\n高雄2023萬年季國慶連假登場 重頭戲300人迓巨型火獅大遊行  \n\n4.完整新聞內文:\n\n〔記者陳文嬋／高雄報導〕2023萬年季「高雄迎火獅」將於國慶連假10月7日至9日在左營蓮\n池潭孔廟廣場登場，今年打造逾5公尺高巨型火獅，重頭戲迓火獅首度開放民眾參與，推出3\n00人迓火獅大遊行，節目也改以馬戲團、火舞等動態演出為主，還保留攻炮城等傳統特色文\n化迎賓，一起祈福保平安。\n\n高市府民政局長閻青智表示，左營萬年季今年邁入第23年，去年活動吸引30萬人潮，為地方\n商圈帶來廣大商機，今年為傳統民俗活動增添新元素，結合親子喜愛的表演，歡迎親子共襄\n盛舉。\n\n民政局今年不同以往，打造高逾5公尺、重達700多公斤的巨型火獅，壯觀更顯氣勢，更首度\n推出眾人迓火獅，開放300位民眾參與地方習俗，一起迓火獅祈福保平安，將於9月23日中午\n12時開放線上報名，報名至額滿為止。\n\n活動於國慶連假首日7日下午4時開始，由十鼓擊樂團演出揭開序幕，應援女神壯壯與柯大堡\n聯手主持開幕大戲，戊己劇團鄭子墉導演與藝想台灣團隊編製「家將大秀」接力登場。\n\n重頭戲迓火獅將於8日下午3時登場，300位民眾將於龍虎塔旁勝利、蓮潭路口空地集結，一\n路迓火獅大遊行至左營蓮池潭孔廟廣場，全長超過1公里，PLG夢想家啦啦隊隊長梓梓，也將\n率啦啦隊Formosa Sexy加入隊伍，體驗傳統火獅出巡樂趣。\n\n民政局表示，今年主舞台節目不同以往大多是演唱，改以動態表演為主，包括FOCA福爾摩沙\n馬戲團、即將成真火舞團等，輪番上陣演出，並結合在地10間廟宇，請吃紅龜粿、珠算餅、\n請喝青草茶等，民眾走廟巡禮，品嚐傳統美食。\n\n此外，國慶連假4天下午3時至晚上9時，孔廟及蓮池潭周邊也設有市集，融合古早味童玩及\n品牌商家、嚴選美食及質感小物，結合傳統習俗攻炮城、文化導覽等，讓民眾好逛、好吃又\n好玩。\n\n5.完整新聞連結 (或短網址)不可用YAHOO、LINE、MSN等轉載媒體:\n\nhttps://art.ltn.com.tw/article/breakingnews/4432801\n\n6.備註:\n\n",
    "last_crawled_datetime": datetime.now().timestamp(),
    "num_of_comment": 7,
    "num_of_favor": 3,
    "num_of_against": 0,
    "num_of_arrow": 4,
    "comments": [
      {
        "commenter_id": "Healine",
        "commenter_ip": "1.200.36.97",
        "comment_time": 1695226919,
        "comment_type": "推",
        "comment_content": "大家一起出門被蚊子叮 一起登革熱～"
      },
      {
        "commenter_id": "Behind4",
        "commenter_ip": "114.35.155.69",
        "comment_time": 1695227159,
        "comment_type": "推",
        "comment_content": "台灣民國 台灣民國 千秋萬世 直到永遠"
      },
      {
        "commenter_id": "kbten",
        "commenter_ip": "101.10.8.58",
        "comment_time": 1695227279,
        "comment_type": "→",
        "comment_content": "暖"
      },
      {
        "commenter_id": "ketrobo",
        "commenter_ip": "114.136.185.198",
        "comment_time": 1695227399,
        "comment_type": "→",
        "comment_content": "找人推一攤巴西茶葉蛋過去賣看看"
      },
      {
        "commenter_id": "jackycheny",
        "commenter_ip": "36.230.9.158",
        "comment_time": 1695227999,
        "comment_type": "→",
        "comment_content": "登革熱，有邁導我就問怎麼輸好暖嘻嘻"
      },
      {
        "commenter_id": "OGC168",
        "commenter_ip": "219.70.79.59",
        "comment_time": 1695230159,
        "comment_type": "→",
        "comment_content": "民主蚊愛你"
      },
      {
        "commenter_id": "a12c45a",
        "commenter_ip": "111.242.212.188",
        "comment_time": 1695248399,
        "comment_type": "推",
        "comment_content": "https://i.imgur.com/Lcc76qV.jpg"
      }
    ]
}


mock_data_for_checking_getting_num_comments = {
    "_id": "getting_num_comments",
    "article_page_idx": 39211,
    "article_url": "https://www.ptt.cc/bbs/Gossiping/M.1695226745.A.B50.html",
    "article_data": {
    "author": "chun0303 (chun)",
    "ipaddress": "111.71.78.224",
    "title": "[新聞] 高雄2023萬年季國慶連假登場 重頭戲300",
    "time": 1695226743,
    "main_content": "\n1.媒體來源:\n\n自由時報\n\n2.記者署名:\n\n陳文嬋\n\n3.完整新聞標題:\n\n高雄2023萬年季國慶連假登場 重頭戲300人迓巨型火獅大遊行  \n\n4.完整新聞內文:\n\n〔記者陳文嬋／高雄報導〕2023萬年季「高雄迎火獅」將於國慶連假10月7日至9日在左營蓮\n池潭孔廟廣場登場，今年打造逾5公尺高巨型火獅，重頭戲迓火獅首度開放民眾參與，推出3\n00人迓火獅大遊行，節目也改以馬戲團、火舞等動態演出為主，還保留攻炮城等傳統特色文\n化迎賓，一起祈福保平安。\n\n高市府民政局長閻青智表示，左營萬年季今年邁入第23年，去年活動吸引30萬人潮，為地方\n商圈帶來廣大商機，今年為傳統民俗活動增添新元素，結合親子喜愛的表演，歡迎親子共襄\n盛舉。\n\n民政局今年不同以往，打造高逾5公尺、重達700多公斤的巨型火獅，壯觀更顯氣勢，更首度\n推出眾人迓火獅，開放300位民眾參與地方習俗，一起迓火獅祈福保平安，將於9月23日中午\n12時開放線上報名，報名至額滿為止。\n\n活動於國慶連假首日7日下午4時開始，由十鼓擊樂團演出揭開序幕，應援女神壯壯與柯大堡\n聯手主持開幕大戲，戊己劇團鄭子墉導演與藝想台灣團隊編製「家將大秀」接力登場。\n\n重頭戲迓火獅將於8日下午3時登場，300位民眾將於龍虎塔旁勝利、蓮潭路口空地集結，一\n路迓火獅大遊行至左營蓮池潭孔廟廣場，全長超過1公里，PLG夢想家啦啦隊隊長梓梓，也將\n率啦啦隊Formosa Sexy加入隊伍，體驗傳統火獅出巡樂趣。\n\n民政局表示，今年主舞台節目不同以往大多是演唱，改以動態表演為主，包括FOCA福爾摩沙\n馬戲團、即將成真火舞團等，輪番上陣演出，並結合在地10間廟宇，請吃紅龜粿、珠算餅、\n請喝青草茶等，民眾走廟巡禮，品嚐傳統美食。\n\n此外，國慶連假4天下午3時至晚上9時，孔廟及蓮池潭周邊也設有市集，融合古早味童玩及\n品牌商家、嚴選美食及質感小物，結合傳統習俗攻炮城、文化導覽等，讓民眾好逛、好吃又\n好玩。\n\n5.完整新聞連結 (或短網址)不可用YAHOO、LINE、MSN等轉載媒體:\n\nhttps://art.ltn.com.tw/article/breakingnews/4432801\n\n6.備註:\n\n",
    "last_crawled_datetime": 1695287890.569793,
    "num_of_comment": 2,
    "num_of_favor": 1,
    "num_of_against": 0,
    "num_of_arrow": 1,
    "comments": [
      {
        "commenter_id": "Healine",
        "commenter_ip": "1.200.36.97",
        "comment_time": 1695226919,
        "comment_type": "推",
        "comment_content": "大家一起出門被蚊子叮 一起登革熱～"
      },
      {
        "commenter_id": "kbten",
        "commenter_ip": "101.10.8.58",
        "comment_time": 1695227279,
        "comment_type": "→",
        "comment_content": "暖"
      },
    ]
    }
}


example_article_soup = bs4.BeautifulSoup(
    ""
)