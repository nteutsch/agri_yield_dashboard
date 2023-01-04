import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache
def load_data(path):
    dataset = pd.read_csv(path)
    dataset.rename(columns = {'hg/ha_yield':'Yield (Tonnes)',
                              'average_rain_fall_mm_per_year':'Average Rainfall (mm)',
                              'pesticides_tonnes':'Pesticides (Tonnes)',
                              'avg_temp':'Average Temperature (C)'},
                   inplace=True)
    return dataset

@st.cache
def clean_average_data(df, countries, crops, years):
    main_df = df[df['Area'].str.strip().astype(bool)] #drop blanks
    main_df = main_df.drop('Unnamed: 0', axis=1) #drop column we dont need
    main_df.sort_values(by=['Area', 'Year'], inplace=True, ascending=[True, True])

    ave_df = pd.DataFrame(columns=main_df.columns) # new df to append to
    # take average for countries, year and crop that repeat in raw dataset
    # a faster method would need to be used for a real customer facing dashboard but the cache helps for now
    for country in countries:
        country_df = main_df[main_df['Area'] == country]
        for crop in crops:
            country_crop_df = country_df[country_df['Item'] == crop]
            for year in years:
                country_crop_year_df = country_crop_df[country_crop_df['Year'] == year]
                temp_stats = country_crop_year_df.mean(axis=0)
                temp_data = [country, crop, year,
                             temp_stats['Yield (Tonnes)'],
                             temp_stats['Average Rainfall (mm)'],
                             temp_stats['Pesticides (Tonnes)'],
                             temp_stats['Average Temperature (C)']]
                temp_df = pd.DataFrame([temp_data], columns=main_df.columns)
                ave_df = pd.concat([ave_df, temp_df], ignore_index=True)
    ave_df = ave_df[ave_df['Yield (Tonnes)'].notna()]
    ave_df.sort_values(by=['Area', 'Year'], inplace=True, ascending=[True, True])
    return ave_df

with st.sidebar:
    st.write('Welcome to my dashboard :wave:')
    st.write('')
    st.markdown('''
    This dashboard is intended to show the yield of different crops grown across the globe. 
    It also begins to look at key factors which may impact growth.
      
    Each section poses a few questions it intends to help answer, then suggest some next steps for analysis.
      
    The raw data is shown at the end of the page, for your reference.
      
    Please have a go and don't hesitate to get in touch.
      
    Thanks,  
    Natalie Teutsch
    ''')


# set up page heading
st.title(':seedling: Agricultural yield dashboard :seedling:')
#st.markdown('''*Authored by Natalie Teutsch*''')

# load in data
load_path = 'data/yield_df.csv'
raw_df = load_data(load_path)

# get some variable lists to help
countries = raw_df['Area'].drop_duplicates()
crops = raw_df['Item'].drop_duplicates()
years = raw_df['Year'].drop_duplicates()

# Perform some quick data clean up and sorting
ave_df = clean_average_data(raw_df, countries, crops, years)


######################################## section 1 #################################################
st.markdown('***')
st.header('Geographic distribution of crops per year')
st.markdown('''
This section is aimed at answering the following questions:  
* Which country grows the most of crops and does that change year on year?  
* Does yield correlate to rainfall or temperature?
  
The audience for this would be an external client or general public with an interest. 
Possibly they are looking at the global market for a crop to invest in or compete with.
  
I have included a line graph showing the total crop yield for all countries in the data set. 
It is clear that there is too much information to be displayed at once, in this manner. 
Instead, it would be better to investigate crops individually.
''')


# calculate total for crop yield per country and year
ave_pivot_df = pd.pivot_table(ave_df, index=['Area', 'Year'])
ave_pivot_df['Area'] = ave_pivot_df.index.get_level_values(0)
ave_pivot_df['Year'] = ave_pivot_df.index.get_level_values(1)

fig1 = px.line(ave_pivot_df,
               x='Year',
               y='Yield (Tonnes)',
               color='Area',
               labels={'Area':'Country'},
               title='Total crop yield per country per year.',
               color_discrete_sequence=px.colors.qualitative.Pastel)
fig1.update_layout(xaxis_title='Year',
                   yaxis_title='Total crop yield (Tonnes)')
fig1.update_traces(opacity=0.9)
st.plotly_chart(fig1)

st.markdown('''  
Therefore, I decided to use a choropleth to show each crop separately. 
A choropleth gives an overview of a large geographical data set.
The drop downs let the audience pick the crop and the information to be displayed.
By watching a country as the slider progresses, the audience can get a general idea of increase and decrease over time.
''')

# select display options
col1, col2 = st.columns([3, 2])
with col1:
    crop_sec1 = st.selectbox('Crop', crops)
with col2:
    display_sec1 = st.selectbox('Display:', ['Yield (Tonnes)', 'Average Rainfall (mm)', 'Average Temperature (C)'])

# filter for the crop
crop_sec1_df = ave_df[ave_df['Item'] == crop_sec1]

# show choropleth for yield, rainfall, temp
if display_sec1 == 'Yield (Tonnes)':
    this_colour_scale = 'greens'
elif display_sec1 == 'Average Rainfall (mm)':
    this_colour_scale = 'blues'
elif display_sec1 == 'Average Temperature (C)':
    this_colour_scale = 'reds'
fig2 = px.choropleth(crop_sec1_df,
                     locations="Area",
                     color=display_sec1,
                     hover_name='Area',
                     hover_data=['Item', 'Year', 'Yield (Tonnes)'],
                     locationmode='country names',
                     animation_frame='Year',
                     range_color=([0, crop_sec1_df[display_sec1].max()]),
                     color_continuous_scale=this_colour_scale,
                     labels={'Item':'Crop', 'Area':'Country'},
                     title='Animated choropleth world map showing '+display_sec1+' per country.')
fig2.update_layout(margin={"r": 50, "t": 50, "l": 0, "b": 0})
st.plotly_chart(fig2)

st.markdown('''
_Future analysis for this section could include comparing crop yield with other factors, such as 
yield per land area dedicated to that crop, crop export, and transport links._
''')


################################# section 2 #############################################################
st.markdown('***')
st.header('Crop yield and composition per country')
st.markdown('''
This section is aimed at answering the following questions:  
* Does the total crop yield vary with time?
* How does the crops grown break down in each country vary by year?
* Does pesticide use/ rainfall impact crop yield and does that vary with the crop?

This would be an external client or general public with an interest with in interest in a per country breakdown. 
Perhaps they are looking for a market opening for a particular country to invest in or compete with, 
or analysing their own performance to date.

Therefore, I decided to use a stacked bar chart as these are excellent for comparing data.
In this case, the bar chart compares the yield of each crop as well as overall yield.

The '*Normalise yield?*' option for the bar chart has been include so the audience can either look at the progression 
of total crop yield crops, or they can compare how the distribution of crops has changed over time. 

''')

country_sec2 = st.selectbox('Country', countries)
normalise_sec2 = st.checkbox('Normalise yield?')

# filter df for country
country_sec2_df = ave_df[ave_df['Area'] == country_sec2]
#normalise the yield per crop for each year
country_sec2_df['Normalised Yield (Tonnes)'] = \
    100*country_sec2_df['Yield (Tonnes)']/country_sec2_df.groupby('Year')['Yield (Tonnes)'].transform(sum)

# bar chart showing yield in tonnes per country
if normalise_sec2 == False:
    y_plot = 'Yield (Tonnes)'
    y_title = 'Yield (Tonnes)'
elif normalise_sec2 == True:
    y_plot = 'Normalised Yield (Tonnes)'
    y_title = 'Normalised Yield (%)'
fig3 = px.bar(country_sec2_df,
              x='Year',
              y=y_plot,
              color='Item',
              barmode='stack',
              title='Crop composition per year, for '+country_sec2+'.',
              labels={'Item':'Crop'},
              color_discrete_sequence=px.colors.qualitative.Pastel)
fig3.update_layout(xaxis_title='Year',
                   yaxis_title=y_title)
st.plotly_chart(fig3)

st.markdown('''
I have also decided to include a line graphs to show the pesticide and rainfall impact on yield, 
as this is a quantitative relationship.
The audience would likely want to see the trends, as well as easily read off the values.
''')

# yield (tonne) per tonne of pesticide used, coloured by crop
country_sec2_df['Yield/ Pesticides'] = country_sec2_df['Yield (Tonnes)']/country_sec2_df['Pesticides (Tonnes)']
fig4 = px.line(country_sec2_df,
               x='Year',
               y='Yield/ Pesticides',
               color='Item',
               labels={'Item':'Crop'},
               title='Crop yield per tonne of pesticide used per year, for '+country_sec2+'.',
               color_discrete_sequence=px.colors.qualitative.Pastel)
fig4.update_layout(xaxis_title='Year',
                   yaxis_title='Yield per tonne of pesticide used (Tonnes)')
st.plotly_chart(fig4)

# yield (tonne) per mm rainfall, coloured by crop
country_sec2_df['Yield/ Rainfall'] = country_sec2_df['Yield (Tonnes)']/country_sec2_df['Average Rainfall (mm)']
fig5 = px.line(country_sec2_df,
               x='Year',
               y='Yield/ Rainfall',
               color='Item',
               labels={'Item':'Crop'},
               title='Crop yield per mm of rainfall per year, for '+country_sec2+'.',
               color_discrete_sequence=px.colors.qualitative.Pastel)
fig5.update_layout(xaxis_title='Year',
                   yaxis_title='Yield per mm of rainfall (Tonnes)')
st.plotly_chart(fig5)

st.markdown('''
_Future analysis for this section could include comparing these graphs to crop prices.
This could allow optimisation of pesticide use in relation to gross revenue, to help customers make informed decisions._
  
_It would also be useful to compare these graphs with the land area used for crop growth, 
especially for the data using rainfall and pesticides used._
''')


################################# section 3 #############################################################
st.markdown('***')
st.subheader('Raw data, as loaded')
st.markdown('''
*Data source:* 
[Kaggle](https://www.kaggle.com/datasets/patelris/crop-yield-prediction-dataset?resource=download&select=yield_df.csv) 
''')

raw_df






