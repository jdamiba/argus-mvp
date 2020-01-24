from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required
from config import Config
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from datetime import datetime
import pybaseball as pb
import plotly.express as px
import pandas as pd

# Method to protect dash views/routes
def protect_dashviews(dashapp):
    dashapp.url_base_pathname = "/dashboard/"
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(
                dashapp.server.view_functions[view_func]
            )


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = "login"

external_stylesheets = [
    "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"
]

dash_app = dash.Dash(
    __name__,
    server=app,
    url_base_pathname="/dashboard/",
    external_stylesheets=external_stylesheets,
)

with app.app_context():
    dash_app.title = "MLB Pitcher Scouting Report"
    dash_app.layout = html.Div(
        children=[
            html.Nav(
                className="navbar",
                children=[
                    html.A("Home", href="/"),
                    html.A("Logout", href="/logout"),
                    html.H1(
                        children=[
                            html.A(
                                className="navbar-brand",
                                children="MLB Pitcher Scouting Report",
                                href="/scouting-report",
                            )
                        ]
                    )
                ],
            ),
            html.Div(
                className="mr-5 ml-5 mt-0 pt-2 jumbotron",
                children=[
                    dcc.Markdown("#### First Name"),
                    dcc.Input(
                        className="mb-3", id="first-name", value="Gerrit", type="text"
                    ),
                    dcc.Markdown("#### Last Name"),
                    dcc.Input(
                        className="mb-3", id="last-name", value="Cole", type="text"
                    ),
                    dcc.Markdown("#### Date Range"),
                    dcc.DatePickerRange(
                        className="mb-3",
                        id="date-picker",
                        min_date_allowed=datetime(2019, 3, 20),
                        max_date_allowed=datetime(2019, 9, 29),
                        initial_visible_month=datetime(2019, 3, 20),
                    ),
                    dcc.Markdown("#### Infield Fielding Alignment"),
                    dcc.Dropdown(
                        className="mb-3 w-25",
                        id="infield-dropdown",
                        options=[
                            {"label": "Standard", "value": "Standard"},
                            {"label": "Shift", "value": "Infield shift"},
                        ],
                        value="Standard",
                    ),
                    dcc.Markdown("#### Outfield Fielding Alignment"),
                    dcc.Dropdown(
                        className="w-25",
                        id="outfield-dropdown",
                        options=[
                            {"label": "Standard", "value": "Standard"},
                            {"label": "Strategic", "value": "Strategic"},
                        ],
                        value="Standard",
                    ),
                    html.Button(
                        "Create Data Visualizations!",
                        id="button",
                        className="btn btn-primary mt-3 mb-3",
                    ),
                ],
            ),
            dcc.Loading(html.Div(id="graph-div")),
        ],
    )

    @dash_app.callback(
        Output(component_id="graph-div", component_property="children"),
        [
            Input("button", "n_clicks"),
            Input("date-picker", "start_date"),
            Input("date-picker", "end_date"),
            Input("infield-dropdown", "value"),
            Input("outfield-dropdown", "value"),
        ],
        [
            State(component_id="first-name", component_property="value"),
            State(component_id="last-name", component_property="value"),
        ],
    )
    def update_output_div(
        n_clicks, start_date, end_date, infield, outfield, first_name, last_name,
    ):
        # only update on increment
        prev_clicks = 0
        if (
            start_date is None
            or n_clicks is None
            or end_date is None
            or first_name is None
            or last_name is None
            or n_clicks == prev_clicks
            or infield is None
            or outfield is None
        ):
            raise PreventUpdate
        else:
            data = get_data(first_name, last_name, start_date, end_date)

            data = data[data["if_fielding_alignment"] == infield]
            data = data[data["of_fielding_alignment"] == outfield]

            strikes = [
                i
                for i in data["Result of Pitch"]
                if i == "called_strike" or i == "swinging_strike"
            ]
            balls = [i for i in data["Result of Pitch"] if i == "ball"]
            foul = [i for i in data["Result of Pitch"] if i == "foul"]

            FF = len(data[data["Pitch Type"] == "4-Seam Fastball"])
            KC = len(data[data["Pitch Type"] == "Knuckle Curve"])
            CU = len(data[data["Pitch Type"] == "Curveball"])
            CH = len(data[data["Pitch Type"] == "Changeup"])
            SL = len(data[data["Pitch Type"] == "Slider"])
            FT = len(data[data["Pitch Type"] == "2-Seam Fastball"])

            pitch_type_bar = px.bar(
                y=[FF, KC, CU, CH, SL, FT],
                x=[
                    "4-Seam Fastball",
                    "Knuckle Curve",
                    "Curveball",
                    "Changeup",
                    "Slider",
                    "2-Seam Fastball",
                ],
                title=f"Bar Chart of {first_name} {last_name}'s Pitch Selection Between {start_date} and {end_date}",
                template="plotly_dark",
            ).update_layout(xaxis_title="Pitch Type", yaxis_title="Count")

            pitch_type_pie = px.pie(
                values=[FF, KC, CU, CH, SL, FT],
                names=[
                    "4-Seam Fastball",
                    "Knuckle Curve",
                    "Curveball",
                    "Changeup",
                    "Slider",
                    "2-Seam Fastball",
                ],
                title=f"Pie Chart of {first_name} {last_name}'s Pitch Selection Between {start_date} and {end_date}",
                template="plotly_dark",
            ).update_traces(textinfo="percent+label")

            pitch_type_scatter = px.scatter(
                data,
                x="Pitch Number",
                y="Pitch Speed",
                color="Pitch Type",
                trendline="ols",
                hover_data=["Result of Pitch", "Play by Play"],
                title=f"3D Scatter Plot of {first_name} {last_name}'s Pitch Speed Between {start_date} and {end_date}",
                template="plotly_dark",
            )

            pitch_type_box = px.box(
                data,
                x="Pitch Type",
                y="Pitch Speed",
                color="Pitch Type",
                points="all",
                hover_data=["Result of Pitch", "Play by Play"],
                title=f"Box Plot of {first_name} {last_name}'s Pitch Speed Between {start_date} and {end_date}",
                template="plotly_dark",
            )

            prev_clicks = prev_clicks + 1

            return [
                dcc.Graph(figure=pitch_type_pie),
                dcc.Graph(figure=pitch_type_bar),
                dcc.Graph(figure=pitch_type_scatter),
                dcc.Graph(figure=pitch_type_box),
            ]

    def get_data(first_name, last_name, start_date, end_date):
        try:
            key = pb.playerid_lookup(last_name, first_name)["key_mlbam"].values[
                0
            ]  # get unique pitcher identifier
        except:
            pass

        data = pb.statcast_pitcher(
            start_date, end_date, key
        )  # get dataset of pitches thrown by pitcher
        data = data.sort_values(
            ["pitch_number"]
        )  # sort pitches by order thrown, earliest first
        data = data.dropna(
            subset=["pitch_type", "des", "description", "release_spin_rate"]
        )  # make sure dataset does not contain nulls

        data["order"] = data.reset_index().index  # create new column with pitch order

        df = pd.DataFrame(data)

        df = df.rename(
            {
                "des": "Play by Play",
                "description": "Result of Pitch",
                "order": "Pitch Number",
                "pitch_name": "Pitch Type",
                "release_speed": "Pitch Speed",
            },
            axis=1,
        )

        return df


protect_dashviews(dash_app)

from app import routes, models

if __name__ == "__main__":
    dash_app.run_server(debug=True)
