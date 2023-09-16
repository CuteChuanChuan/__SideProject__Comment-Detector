import streamlit as st
from data_processing.aggregate_mongo import count_articles, count_comments, count_accounts

total_articles = count_articles("gossip") + count_articles("politics")
total_comments = count_comments("gossip") + count_comments("politics")
total_accounts = count_accounts("gossip") + count_accounts("politics")

st.title("PTT Comment Detector")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<h6 style='text-align: center;'>Crawled Article Count</h6>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center;'>{total_articles}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align: center;'>Articles</h6>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<h6 style='text-align: center;'>Crawled Comment Count</h6>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center;'>{total_comments}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align: center;'>Comments</h6>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<h6 style='text-align: center;'>Crawled Account Count</h6>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center;'>{total_accounts}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h6 style='text-align: center;'>Accounts</h6>", unsafe_allow_html=True)

st.divider()


