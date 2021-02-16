import collections
import graph
import pandas as pd
import pytz
import urllib.request

from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader, select_autoescape
from scipy.optimize import curve_fit


# Config countries
Country = collections.namedtuple(
    'Country',
    ['iso', 'name', 'color', 'emoji']
)
COUNTRIES = [
    Country('GBR', 'United Kingdom', '#007bff', '🇬🇧'),
    Country('DEU', 'Germany', '#28a745', '🇩🇪')
]

# Config date limits
START_DATE = datetime.strptime('2021-01-01', '%Y-%m-%d')  # x-axis min
END_DATE = datetime.strptime('2021-07-01', '%Y-%m-%d')  # x-axis max
MAX_DATE = datetime.strptime('2022-12-31', '%Y-%m-%d')  # extrapolation limit


def load_data(filename="vaccinations.csv"):
    df = pd.read_csv(filename)

    df = df[df['iso_code'].isin([c.iso for c in COUNTRIES])]
    df = df[['iso_code', 'date', 'total_vaccinations_per_hundred']]

    # we add a convenience `days` column for making the curve fitting code simpler
    df['date'] = pd.to_datetime(df['date'])
    df['days'] = df['date'].map(lambda x: (x - START_DATE).days)
    return df


def calc_fitted_curves(df):
    """Calculates fitted polynomials of degree three and two for each country.
    Then returns extrapolated series from START_DATE to MAX_DATE.
    """

    def prototype_function_d3(x, a, b, c):
        return a * (x ** 2) + b * (x ** 1) + c

    def prototype_function_d2(x, b, c):
        return b * (x ** 1) + c

    fitted_curves = {c.iso: None for c in COUNTRIES}
    for iso in fitted_curves:
        fitting_df = df[df.iso_code == iso].dropna()
        x = fitting_df['days'].values
        y = fitting_df['total_vaccinations_per_hundred'].values

        # 3rd-degree polynomial accounting for increasing supply (optimistic case)
        params_d3, _ = curve_fit(prototype_function_d3, x, y, (0.5, 0.5, 0.5))

        # 2nd-degree polynomial accounting only for the average rate up to date
        params_d2, _ = curve_fit(prototype_function_d2, x, y, (0.5, 0.5))

        # Create series of extrapolates values for each country
        fitted_curve = {'x': [], 'y': [], 'y_base': []}
        fitted_curves[iso] = fitted_curve

        curr_date = START_DATE
        while curr_date <= MAX_DATE:
            fitted_curve['x'].append(curr_date)
            day = (curr_date - START_DATE).days

            fitted_curve['y'].append(
                prototype_function_d3(day, *params_d3))
            fitted_curve['y_base'].append(
                prototype_function_d2(day, *params_d2))

            curr_date += timedelta(days=1)
    return fitted_curves


def gen_html(df, fitted_curves, template_filename="index.html.jinja"):
    jinja_env = Environment(
        loader=FileSystemLoader('./'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = jinja_env.get_template(template_filename)

    def get_curr(iso):
        """Returns highest value for country."""
        d = df[df.iso_code == iso].dropna()
        return max(d['total_vaccinations_per_hundred'].values)

    def get_date_for_target(iso, target):
        """Returns date when fitted curve passes target."""
        curve = fitted_curves[iso]
        for date, y in zip(curve['x'], curve['y']):
            if y > target:
                return date
        return MAX_DATE

    def get_daily_rate(iso):
        """Returns difference between the two most recent values."""
        d = df[df.iso_code == iso].dropna()
        tail = d['total_vaccinations_per_hundred'][-2:].values
        return "+%.2f" % (tail[1] - tail[0])

    data_per_country = {c.iso: {} for c in COUNTRIES}
    for c in COUNTRIES:
        data_per_country[c.iso] = {
            'curr': get_curr(c.iso),
            'daily_rate': get_daily_rate(c.iso),
            'optimistic_date_100': get_date_for_target(c.iso, 100),
            'optimistic_date_200': get_date_for_target(c.iso, 200),
        }

    return template.render(
        countries=COUNTRIES,
        data_per_country=data_per_country,
        last_update=datetime.now(pytz.timezone('GMT'))
    )


if __name__ == "__main__":
    print("[ ] Downloading data")
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv",
        "vaccinations.csv")

    print("[ ] Reading data")
    df = load_data()

    print("[ ] Computing extrapolations")
    fitted_curves = calc_fitted_curves(df)

    print("[ ] Creating graph")
    graph.create_graph(
        df, fitted_curves,
        START_DATE, END_DATE,
        COUNTRIES,
    )

    print("[ ] Creating html")
    html = gen_html(df, fitted_curves)
    with open("public/index.html", "w") as f:
        f.write(html)

    print("[+] Done")
