import pandas as pd
import numpy as np
from glob import glob
import os

def simplify(df):
    collist = ['Other_dau', 'iOS_dau', 'Android_dau', 'Other_mau', 'iOS_mau', 'Android_mau',
              '13-14_dau', '15-19_dau', '15-24_dau', '20-24_dau', '25-29_dau', '30-34_dau', '35-39_dau', '40-44_dau',
              '45-49_dau', '50-54_dau', '55-59_dau', '25-64_dau', '60-64_dau', '13-nil_dau', '65-nil_dau',
              '13-14_mau', '15-19_mau', '15-24_mau', '20-24_mau', '25-29_mau', '30-34_mau', '35-39_mau', '40-44_mau',
              '45-49_mau', '50-54_mau', '55-59_mau', '25-64_mau', '60-64_mau', '13-nil_mau', '65-nil_mau',
              'Total_dau', 'Male_dau', 'Female_dau', 'Total_mau', 'Male_mau', 'Female_mau',
              'Graduated_dau', 'High_School_dau', 'No_Degree_dau', 'Graduated_mau', 'High_School_mau', 'No_Degree_mau']

    df = df[['access_device', 'ages_ranges', 'citizenship', 'genders', 'geo_locations', 'scholarities', 'dau_audience',
             'mau_audience']]
    access_device_df = pd.pivot_table(
        df[df['ages_ranges'] == "{u'min': 13}"][df['genders'] == 0][df['scholarities'].isnull()],
        values=['dau_audience', 'mau_audience'], index='citizenship', columns=['access_device'], fill_value=-1)
    ages_ranges_df = pd.pivot_table(df[df['genders'] == 0][df['scholarities'].isnull()][df['access_device'].isnull()],
                                    values=['dau_audience', 'mau_audience'], index='citizenship', columns='ages_ranges',
                                    fill_value=-1)
    genders_df = pd.pivot_table(
        df[df['ages_ranges'] == "{u'min': 13}"][df['scholarities'].isnull()][df['access_device'].isnull()],
        values=['dau_audience', 'mau_audience'], index='citizenship', columns='genders', fill_value=-1)
    scholarities_df = pd.pivot_table(
        df[df['ages_ranges'] == "{u'min': 13}"][df['genders'] == 0][df['access_device'].isnull()],
        values=['dau_audience', 'mau_audience'], index='citizenship', columns='scholarities', fill_value=-1)
    cdf = pd.concat([access_device_df, ages_ranges_df, genders_df, scholarities_df], axis=1)
    cdf.columns = collist
    cdf = cdf.reset_index()
    for index, rows in cdf.iterrows():
        if cdf.citizenship[index] == "{u'not': [6015559470583], u'name': u'All - Expats'}":
            cdf.citizenship[index] = "Locals"
        else:
            cdf.citizenship[index] = cdf.loc[index, 'citizenship'][
                                     cdf.loc[index, 'citizenship'].find('(') + 1:cdf.loc[index, 'citizenship'].find(')')]
    return cdf


if __name__ == "__main__":
    print("Simplifying all the files in ./static/original/...")

    for f in glob("./static/original/??_dataframe_collected_finished_*.csv.gz"):

        country_code = os.path.basename(f)[:2]
        df = pd.read_csv(f)
        dfs = simplify(df)

        dfs.to_csv("./static/simplified/%s.csv.gz" % (country_code), index=False)



