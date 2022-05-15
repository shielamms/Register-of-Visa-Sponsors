from flask import Flask
from flask import render_template
from flask import request
import csv
import tabula
import pandas as pd
import numpy as np

app = Flask(__name__)

def clean_char_cases(column_data):
    lower_case = list(column_data.str.lower())

    for i, t in enumerate(lower_case):
        lower_case[i] = ' '.join(list(map(lambda x: x.capitalize(), t.split())))

    return lower_case

@app.route('/refresh', methods=['GET'])
def parse_csv_file():
    file = 'https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/935287/2020-11-13_Tier_2_5_Register_of_Sponsors.pdf'

    tables = tabula.read_pdf(file, pages="1", multiple_tables=True, area=[200, 10, 800, 830],
                             pandas_options={'header': None})
    columns = ['Organization Name', 'Town/City', 'County', 'Tier & Rating', 'Sub Tier']

    first_page = tables[0]
    first_page.columns = columns

    total_pages_cell = first_page['Town/City'].iloc[len(first_page['Town/City']) - 1]
    total_pages = int(total_pages_cell.split()[-1])

    # Parse other pages
    other_pages = tabula.read_pdf(file, pages = '2-' + str(50), multiple_tables=True,
                                  area=[30, 10, 800, 828], pandas_options={'header': None})
    valid_columns = other_pages[0].columns

    for i, other in enumerate(other_pages):
        if len(other.columns) > 5:
            other_pages[i] = other.drop(2, axis=1)
            other_pages[i].columns = valid_columns

    new_df = pd.concat(other_pages)
    new_df.columns = columns

    all_data = pd.concat([first_page, new_df], axis=0).reset_index()

    # Clean the data
    all_data['Town/City'] = all_data['Town/City'].replace(to_replace=r'Page', value=np.nan, regex=True)
    all_data['Organization Name'] = all_data['Organization Name'].fillna(method='ffill')
    all_data['Town/City'] = all_data['Town/City'].fillna(method='ffill')
    # all_data['County'] = all_data['County'].fillna(method='ffill')

    all_data = all_data.drop(all_data.loc[all_data['Tier & Rating'].isna()].index, axis=0).drop(['index'], axis=1)
    all_data = all_data.reset_index(drop=True)

    all_data['Town/City'] = clean_char_cases(all_data['Town/City'])

    # Export csv
    all_data.to_csv('static/Register of Sponsors.csv', index=False)

@app.route('/', methods=['GET'])
def show_all_list():
    csv_file = 'static/Register of Sponsors.csv'

    results = []
    reader = None

    with open(csv_file, newline='\n') as file:
        reader = csv.DictReader(file)

        for row in reader:
            results.append(dict(row))

    col_names = [key for key in results[0].keys()]

    return render_template('index.html', results=results, col_names=col_names, num_cols=len(col_names))


if __name__ == '__main__':
    app.run(debug=True)

