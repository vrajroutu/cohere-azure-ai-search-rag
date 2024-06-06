import streamlit as st  
from utils.studio_style import apply_studio_style  
  
if __name__ == '__main__':  
    st.set_page_config(  
        page_title="Welcome"  
    )  
    apply_studio_style()  
    st.title("Welcome to Cohere & Azure AI Search RAG")  
    st.markdown("""  
        Explore Retrieval-Augmented Generation (RAG) with Cohere and Azure AI Search. This demo shows how to use Cohere Embed V3 for generating int8 and binary embeddings, reducing memory costs while maintaining high search quality. Integrate these embeddings with Azure AI Search and perform RAG using CommandR+ in Azure AI Studio.  
    """)  
    st.markdown("""  
        Store and search over Cohere's latest Embed-V3-Multilingual and Embed V3-English int8 embeddings using Azure AI Search. This offers significant memory cost reductions while maintaining high search quality, making it ideal for semantic search over large datasets powering your Generative AI applications.  
    """) 
    st.image("./assets/dashboard.png", caption="With int8 Cohere embeddings available in Azure AI Search, Cohere and Azure users alike can now run advanced RAG using a memory-optimized embedding model and a state-of-the-art retrieval system.", use_column_width=True)   
    st.markdown("""  
         Read the full announcement from Cohere [here](https://cohere.com/blog/int8-binary-embeddings).  
    """, unsafe_allow_html=True)  
    st.markdown("""  
        <div style="text-align: center;">  
            <a href="https://www.linkedin.com/pulse/your-article-link" target="_blank">Read our latest LinkedIn article on RAG with Cohere and Azure AI Search</a>  
        </div>  
    """, unsafe_allow_html=True)  

# Sidebar  
LOGO_URL = "./assets/cohererag.png"  # Replace with your logo URL  
st.logo(LOGO_URL, link="https://www.linkedin.com/in/vrajkishoreroutu/", icon_image=LOGO_URL)  
st.sidebar.title("Contact Us")      
col1, col3 = st.sidebar.columns(2)  
col1.metric("Devlopers", "1", "-8%")  
col3.metric("Uptime", "96%", "4%")  


