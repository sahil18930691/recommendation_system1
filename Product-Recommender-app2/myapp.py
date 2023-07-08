import base64
import streamlit as st
import time
import requests
import PIL.Image
import io
import pickle
import pandas as pd
import numpy as np
import bz2file as bz2

def decompress_pickle(file):
    data = bz2.BZ2File(file, 'rb')
    data = pickle.load(data)
    return data

FASTAPI_URL = "https://product-recommender.azurewebsites.net"

#FASTAPI_URL = "http://localhost:8000"

df = pd.read_pickle("embedded2.pkl")
#df = decompress_pickle('sentencetransformer2.pbz2')
product_id_options = df['product_id'].value_counts().sort_values(ascending=False)
product_id_options = product_id_options.index.tolist()
#product_id_options=['B000NZW3J8','B000ULN4NO','B00008JP7C','B001KU60XA','B0000ANHST','B004IPRWRC','B0037TPECK','B0068VM5T4','B0085A43W8']
brand_options = df['brand_name'].value_counts().sort_values(ascending=False)
brand_options = brand_options.index.tolist()
brand_name=''
category=''

default_image_url = "https://via.placeholder.com/200x200?text=No+Image"

st.set_page_config(page_title='Product Recommender',page_icon='🛒', layout='wide')
page_bg_img = f"""
<style>
[data-testid="stVerticalBlock"]{{
max-width: 100rem;
border-radius: 8px;
padding:15px 15px 15px 15px;
background: rgb(0 0 0 / 0.9%);
}}
</style>
"""

st.markdown(page_bg_img, unsafe_allow_html=True)
st.title("Product Recommender")

col1, col2,col3 = st.columns(3)
col1.subheader("Search by **Product** ID or **Brand & Category** ")
k = col2.slider('Select Number of Products to be recommended',5, 10, 5) 
if col3.button("Clear"):
    st.session_state.productidbox = ''
    st.session_state.brandbox = ''
    st.session_state.categorybox = ''
    st.experimental_rerun()
    
          
col1, col2, col3 = st.columns(3)
product_id = col1.selectbox('**Or Select a Product ID**', [''] + product_id_options,key = 'productidbox')

if product_id:
    brand_name=''
    category=''
    brand_name = df.loc[(df['product_id'] == product_id), 'brand_name'].values[0]
    category = df.loc[(df['product_id'] == product_id), 'category'].values[0]         
    
# Get the product title and category from the user
brand_name1 = col2.selectbox('**Select a Brand**', [''] + brand_options,key = 'brandbox')
prod_category_options = list(set(df.loc[df['brand_name'] == brand_name1]['category'].tolist()))
category1 = col3.selectbox("**Select a category**", [''] + prod_category_options,key = 'categorybox') 

if brand_name1 and category1:
    brand_name = brand_name1
    category = category1
elif brand_name1 and not category1:
    time.sleep(5)
    st.warning("Please Choose a Category")
       
if product_id or (brand_name1 and category1):
    # Send a POST request to the FastAPI endpoint with the user input as JSON data
    response = requests.post(f"{FASTAPI_URL}/{brand_name}/{category}/{k}", json={"brand_name": brand_name, "category": category})
    data = response.json()
    with st.container():
        if "Error" in data:
            st.error(data["Error"])
        else:
            st.write(f"**Recommendations for Brand- _:orange[{brand_name}]_ and Category - _:orange[{category}]_:**")
            for item in data:
                # Check if the product_img_url field is present and valid
                if "imgurl" in item and item["imgurl"]:
                    try:
                        # Get the image data from the product_img_url field
                        img_data = requests.get(item["imgurl"]).content
                        # Convert the image data to a bytes object
                        img_bytes = io.BytesIO(img_data)
                        # Open the image from the bytes object
                        img = PIL.Image.open(img_bytes)
                    except Exception as e:
                        # If there is an exception, use the default or placeholder image instead
                        img_data = requests.get(default_image_url).content
                        img_bytes = io.BytesIO(img_data)
                        img = PIL.Image.open(img_bytes)
                else:
                    # If there is no valid product_img_url field, use the default or placeholder image instead
                    img_data = requests.get(default_image_url).content
                    img_bytes = io.BytesIO(img_data)
                    img = PIL.Image.open(img_bytes)
                # Display the image, title, and similarity score in a column layout
                col1, col2 = st.columns([2, 8])
                with col1:
                    st.image(img, use_column_width="auto") #width=200
                with col2: 
                    similarity_percentage = item['similarity'] * 100
                    color = "green" if similarity_percentage >= 60 else "red"
                    st.markdown(f"🔗 Product ID - **{item['product_id']} <span style='color:{color}'>{similarity_percentage:.2f}% </span>** match", unsafe_allow_html=True)
                    
                    #st.markdown(f"**<span style='color:{color}'>{similarity_percentage:.2f}% </span>Match**", unsafe_allow_html=True)

                    st.markdown(f"🔗 Title - **{item['product_title']}**")
                    st.markdown(f"🔗 Brand - **{item['brand_name']}**")
                    st.markdown(f"🔗 Rating - **{item['rating']}** ⭐")
                    st.markdown(f"🔗 Category - **{item['category']}**") 
                    #st.markdown(f"🔗 Review - {item['review_text'].replace('$', 'USD')}")
                    with st.expander(f"🔗 Open review ✍️ "):
                        st.markdown(f"**{item['review_text'].replace('$', 'USD')}**")  
                    #st.markdown(f"**{item['similarity']*100}% Match**")          
            st.success('**Successful Recommendation!**', icon="✅")
