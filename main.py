from altair import Field
from fastapi import FastAPI, Body
from typing import Annotated
from pydantic import BaseModel
import uvicorn
import pickle
import pandas as pd
import numpy as np
import bz2file as bz2
import sklearn
from sklearn.metrics.pairwise import cosine_similarity

def decompress_pickle(file):
    data = bz2.BZ2File(file, 'rb')
    data = pickle.load(data)
    return data

global data,combined_features
#data = decompress_pickle('filename.pbz2')
data = pd.read_pickle("embedded2.pkl")
combined_features = np.vstack(data["combined_vector"])

class recommend:
    
    def find_similar_products(brand_name, k, category=None):
        # Filter the data for the selected brand name
        filtered_data = data[data["brand_name"] == brand_name]
        
        # Get the available categories for the selected brand
        available_categories = filtered_data["category"].unique().tolist()
        
        # Let the user select a category from the available categories or use the default
        if category is None or category not in available_categories:
            selected_category = available_categories[0]  # Select the first category by default
        else:
            selected_category = category
        
        # Filter the data further for the selected category
        filtered_data = filtered_data[filtered_data["category"] == selected_category]
        
        # Get the combined vectors for the selected products
        selected_product_indices = filtered_data.index.tolist()
        selected_product_vectors = combined_features[selected_product_indices]
        
        # Compute the cosine similarity between the selected product vectors and all other product vectors
        similarities = sklearn.metrics.pairwise.cosine_similarity(selected_product_vectors, combined_features)
        
        # Sort the similarities in descending order for each selected product and get the indices of the top-k similar products
        recommended_indices = []
        for i, product_index in enumerate(selected_product_indices):
            product_similarities = similarities[i]
            product_indices = np.argsort(product_similarities)[::-1][:] #[:k+1][:, ::-1]
            recommended_indices.append(product_indices)
            #recommended_indices.extend(product_indices) #optimized
        
        # Flatten the recommended indices list
        recommended_indices = np.array(recommended_indices).flatten()
        
        # Remove duplicate indices and the original selected product indices
        recommended_indices = np.unique(recommended_indices)
        #recommended_indices = np.setdiff1d(recommended_indices, selected_product_indices)
        
        # Retrieve the recommended products based on the indices
        recommended_products = data[["product_id","brand_name","product_title","category","rating","review_text","imgurl"]].iloc[recommended_indices]
   
        # Add the similarity score to the recommended products
        recommended_products["similarity"] = similarities.flatten()[recommended_indices]

        # Filter the recommended products to include only those with a rating greater than or equal to 3
        recommended_products = recommended_products[recommended_products["rating"] >= 3]
        

        # Filter the recommended products to include those with the same category or the first category by default
        same_category_brand_products = recommended_products[
            (recommended_products["category"] == selected_category) & 
            (recommended_products["brand_name"] == brand_name)
        ]
        same_category_products = recommended_products[
            (recommended_products["category"] == selected_category) & 
            (recommended_products["brand_name"] != brand_name)
        ]
        same_brand_products = recommended_products[
            (recommended_products["category"] != selected_category) & 
            (recommended_products["brand_name"] == brand_name)
        ]
        other_category_brand_products = recommended_products[
            (recommended_products["category"] != selected_category) & 
            (recommended_products["brand_name"] != brand_name)
        ]
        
        # Sort the recommended products based on the similarity score in descending order
        
        same_category_brand_products = same_category_brand_products.sort_values("similarity", ascending=False)
        other_category_brand_products = other_category_brand_products.sort_values("similarity", ascending=False)
        same_category_products = same_category_products.sort_values("similarity", ascending=False)
        same_brand_products = same_brand_products.sort_values("similarity", ascending=False)
        
        # Combine the sorted DataFrames
        recommended_products = pd.concat([same_category_brand_products, same_category_products, same_brand_products, other_category_brand_products]) #
        
        
        # Remove duplicate products based on product_id, retaining the one with the highest rating
        #recommended_products = recommended_products.sort_values("rating", ascending=False)
        recommended_products = recommended_products.drop_duplicates(subset="product_id", keep="first")
        # Convert the similarity column to numeric data type
        recommended_products["similarity"] = recommended_products["similarity"].apply(lambda x: round(x, 3))
        #Sort the recommended products based on the similarity score in descending order
        #recommended_products = recommended_products.sort_values("similarity", ascending=False)
        
        df = recommended_products.head(k)
        df = df.to_dict('records')        
        return df
    
app = FastAPI()

class Product(BaseModel):
    brand_name: str
    category : str
                      
@app.get("/{product_id}/{k}")
def get_recommendations_by_product_id(product_id : str, k: int = 5):
    '''Some Product IDs : [' B000NZW3J8 ','B000ULN4NO',' B00008JP7C ',' B001KU60XA ',' B0000ANHST ',' B004IPRWRC ',' B0037TPECK ',' B0068VM5T4 ',' B0085A43W8 '] '''
    product_id = product_id.strip()
    try:
        brand_name = data.loc[(data['product_id'] == product_id), 'brand_name'].values[0]
        category = data.loc[(data['product_id'] == product_id), 'category'].values[0]    
    except:
        # this means there are no matches in the dataframe
        return {"Error":"Sorry, no product found for this product id"}
    return recommend.find_similar_products(brand_name,k,category)

global example
example={
                "1": {
                  "summary": "A normal example 1",
                    "value": {
                                    "brand_name": "The Mountain",
                                    "category": "t-shirts"
                             },
                     },
                "2": {
                    "summary": "A normal example 2",
                    "value": {
                                "brand_name": "Alternative Men's",
                                "category": "hoodies sweatshirts big & tall"
                             },
                     },
                "3": {
                    "summary": "A normal example 3",
                    "value": {
                                "brand_name": "BIG BANG",
                                "category": "t-shirts men"
                             },
                     },
                "4": {
                    "summary": "A normal example 4",
                    "value": {
                                "brand_name": "Carhartt Men's",
                                "category": "carhartt tops t-shirts"
                             },
                     },
                "5": {
                    "summary": "A normal example 5",
                    "value": {
                                "brand_name": "Chestnut Hill",
                                "category": "casual button-down shirts"
                             },
                     },
                "6": {
                    "summary": "A normal example 6",
                    "value": {
                                "brand_name": "Chestnut Hill",
                                "category": "polos"
                             },
                     },
                "7": {
                    "summary": "A normal example 7",
                    "value": {
                                "brand_name": "Paul Fredrick",
                                "category": "big & tall dress shirts"
                             },
                     },
                "8": {
                    "summary": "A normal example 8",
                    "value": {
                                "brand_name": "Trump Men's",
                                "category": "casual button-down shirts big & tall dress shirts"
                             },
                     }
            }

@app.post("/{brand_name}/{category}/{k2}")
def get_recommendations_by_brand_name_and_category(prod : Annotated[Product,Body(examples = example)], k2: int = 5): #prodproduct_title : str,category : str

    try:
        rows = data[(data['brand_name'] == prod.brand_name) & (data['category'] == prod.category)].values[0]   
    except IndexError:
        # this means there are no matches in the dataframe
        return {"Error":"Sorry, no product found for this brand and category"}
    return recommend.find_similar_products(prod.brand_name,k2,prod.category)

#if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run(app, host="0.0.0.0", port=8000)
