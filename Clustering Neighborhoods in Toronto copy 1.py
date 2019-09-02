#!/usr/bin/env python
# coding: utf-8

# In[25]:


LIMIT = 100
def getNearbyVenues(names, latitudes, longitudes, radius=500):
    
    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)
            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            radius, 
            LIMIT)
            
        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']
        
        # return only relevant information for each nearby venue
        venues_list.append([(
            name, 
            lat, 
            lng, 
            v['venue']['name'], 
            v['venue']['location']['lat'], 
            v['venue']['location']['lng'],  
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighborhood', 
                  'Neighborhood Latitude', 
                  'Neighborhood Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    
    return(nearby_venues)


# In[26]:


#get the top venues that are in North York within a radius of 500 meters
NorthYork_venues = getNearbyVenues(names=NorthYork_data['Neighborhood'],
                                   latitudes=NorthYork_data['Latitude'],
                                   longitudes=NorthYork_data['Longitude']
                                  )


# In[27]:


NorthYork_venues.head()


# In[28]:


NorthYork_venues.shape


# In[29]:


#how many venues were returned for each neighborhood:
NorthYork_venues.groupby('Neighborhood').count()


# In[30]:


## analtzing each neighborhood:
# one hot encoding
NorthYork_onehot = pd.get_dummies(NorthYork_venues[['Venue Category']], prefix="", prefix_sep="")

# add neighborhood column back to dataframe
NorthYork_onehot['Neighborhood'] = NorthYork_venues['Neighborhood'] 

# move neighborhood column to the first column
fixed_columns = [NorthYork_onehot.columns[-1]] + list(NorthYork_onehot.columns[:-1])
NorthYork_onehot = NorthYork_onehot[fixed_columns]

NorthYork_onehot.head()


# In[31]:


NorthYork_onehot.shape


# In[32]:


# grouping rows by neighborhoods:
NorthYork_grouped = NorthYork_onehot.groupby('Neighborhood').mean().reset_index()
NorthYork_grouped


# In[33]:


NorthYork_grouped.shape


# In[34]:


def return_most_common_venues(row, num_top_venues):
    row_categories = row.iloc[1:]
    row_categories_sorted = row_categories.sort_values(ascending=False)
    
    return row_categories_sorted.index.values[0:num_top_venues]


# In[35]:


num_top_venues = 10

indicators = ['st', 'nd', 'rd']

# create columns according to number of top venues
columns = ['Neighborhood']
for ind in np.arange(num_top_venues):
    try:
        columns.append('{}{} Most Common Venue'.format(ind+1, indicators[ind]))
    except:
        columns.append('{}th Most Common Venue'.format(ind+1))

# create a new dataframe
neighborhoods_venues_sorted = pd.DataFrame(columns=columns)
neighborhoods_venues_sorted['Neighborhood'] = NorthYork_grouped['Neighborhood']

for ind in np.arange(NorthYork_grouped.shape[0]):
    neighborhoods_venues_sorted.iloc[ind, 1:] = return_most_common_venues(NorthYork_grouped.iloc[ind, :], num_top_venues)

neighborhoods_venues_sorted.head()


# In[36]:


# set number of clusters
kclusters = 5

NorthYork_grouped_clustering = NorthYork_grouped.drop('Neighborhood', 1)

# run k-means clustering
kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(NorthYork_grouped_clustering)

# check cluster labels generated for each row in the dataframe
kmeans.labels_[0:10] 


# In[37]:


# add clustering labels
neighborhoods_venues_sorted.insert(0, 'Cluster Labels', kmeans.labels_)

NorthYork_merged = NorthYork_data

# merge toronto_grouped with toronto_data to add latitude/longitude for each neighborhood
NorthYork_merged = NorthYork_merged.join(neighborhoods_venues_sorted.set_index('Neighborhood'), on='Neighborhood')

NorthYork_merged.head() # check the last columns!


# In[38]:


# create clustered map
map_clusters = folium.Map(location=[latitude, longitude], zoom_start=11)

# set color scheme for the clusters
x = np.arange(kclusters)
ys = [i + x + (i*x)**2 for i in range(kclusters)]
colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
rainbow = [colors.rgb2hex(i) for i in colors_array]

# add markers to the map
markers_colors = []
for lat, lon, poi, cluster in zip(NorthYork_merged['Latitude'], NorthYork_merged['Longitude'], NorthYork_merged['Neighborhood'], NorthYork_merged['Cluster Labels']):
    label = folium.Popup(str(poi) + ' Cluster ' + str(cluster), parse_html=True)
    folium.CircleMarker(
        [lat, lon],
        radius=5,
        popup=label,
        fill=True,
        fill_opacity=0.7).add_to(map_clusters)
       
map_clusters


# In[39]:


# cluster 1:
NorthYork_merged.loc[NorthYork_merged['Cluster Labels'] == 0, NorthYork_merged.columns[[1] + list(range(5, NorthYork_merged.shape[1]))]]

# we can call this cluster "Shopping Stores" because it is the most common word in this cluster.


# In[40]:


# cluster 2:
NorthYork_merged.loc[NorthYork_merged['Cluster Labels'] == 1, NorthYork_merged.columns[[1] + list(range(5, NorthYork_merged.shape[1]))]]

# we can call this cluster "Restaurant" because it is the most common word in this cluster.


# In[41]:


# cluster 3:
NorthYork_merged.loc[NorthYork_merged['Cluster Labels'] == 2, NorthYork_merged.columns[[1] + list(range(5, NorthYork_merged.shape[1]))]]

# we can call this cluster "Multi-shops and stores" because there is no common word in this cluster.


# In[42]:


# cluster 4:
NorthYork_merged.loc[NorthYork_merged['Cluster Labels'] == 3, NorthYork_merged.columns[[1] + list(range(5, NorthYork_merged.shape[1]))]]

# we can call this cluster "Convenience" because it seems it is common word with (coming in different titiles) in this cluster.


# In[43]:


# cluster 5:
NorthYork_merged.loc[NorthYork_merged['Cluster Labels'] == 4, NorthYork_merged.columns[[1] + list(range(5, NorthYork_merged.shape[1]))]]

# we can call this cluster "Parks" because it is common word with in this cluster.


# In[ ]:




