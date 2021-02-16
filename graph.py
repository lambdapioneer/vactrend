import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def create_graph(
        df, fitted_curves,
        start_date, end_date,
        countries,
        output_filename='public/vactrend.png', scale=0.6):

    # Assume general 16:9 format and allow to `scale` font size
    fig, ax = plt.subplots(1, 1)
    fig.autofmt_xdate(rotation=45)
    fig.set_size_inches(16*scale, 9*scale)

    ax.set_xlim(start_date, end_date)
    ax.set_xlabel("Date: January 2021 to July 2021", weight='bold')
    ax.set_ylim(0, 200)
    ax.set_ylabel("Total vaccinations per 100 adults", weight='bold')
    ax.axhline(100, color='#000', lw=0.75)

    handles, labels = {}, {}
    for country in countries:
        # draw scatters of original entries
        raw_df = df[df.iso_code == country.iso].dropna()
        x = raw_df['date'].values
        y = raw_df['total_vaccinations_per_hundred'].values
        scatter_handle = ax.scatter(
            x, y, marker='+', alpha=0.75, color=country.color)

        # draw fitted curves
        fitted_curve = fitted_curves[country.iso]
        x, y, y_base = fitted_curve['x'], fitted_curve['y'], fitted_curve['y_base']
        line_handle, = ax.plot(x, y, ls='-', lw=1, color=country.color)

        ax.plot(x, y_base, ls='--', lw=1, color=country.color)

        ax.fill_between(x, y, y_base, facecolor=country.color,
                        interpolate=False, alpha=0.25)

        handles[country.iso] = (scatter_handle, line_handle)
        labels[country.iso] = (
            f"{country.name} (history)", f"{country.name} (optimistic)")

    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("$1^{st}$ %B"))

    ax.grid(True, color='#bbb', lw=1)
    ax.set_axisbelow(True)

    ax.legend(
        [x for hs in handles.values() for x in hs],
        [x for ls in labels.values() for x in ls],
        loc='upper right', bbox_to_anchor=(1, 1.16),
        ncol=2, frameon=False)

    plt.tight_layout()
    plt.savefig(output_filename, dpi=240)
