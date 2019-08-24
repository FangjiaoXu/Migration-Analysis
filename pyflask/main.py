from flask import Flask, request, render_template, render_template_string
import pandas as pd
from glob import glob
import folium
import json
import requests
import os
import base64
import matplotlib
import re
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib import rc
from bs4 import BeautifulSoup
import seaborn as sns
import locale
# My functions
import plotmap
import mapping
import mapnavbar


app = Flask(__name__)

@app.route('/')
def index():
    countries = {}
    for i in glob('./static/original/??_dataframe*.csv.gz'):
        country_code = os.path.basename(i)[:2]
        countries[country_code] = mapping.convert_country_code(country_code)
    length = len(countries)

    # Sort list of countries by their names instead of by their code
    country_list = sorted(countries.items(), key=lambda x: x[1])
    li_path, li_country = zip(*country_list)
    return render_template("index.html", list_path=li_path, list_country=li_country, length=length)


@app.route('/plotgraph')
def plotgraph():
    gender = request.args.get('gender')
    scholarities = request.args.get('scholarities')
    os_var = request.args.get('os')
    countrycode = request.args.get('cc')
    relative = request.args.get('relative')
    path = glob('./static/original/%s_dataframe_collected_finished_*.csv.gz' % (countrycode))[0]
    maindf = pd.read_csv(path)
    # We make a copy of the dataframe, this way we can alter it later
    tempdf = maindf.dropna(subset=['citizenship']).copy()
    tempdf["citizenship"] = tempdf["citizenship"].apply(lambda s: s[s.find("(") + 1:s.find(")")])
    totaldf = tempdf[(tempdf['ages_ranges'] == "{u'min': 13}") & (tempdf['genders'] == 0) & (tempdf['scholarities'].isnull()) & (tempdf['access_device'].isnull())]
    totaldf = totaldf[['citizenship', 'mau_audience']]
    totaldf.columns = ['citizenship', 'total']

    if gender == 'both':
        tempdf = tempdf[(tempdf['genders'] == 0) & (tempdf['ages_ranges'] == "{u'min': 13}")]
    elif gender == 'male':
        tempdf = tempdf[(tempdf['genders'] == 1) & (tempdf['ages_ranges'] == "{u'min': 13}")]
    elif gender == 'female':
        tempdf = tempdf[(tempdf['genders'] == 2) & (tempdf['ages_ranges'] == "{u'min': 13}")]
    else:
        print("ERROR!!!! You forgot to select a gender.")

    if scholarities == 'all':
        tempdf = tempdf[tempdf['scholarities'].isnull()]
    elif scholarities == 'graduated':
        tempdf = tempdf[tempdf['scholarities'] == "{u'name': u'Graduated', u'or': [3, 7, 8, 9, 11]}"]
    elif scholarities == 'nodegree':
        tempdf = tempdf[tempdf['scholarities'] == "{u'name': u'No Degree', u'or': [1, 12, 13]}"]
    elif scholarities == 'highschool':
        tempdf = tempdf[tempdf['scholarities'] == "{u'name': u'High School', u'or': [2, 4, 5, 6, 10]}"]
    else:
        print("ERROR!!!! You forgot to select a scholarity option.")

    if os_var == 'all':
        tempdf = tempdf[tempdf['access_device'].isnull()]
    elif os_var == 'ios':
        tempdf = tempdf[tempdf['access_device'] == "{u'or': [6004384041172], u'name': u'iOS'}"]
    elif os_var == 'android':
        tempdf = tempdf[tempdf['access_device'] == "{u'or': [6004386044572], u'name': u'Android'}"]
    elif os_var == 'others':
        tempdf = tempdf[tempdf['access_device'] == "{u'not': [6004384041172, 6004386044572], u'name': u'Other'}"]
    else:
        print("ERROR!!!! You forgot to select an OS type.")

    tempdf = tempdf[['citizenship', 'mau_audience']]

    locals_str = "{u'not': [6015559470583], u'name': u'All - Expats'"
    tempdf.at[tempdf[tempdf["citizenship"] == locals_str].index[0], "citizenship"] = "Locals"
    tempdf = tempdf[~tempdf["citizenship"].isin(["Locals", "All ", "All"])]
    tempdf['citizenship'] = tempdf['citizenship'].apply(lambda x: x.replace(" ", "\n"))
    tempdf = tempdf[tempdf["mau_audience"] > 1000]

    if relative == 'on':
        tempdf = tempdf.set_index('citizenship').join(totaldf.set_index('citizenship')).reset_index()
        tempdf['mau_audience'] = (100 * tempdf['mau_audience'] ) / tempdf['total']
        # print(tempdf.sort_values('mau_audience', ascending=False).head(10))

    if tempdf.empty:
        fig, ax = plt.subplots(figsize=(9.5, 6))
        ax.set_xlabel('', labelpad=15)
        ax.set_ylabel('', labelpad=30)
        ax.set_yticks([])
        ax.set_xticks([0])
        plt.savefig('static/plot.png', transparent=True)
        plt.close()
        encoded = base64.b64encode(open('static/plot.png', 'rb').read()).decode()
        plothtml = 'data:image/png;base64,{}'
        plothtml = plothtml.format(encoded)
    else:
        fig, ax = plt.subplots(figsize=(12, 8.5))

        sns.barplot(x='citizenship', y='mau_audience',
                    data=tempdf.sort_values('mau_audience', ascending=False).head(10),
                    palette=sns.color_palette("YlGnBu"))
        ax.set_xlabel('', labelpad=15)
        if relative == 'on':
            ax.set_ylabel('Facebook Monthly Active Users (%)', labelpad=20, fontsize=18)
        else:
            ax.set_ylabel('Facebook Monthly Active Users', labelpad=20, fontsize=18)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        plt.xticks(rotation=15, fontsize=15.5)
        plt.yticks(fontsize=15.5)
        plt.savefig('static/plot.png', transparent=True)
        plt.close()
        encoded = base64.b64encode(open('static/plot.png', 'rb').read()).decode()
        plothtml = 'data:image/png;base64,{}'
        plothtml = plothtml.format(encoded)

    return render_template('plotgraph.html', plot=plothtml, gender=gender, scholarities=scholarities, os=os_var)

@app.route('/plotpie')
def plotpie():
    location = request.args.get('location')
    category = request.args.get('category')
    countrycode = request.args.get('cc')
    path = glob('static/simplified/{}.csv.gz'.format(countrycode))[0]
    maindf = pd.read_csv(path)
    df=maindf.head(2)
    fig, ax = plt.subplots(figsize=(9.5, 6))

    if category=='Gender':
        if location=='All':
            male=df.loc[1]['Male_mau']
            female=df.loc[1]['Female_mau']
        if location=='Local':
            male=df.loc[0]['Male_mau']
            female=df.loc[0]['Female_mau']
        else:
            male=df.loc[1]['Male_mau']-df.loc[0]['Male_mau']
            female=df.loc[1]['Female_mau']-df.loc[0]['Female_mau']
        ax.pie([male,female], labels=['male', 'female'], autopct='%1.1f%%', shadow=True, startangle=90)
        plt.savefig('myfig.png', transparent = True)
        encoded = base64.b64encode(open('myfig.png', 'rb').read()).decode()

    if category=='Education':
        if location=='All':
            Graduated=df.loc[1]['Graduated_mau']
            High_School=df.loc[1]['High_School_mau']
            No_Degree=df.loc[1]['No_Degree_mau']
        if location=='Local':
            Graduated=df.loc[0]['Graduated_mau']
            High_School=df.loc[0]['High_School_mau']
            No_Degree=df.loc[0]['No_Degree_mau']
        else:
            Graduated=df.loc[1]['Graduated_mau']-df.loc[0]['Graduated_mau']
            High_School=df.loc[1]['High_School_mau']-df.loc[0]['High_School_mau']
            No_Degree=df.loc[1]['No_Degree_mau']-df.loc[0]['No_Degree_mau']
        ax.pie([Graduated,High_School, No_Degree], labels=['Graduated', 'High_School', 'No_Degree'], autopct='%1.1f%%',
               shadow=True, startangle=90)
        plt.savefig('myfig.png', transparent = True)
        encoded = b64encode(open('myfig.png', 'rb').read()).decode()
            
    if category=='OS':
        if location=='All':
            other=df.loc[1]['Other_mau']
            ios=df.loc[1]['iOS_mau']
            android=df.loc[1]['Android_mau']
        if location=='Local':
            other=df.loc[0]['Other_mau']
            ios=df.loc[0]['iOS_mau']
            android=df.loc[0]['Android_mau']
        else:
            other=df.loc[1]['Other_mau']-df.loc[0]['Other_mau']
            ios=df.loc[1]['iOS_mau']-df.loc[0]['iOS_mau']
            android=df.loc[1]['Android_mau']-df.loc[0]['Android_mau']
        ax.pie([other,ios, android], labels=['other', 'ios', 'android'], autopct='%1.1f%%', shadow=True, startangle=90)
        plt.savefig('myfig.png', transparent = True)
        encoded = base64.b64encode(open('myfig.png', 'rb').read()).decode()
        

    piehtml = 'data:image/png;base64,{}'
    # piehtml = pietml.format(encoded)
    # plt.close()
    piehtml = piehtml.format(encoded)
    os.remove('myfig.png')

    return render_template('plotpie.html', pie=piehtml, location=location, category=category)

def donutpie(group_names, group_size, subgroup_names, subgroup_size, color, subcolor):
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    mypie, _ = ax.pie(group_size, radius=1.2, labels=group_names, colors=color, labeldistance=0.8,
                      textprops={'fontsize': 22})
    plt.setp(mypie, width=0.3, edgecolor='white')
    mypie2, _ = ax.pie(subgroup_size, radius=1.2 - 0.3, labels=subgroup_names, labeldistance=0.5,
                       colors=subcolor, textprops={'fontsize': 18})
    plt.setp(mypie2, width=0.4, edgecolor='white')
    plt.margins(0, 0)
    plt.savefig('static/myfig.png', transparent=True)
    plt.close()
    encoded = base64.b64encode(open('static/myfig.png', 'rb').read()).decode()
    piehtml = 'data:image/png;base64,{}'
    piehtml = piehtml.format(encoded)
    return piehtml


@app.route('/explore')
def explore():
    countrycode = request.args.get('cc')
    country = request.args.get('country')
    emigration = request.args.get('emigration')
    path = glob('static/simplified/{}.csv.gz'.format(countrycode))[0]
    maindf = pd.read_csv(path)
    df = maindf.set_index('citizenship')
    a, b, c, d = [plt.cm.Blues, plt.cm.Reds, plt.cm.Greens, plt.cm.Oranges]
    pie1 = donutpie(['Locals', 'Expats'], [df.loc['Locals', 'Total_mau'], df.loc['All', 'Total_mau']],
                    ['Male', 'Female', 'Male', 'Female'],
                    [df.loc['Locals', 'Male_mau'], df.loc['Locals', 'Female_mau'], df.loc['All', 'Male_mau'],
                     df.loc['All', 'Female_mau']],
                    [a(0.6), b(0.6)], [a(0.5), a(0.4), b(0.5), b(0.4)])

    pie2 = donutpie(['Locals', 'Expats'], [df.loc['Locals', 'Total_mau'], df.loc['All', 'Total_mau']],
                    ['iOS', 'Anroid', 'Others', 'iOS', 'Android', 'Others'],
                    [df.loc['Locals', 'iOS_mau'], df.loc['Locals', 'Android_mau'], df.loc['Locals', 'Other_mau'],
                     df.loc['All', 'iOS_mau'],
                     df.loc['All', 'Android_mau'], df.loc['All', 'Other_mau']],
                    [c(0.6), a(0.6)], [c(0.5), c(0.4), c(0.2), a(0.5), a(0.4),a(0.2)])

    pie3 = donutpie(['Locals', 'Expats'], [df.loc['Locals', 'Total_mau'], df.loc['All', 'Total_mau']],
                    ['Graduated', 'High School', 'No Degree', 'Graduated', 'High School', 'No Degree'],
                    [df.loc['Locals', 'Graduated_mau'], df.loc['Locals', 'High_School_mau'],
                     df.loc['Locals', 'No_Degree_mau'],
                     df.loc['All', 'Graduated_mau'],df.loc['All', 'High_School_mau'], df.loc['All', 'No_Degree_mau']],
                    [d(0.6), c(0.6)], [d(0.5), d(0.4), d(0.2), c(0.5), c(0.4), c(0.2)])
    #stacked barplot
    fig, ax = plt.subplots(figsize=(12, 7))
    mdf = maindf[maindf['citizenship'].apply(lambda x: x not in set(['All', 'Locals']))]
    mdf['citizenship'] = mdf['citizenship'].apply(lambda x: x.replace(" ", "\n"))
    mdf = mdf[mdf['Total_mau'] > 1000].sort_values('Total_mau', ascending=False).set_index('citizenship').head(10)
    bars2 = [ mdf.loc[i, 'Male_mau'] for i in mdf.index.values ]
    bars1 = [mdf.loc[i, 'Female_mau'] for i in mdf.index.values ]
    r = [i for i in range(len(mdf.index.values))]
    names = mdf.index.values
    plt.bar(r, bars1, color='#bfd96a', edgecolor='white', width=0.7, label='Female')
    plt.bar(r, bars2, bottom=bars1, color='#3c4d4d', edgecolor='white', width=0.7, label='Male')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.xticks(r, names, fontweight='bold', rotation=40)
    plt.legend()
    plt.savefig('static/myfig.png', transparent=True)
    plt.close()
    encoded = base64.b64encode(open('static/myfig.png', 'rb').read()).decode()
    barhtml = 'data:image/png;base64,{}'
    barhtml = barhtml.format(encoded)

    return render_template("explore.html", country=country, pie1=pie1, pie2=pie2, pie3=pie3,
                           bar1=barhtml, countrycode=countrycode, emigration=emigration)


def isdigit2(inputString):
    return any(char.isdigit() for char in inputString)

@app.route('/country/<countrycode>', methods=['get','post'])
def country(countrycode):

    country = mapping.convert_country_code(countrycode)
    path = glob('static/simplified/{}.csv.gz'.format(countrycode))[0]

    df = pd.read_csv(path)
    df = df[df['citizenship'].apply(lambda x: x not in set(['All', 'Locals']))]
    df['citizenship'] = df['citizenship'].apply(lambda x: x.replace(" ", "\n"))

    if df[df['Total_mau']>1000].empty:
        fig, ax = plt.subplots(figsize=(9.5, 6))
        ax.set_xlabel('Data insufficient', labelpad=15)
        ax.set_ylabel('', labelpad=30)
        ax.set_yticks([])
        ax.set_xticks([0])
        plt.savefig('static/plot.png', transparent=True)
        plt.close()
        encoded = base64.b64encode(open('static/plot.png', 'rb').read()).decode()
        html1 = 'data:image/png;base64,{}'
        html1 = html1.format(encoded)
    else:
        fig, ax = plt.subplots(figsize=(12, 8.5))
        sns.barplot(x='citizenship', y='Total_mau', data=df[df['Total_mau']>1000].sort_values('Total_mau',
                                                                                              ascending=False).head(10),
                palette=sns.color_palette("GnBu_d"))
        ax.set_xlabel('', labelpad=15)
        plt.xticks(rotation=15, fontsize=15.5)
        plt.yticks(fontsize=15.5)
        ax.set_ylabel('Facebook Monthly Active Users', labelpad=20, fontsize=16)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        plt.savefig('static/plotcountry1{}.png'.format(countrycode), transparent=True)
        plt.close()
        encoded = base64.b64encode(open('static/plotcountry1{}.png'.format(countrycode), 'rb').read()).decode()
        html1 = 'data:image/png;base64,{}'.format(encoded)
    url = 'http://data.un.org/en/iso/{}.html'.format(countrycode)
    countryData = requests.get(url).text
    soup = BeautifulSoup(countryData, 'lxml')
    tables = soup.find_all("tbody")
    lists, i = [[], []], 1
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8') #for 1000 separator
    for tag in tables[1].find_all('td'):
        if i == 1:
            lists[0].append(tag.text)
        elif i == 3:
            text = tag.text
            if ((isdigit2(text))&(text[1:].find('-')==-1)):
                text = int(re.sub(r"\D", "", text))
                text = "{:n}".format(text)
            lists[1].append(text)
        i += 1
        if i == 4:
            i = 1
    for index in range(2, 5):
        for tag in tables[index].find_all('td'):
            if i == 1:
                lists[0].append(tag.text)
            elif i == 4:
                text = tag.text
                if (isdigit2(text)):
                    text = int(re.sub(r"\D", "", text))
                    text = "{:n}".format(text)
                lists[1].append(text)
            i += 1
            if i == 5:
                i = 1
    attribute, value = lists[0], lists[1]

    emigration = "1"
    #check for emigration
    check = pd.read_csv('static/AllMigrants2.csv')
    if country not in check.columns:
        emigration = "0"
    url = 'http://data.un.org/en/iso/'+countrycode+'.html'
    return render_template("countryinfo.html", cc=countrycode, country=country, attribute=attribute,
                           value=value, length=len(attribute), htmlstring1=html1, htmlstring2=html1,
                           emigration=emigration, url=url)


@app.route('/maps/<countrycode>')
def maps(countrycode):
    return render_template("ImmigrationMaps/{}.html".format(countrycode))

@app.route('/emigration/<countrycode>')
def emigration(countrycode):
    country = mapping.convert_country_code(countrycode)
    return render_template('EmigrationMaps/{}.html'.format(country))
    # country = mapping.convert_country_code(countrycode)
    # check = pd.read_csv('static/AllMigrants2.csv')
    # if country in check.columns:
    #     df = pd.read_csv('static/Emigration/{}.csv'.format(country))
    #     bmap = plotmap.BaseMap(data=df, shapefile='../places.geojson')
    #     bmap.createGroup('Gender')
    #     g = plotmap.Geojson(bmap, 'Gender', 'Total', country, locationcol='Location')
    #     g.colorMap(column1='Total_mau')
    #     g.createMap(key='name')
    #     bmap.groupedLayerControl(['Gender'])
    #     mapnavbar.FloatImage().add_to(bmap.map)
    #     return render_template_string(bmap.map.get_root().render())
    # else:
    #     return render_template_string("Information not available.")


@app.route('/map/<countrycode>')
def map(countrycode):
    path = glob('./static/simplified/{}.csv.gz'.format(countrycode))[0]
    df = pd.read_csv(path)
    country = mapping.convert_country_code(countrycode)

    bmap = plotmap.BaseMap(data=df, shapefile='../places.geojson')
    bmap.createGroup('Gender')
    g = plotmap.Geojson(bmap, 'Gender', 'Total', country, locationcol='citizenship')
    g.colorMap(column1='Total_mau')
    g.createMap(key='name')

    g.addValue(["Male_mau", "Female_mau"], " of the population are males")
    g.addValue(['Female_mau', "Male_mau", ], " of the population are females")

    g.addValue(["Other_mau", "iOS_mau", "Android_mau"], " of the population are using other operating system")
    g.addValue(["iOS_mau", "Other_mau", "Android_mau"], " of the population are using iOS operating system")
    g.addValue(["Android_mau", "iOS_mau", "Other_mau"], " of the population are using Android operating system")

    g.addValue(["No_Degree_mau", "Graduated_mau", "High_School_mau"], " of the population do not have a degree")
    g.addValue(["Graduated_mau", "High_School_mau", "No_Degree_mau"], " of the population graduated from college")
    g.addValue(["High_School_mau", "Graduated_mau", "No_Degree_mau"], " of the population have a high school degree")

    g.addInfoBox(countrycode)

    g = plotmap.Geojson(bmap, 'Gender', 'Male', country, locationcol='citizenship')
    g.colorMap(column1='Male_mau')
    #g.colorMap(column1='Male_mau', threshold_min1=1001)
    g.createMap(key='name')

    g.addValue(["Male_mau", "Female_mau"], " of the population are males")
    g.addValue(['Female_mau', "Male_mau", ], " of the population are females")

    g.addValue(["Other_mau", "iOS_mau", "Android_mau"], " of the population are using other operating system")
    g.addValue(["iOS_mau", "Other_mau", "Android_mau"], " of the population are using iOS operating system")
    g.addValue(["Android_mau", "iOS_mau", "Other_mau"], " of the population are using Android operating system")

    g.addValue(["No_Degree_mau", "Graduated_mau", "High_School_mau"], " of the population do not have a degree")
    g.addValue(["Graduated_mau", "High_School_mau", "No_Degree_mau"], " of the population graduated from college")
    g.addValue(["High_School_mau", "Graduated_mau", "No_Degree_mau"], " of the population have a high school degree")

    g.addInfoBox(countrycode)

    g = plotmap.Geojson(bmap, 'Gender', 'Female', country,  locationcol='citizenship')
    g.colorMap(column1='Female_mau')
    #g.colorMap(column1='Female_dau', threshold_min1=1001)
    g.createMap(key='name')

    g.addValue(["Male_mau", "Female_mau"], " of the population are males")
    g.addValue(['Female_mau', "Male_mau", ], " of the population are females")

    g.addValue(["Other_mau", "iOS_mau", "Android_mau"], " of the population are using other operating system")
    g.addValue(["iOS_mau", "Other_mau", "Android_mau"], " of the population are using iOS operating system")
    g.addValue(["Android_mau", "iOS_mau", "Other_mau"], " of the population are using Android operating system")

    g.addValue(["No_Degree_mau", "Graduated_mau", "High_School_mau"], " of the population do not have a degree")
    g.addValue(["Graduated_mau", "High_School_mau", "No_Degree_mau"], " of the population graduated from college")
    g.addValue(["High_School_mau", "Graduated_mau", "No_Degree_mau"], " of the population have a high school degree")

    g.addInfoBox(countrycode)
    bmap.groupedLayerControl(['Gender'])

    '''bmap.createGroup('Facts')
    f= plotmap.interestingFacts(bmap, 'Facts', 'interesting fact', 'citizenship')
    f.addFacts(['Total_mau', 'Other_mau', 'iOS_mau', 'Android_mau'], ('Other', 'iOS', 'Android'),'trophy.png', 'phone.png')

    bmap.groupedLayerControl(['Gender','Facts'])'''
    mapnavbar.FloatImage().add_to(bmap.map)
    return render_template_string(bmap.map.get_root().render())

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/FAQ')
def FAQ():
    return render_template("FAQ.html")

@app.route('/hostcountry')
def hostcountry():
    return render_template("hostcountry.txt")

@app.route('/homecountry')
def homecountry():
    return render_template("homecountry.txt")



if __name__ == "__main__":
    app.run(debug=True)
