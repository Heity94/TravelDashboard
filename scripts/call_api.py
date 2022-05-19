#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import requests
import pandas as pd
path = '/home/jonas_pieper/project/api_call/output/'


# In[2]:


def call_flight_api():
        response = requests.get("https://opensky-network.org/api/states/all").json()
        flights = pd.DataFrame(response["states"])
        flights['time'] = response['time']
        flights.to_csv(path+f"{response['time']}.csv")


# In[3]:


call_flight_api()


# In[ ]:




