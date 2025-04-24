#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import matplotlib.pyplot as plt


# In[2]:


# Step 1: Extract the Activities log section
with open("round3_final.log", "r") as f:
    lines = f.readlines()
#     print(lines)

# Step 2: Isolate the "Activities log" block
in_activities = False
activities_lines = []

for line in lines:
    if line.strip() == "Activities log:":
        in_activities = True
        continue
    if in_activities:
        if line.strip() == "" or line.endswith("log:\n"):  # new section or empty
            break
        activities_lines.append(line.strip())

# Step 3: Save the extracted log to a temporary file (optional, for clarity)
with open("activities_temp.log", "w") as f:
    for line in activities_lines:
        f.write(line + "\n")

# Step 4: Convert to CSV using pandas
df = pd.read_csv("activities_temp.log", sep=";", engine="python")
df.to_csv("activities_log.csv", index=False)


# In[3]:


df


# In[4]:


pnl = df.groupby(['timestamp', 'product'])['profit_and_loss'].sum().unstack(fill_value=0)
pnl


# In[5]:


products = ['RAINFOREST_RESIN', 'SQUID_INK', 'KELP']
pnl[products].plot(figsize=(10, 6))  # you can tweak figsize as you like

plt.title("PnL Over Time - RAINFOREST_RESIN, SQUID_INK, and KELP")
plt.xlabel("Timestamp")
plt.ylabel("Profit and Loss")
plt.legend(title="Product")
plt.grid(True)
plt.show()


# In[6]:


products = ['CROISSANTS', 'JAMS', 'DJEMBES']
pnl[products].plot(figsize=(10, 6))  # you can tweak figsize as you like

plt.title("PnL Over Time")
plt.xlabel("Timestamp")
plt.ylabel("Profit and Loss")
plt.legend(title="Product")
plt.grid(True)
plt.show()


# In[7]:


products = ['PICNIC_BASKET1','PICNIC_BASKET2']
pnl[products].plot(figsize=(10, 6))  # you can tweak figsize as you like

plt.title("PnL Over Time")
plt.xlabel("Timestamp")
plt.ylabel("Profit and Loss")
plt.legend(title="Product")
plt.grid(True)
plt.show()


# In[8]:


products = ['VOLCANIC_ROCK','VOLCANIC_ROCK_VOUCHER_9500','VOLCANIC_ROCK_VOUCHER_9750', 'VOLCANIC_ROCK_VOUCHER_10000', 'VOLCANIC_ROCK_VOUCHER_10250', 'VOLCANIC_ROCK_VOUCHER_10500']


# In[9]:


pnl[products].plot(figsize=(10, 6))  # you can tweak figsize as you like

plt.title("PnL Over Time")
plt.xlabel("Timestamp")
plt.ylabel("Profit and Loss")
plt.legend(title="Product")
plt.grid(True)
plt.show()


# In[ ]:





# In[ ]:




