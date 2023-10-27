# Comment-Detector

## Table of Contents
* [Introduction](#Introduction)
* [Architecture](#Architecture)
* [Data](#Data)
* [Feature](#Feature)
* [Tools](#Tools)
* [Monitoring](#Monitoring)
* [Clip](#Clip)
* [Contact](#Contact)


## Introduction
#### A dashboard offering users comprehensive & insightful data about PTT (Taiwan's largest forum)
#### Users can form judgment about cyber warriors (網軍) and people manipulating public opinions (帶風向) 
#### Platform: [https://comment-detector.com](https://comment-detector.com)
![Homepage](readme-img/Homepage.png)


## Architecture
![Architecture](readme-img/Architecture.png)

### Compute Engine #1:
- Aim 1: Executing web crawling every 10 minute orchestrated by Apache Airflow on Docker
- Aim 2: Cleaning and extracting data 
- On: GCP Compute Engine

### Compute Engine #2:
- Aim: Deploying Redis as cache system storing data updated by Python scripts scheduled by APScheduler
- On: GCP Compute Engine

### Database
- Aim: Storing cleaned data and providing data for platform
- On: MongoDB Atlas

### Dashboard (Application)
- Aim: Retrieving data from MongoDB and demonstrating organized data for users
- On: image managed by Cloud Run 

## Data
### Source
- PTT - Gossiping which has the largest number of users.
- PTT - HatePolitics which is highly related to politics.

### ETL
- Extract: web crawling (requests + Beautiful Soup)
- Transform: python (data cleaning and extraction)
- Load: MongoDB

## Feature
- Trend (趨勢分析)：
  - 提供資料量數據
  - 呈現熱門關鍵字與文章
- Keywords (關鍵字分析)：
  - 使用者輸入想要了解的關鍵字後，儀表板會呈現與關鍵字相關的熱門文章
  - 統計出留言數量前20名的留言者，以及留言者之間的關係 (Concurrency Analysis)
- Commenter (留言者分析)：
  - 使用者輸入想要了解的留言者後，儀表板會呈現該留言者的活躍時段
  - 彙整該留言者的所有留言，並彙整成文字雲
- 開源資料 API：
  - 獲得更多資訊：IP 與作者等



## Tools
| Category       | Tool/Technique                  |
|----------------|---------------------------------|
| Database       | MongoDB                         |
| Data Pipeline  | Airflow                         |
| Dashboard      | Plotly Dash                     |
| Backend        | FastAPI                         |
| Cache system   | Redis                           |
| Autoscaling    | Cloud Run                       |
| Load Balancing | Cloud Load Balancing            |
| Monitoring     | Cloud Monitoring, Cloud Logging |
| Others         | GCP Compute Engine              |


## Monitoring
#### Overall
- ![overall](readme-img/monitoring-overall.png)
#### Airflow
- ![airflow](readme-img/monitoring-airflow.png)
#### Dashboard
- ![dashboard](readme-img/monitoring-dashboard.png)

## Clip
#### 趨勢分析
- ![Trend](readme-img/demo-trend.gif)
#### 關鍵字分析
- ![Keyword](readme-img/demo-keyword.gif)
#### 留言者分析
- ![Commenter](readme-img/demo-commenter.gif)
#### APIs
- ![ipaddress](readme-img/demo-api.gif)




## Contact
Raymond Hung kirk336neo@gmail.com
