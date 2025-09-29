"""Real-time monitoring dashboard for the Ocean Hazard Monitoring system"""
import logging
import threading
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

class OceanHazardDashboard:
    """Real-time monitoring dashboard for ocean hazards"""
    
    def __init__(self, data_collector=None, hazard_detector=None, refresh_interval=60):
        """Initialize the dashboard
        
        Args:
            data_collector: Data collector instance (optional)
            hazard_detector: Hazard detector instance (optional)
            refresh_interval: Data refresh interval in seconds (default: 60)
        """
        # Store references to data components
        self.data_collector = data_collector
        self.hazard_detector = hazard_detector
        self.refresh_interval = refresh_interval
        
        # Initialize data storage
        self.current_hazards = []
        self.hazard_history = []
        self.location_data = {}
        
        # Initialize dash application
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.app.title = "Ocean Hazard Monitoring System"
        
        # Set up layout
        self.setup_layout()
        
        # Set up callbacks
        self.setup_callbacks()
        
        # Initialize data refresh thread
        self.running = False
        self.refresh_thread = None
        
        logger.info("OceanHazardDashboard initialized successfully")
    
    def setup_layout(self):
        """Set up the dashboard layout"""
        # Define color scheme based on hazard severity
        self.severity_colors = {
            "high": "#dc3545",  # Red
            "medium": "#ffc107",  # Yellow
            "low": "#17a2b8",  # Cyan
            "unknown": "#6c757d"  # Gray
        }
        
        # Define hazard type icons
        self.hazard_icons = {
            "flood": "🚨",
            "storm_surge": "🌊",
            "tsunami": "🌊⚡",
            "high_waves": "🌊",
            "erosion": "🏖️",
            "marine_pollution": "🚮",
            "harmful_algal_bloom": "🟢",
            "coastal_storm": "⛈️"
        }
        
        # Main layout
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("Ocean Hazard Monitoring System", className="text-center mb-4", style={'color': '#007bff'})
                ])
            ]),
            
            # Status and Refresh Control
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("System Status", className="card-title"),
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.Span("Last Updated: "),
                                        html.Span(id="last-updated", children="Never")
                                    ])
                                ], width=6),
                                dbc.Col([
                                    dbc.Button("Refresh Data", id="refresh-button", color="primary", className="float-right")
                                ], width=6)
                            ])
                        ])
                    ])
                ], width=12)
            ]),
            
            # Overview Stats
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Active Hazards", className="card-title"),
                            html.H2(id="active-hazards-count", children="0", style={'color': '#dc3545'})
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("High Severity", className="card-title"),
                            html.H2(id="high-severity-count", children="0", style={'color': '#dc3545'})
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Medium Severity", className="card-title"),
                            html.H2(id="medium-severity-count", children="0", style={'color': '#ffc107'})
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Low Severity", className="card-title"),
                            html.H2(id="low-severity-count", children="0", style={'color': '#17a2b8'})
                        ])
                    ])
                ], width=3)
            ], className="mb-4"),
            
            # Hazard Map and Distribution
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Hazard Locations", className="card-title"),
                            dcc.Graph(id="hazard-map", config={'displayModeBar': False}, style={'height': '400px'})
                        ])
                    ])
                ], width=7),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Hazard Distribution", className="card-title"),
                            dcc.Graph(id="hazard-distribution", config={'displayModeBar': False}, style={'height': '400px'})
                        ])
                    ])
                ], width=5)
            ], className="mb-4"),
            
            # Recent Hazards Table
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Recent Hazard Reports", className="card-title"),
                            html.Div(id="hazard-table-container", style={'maxHeight': '400px', 'overflowY': 'auto'})
                        ])
                    ])
                ], width=12)
            ]),
            
            # Hidden components for callbacks
            dcc.Interval(
                id='interval-component',
                interval=self.refresh_interval * 1000,  # in milliseconds
                n_intervals=0
            ),
            dcc.Store(id='hazards-data')
        ], fluid=True)
    
    def setup_callbacks(self):
        """Set up the dashboard callbacks"""
        
        # Refresh data when interval or refresh button is triggered
        @self.app.callback(
            [Output('hazards-data', 'data'),
             Output('last-updated', 'children')],
            [Input('interval-component', 'n_intervals'),
             Input('refresh-button', 'n_clicks')],
            prevent_initial_call=False
        )
        def refresh_data(n_intervals, n_clicks):
            """Refresh hazard data"""
            self.collect_and_analyze_data()
            last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self._prepare_data_for_dashboard(), last_updated
        
        # Update stats based on hazard data
        @self.app.callback(
            [Output('active-hazards-count', 'children'),
             Output('high-severity-count', 'children'),
             Output('medium-severity-count', 'children'),
             Output('low-severity-count', 'children')],
            [Input('hazards-data', 'data')]
        )
        def update_stats(hazards_data):
            """Update hazard statistics"""
            if not hazards_data:
                return "0", "0", "0", "0"
            
            df = pd.DataFrame(hazards_data)
            total = len(df)
            high = len(df[df['severity'] == 'high'])
            medium = len(df[df['severity'] == 'medium'])
            low = len(df[df['severity'] == 'low'])
            
            return str(total), str(high), str(medium), str(low)
        
        # Update hazard map
        @self.app.callback(
            Output('hazard-map', 'figure'),
            [Input('hazards-data', 'data')]
        )
        def update_hazard_map(hazards_data):
            """Update hazard map visualization"""
            fig = go.Figure()
            
            # Add base map
            fig.update_layout(
                mapbox_style="carto-positron",
                mapbox_zoom=3,
                mapbox_center={"lat": 37.0902, "lon": -95.7129},  # Center on the US
                height=400,
                margin={"r": 0, "t": 0, "l": 0, "b": 0}
            )
            
            if not hazards_data:
                return fig
            
            df = pd.DataFrame(hazards_data)
            
            # Filter only hazards with location data
            df = df[df['latitude'].notna() & df['longitude'].notna()]
            
            if len(df) == 0:
                return fig
            
            # Add hazard markers for each severity level
            for severity, color in self.severity_colors.items():
                severity_df = df[df['severity'] == severity]
                if len(severity_df) > 0:
                    fig.add_trace(
                        go.Scattermapbox(
                            lat=severity_df['latitude'],
                            lon=severity_df['longitude'],
                            mode='markers',
                            marker=dict(
                                size=10,
                                color=color,
                                opacity=0.8
                            ),
                            text=severity_df['description'],
                            name=f'{severity.capitalize()} Severity'
                        )
                    )
            
            # Update legend and layout
            fig.update_layout(legend_title="Hazard Severity")
            
            return fig
        
        # Update hazard distribution chart
        @self.app.callback(
            Output('hazard-distribution', 'figure'),
            [Input('hazards-data', 'data')]
        )
        def update_hazard_distribution(hazards_data):
            """Update hazard distribution visualization"""
            if not hazards_data:
                # Create empty figure
                fig = go.Figure()
                fig.update_layout(
                    height=400,
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    annotations=[
                        dict(
                            text="No data available",
                            x=0.5,
                            y=0.5,
                            showarrow=False,
                            font=dict(size=14)
                        )
                    ]
                )
                return fig
            
            df = pd.DataFrame(hazards_data)
            
            # Create hazard type count
            hazard_counts = {}
            for _, row in df.iterrows():
                hazards = row.get('hazards', [])
                for hazard in hazards:
                    hazard_counts[hazard] = hazard_counts.get(hazard, 0) + 1
            
            # Create severity count
            severity_counts = df['severity'].value_counts().to_dict()
            
            # Create subplots
            from plotly.subplots import make_subplots
            fig = make_subplots(rows=2, cols=1, vertical_spacing=0.2)
            
            # Add hazard type chart
            if hazard_counts:
                fig.add_trace(
                    go.Bar(
                        x=list(hazard_counts.keys()),
                        y=list(hazard_counts.values()),
                        name='Hazard Types',
                        marker_color='#007bff'
                    ),
                    row=1, col=1
                )
            
            # Add severity chart
            if severity_counts:
                colors = [self.severity_colors.get(s, '#6c757d') for s in severity_counts.keys()]
                fig.add_trace(
                    go.Bar(
                        x=list(severity_counts.keys()),
                        y=list(severity_counts.values()),
                        name='Severity Levels',
                        marker_color=colors
                    ),
                    row=2, col=1
                )
            
            # Update layout
            fig.update_layout(
                height=400,
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                showlegend=False
            )
            
            fig.update_xaxes(title_text="Hazard Type", row=1, col=1)
            fig.update_yaxes(title_text="Count", row=1, col=1)
            fig.update_xaxes(title_text="Severity Level", row=2, col=1)
            fig.update_yaxes(title_text="Count", row=2, col=1)
            
            return fig
        
        # Update hazard table
        @self.app.callback(
            Output('hazard-table-container', 'children'),
            [Input('hazards-data', 'data')]
        )
        def update_hazard_table(hazards_data):
            """Update hazard table"""
            if not hazards_data:
                return html.P("No hazard reports available.")
            
            df = pd.DataFrame(hazards_data)
            
            # Sort by timestamp (newest first)
            df = df.sort_values('timestamp', ascending=False)
            
            # Create table
            table_header = [
                html.Thead(html.Tr([
                    html.Th("Time"),
                    html.Th("Location"),
                    html.Th("Hazard Type"),
                    html.Th("Severity"),
                    html.Th("Description")
                ]))
            ]
            
            rows = []
            for _, row in df.head(20).iterrows():
                # Format timestamp
                try:
                    timestamp = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00')).strftime('%H:%M:%S')
                except:
                    timestamp = row['timestamp']
                
                # Format hazards
                hazards = row.get('hazards', [])
                hazard_text = ", ".join([f"{self.hazard_icons.get(h, '⚠️')} {h}" for h in hazards])
                
                # Format severity with color
                severity = row.get('severity', 'unknown')
                severity_color = self.severity_colors.get(severity, '#6c757d')
                
                rows.append(
                    html.Tr([
                        html.Td(timestamp),
                        html.Td(row.get('location', '')),
                        html.Td(hazard_text),
                        html.Td(html.Span(severity, style={'color': severity_color, 'fontWeight': 'bold'})),
                        html.Td(row.get('description', '')[:100] + '...' if len(row.get('description', '')) > 100 else row.get('description', ''))
                    ])
                )
            
            table_body = [html.Tbody(rows)]
            
            return dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True)
    
    def collect_and_analyze_data(self):
        """Collect and analyze hazard data"""
        try:
            if self.data_collector and self.hazard_detector:
                # Collect data from all sources
                raw_data = self.data_collector.collect_all_data()
                
                # Analyze the collected data
                analyzed_data = self.hazard_detector.analyze_batch_reports(raw_data)
                
                # Prioritize the reports
                prioritized_reports = self.hazard_detector.prioritize_reports(analyzed_data)
                
                # Update current hazards and history
                self.current_hazards = prioritized_reports
                self.hazard_history.extend(prioritized_reports)
                
                # Keep history to a reasonable size
                if len(self.hazard_history) > 1000:
                    self.hazard_history = self.hazard_history[-1000:]
                
                logger.info(f"Collected and analyzed {len(prioritized_reports)} hazard reports")
            else:
                # Generate mock data if no data collector or detector is provided
                self._generate_mock_data()
        except Exception as e:
            logger.error(f"Error collecting and analyzing data: {str(e)}")
    
    def _generate_mock_data(self):
        """Generate mock data for demonstration purposes"""
        # Mock data with various hazard types, severities, and locations
        mock_data = [
            {
                "id": "mock_1",
                "description": "Major flooding near the pier in Coastal City. Water levels rising rapidly.",
                "location": "Coastal City",
                "latitude": 34.0522,
                "longitude": -118.2437,
                "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
                "severity": "high",
                "hazards": ["flood", "high_waves"],
                "source": "citizen_report"
            },
            {
                "id": "mock_2",
                "description": "Storm surge warning issued for Beach Town. Expect waves up to 8 feet.",
                "location": "Beach Town",
                "latitude": 36.7783,
                "longitude": -119.4179,
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "severity": "medium",
                "hazards": ["storm_surge"],
                "source": "official_alert"
            },
            {
                "id": "mock_3",
                "description": "High waves observed at Seaside Village. Caution advised for swimmers.",
                "location": "Seaside Village",
                "latitude": 38.8951,
                "longitude": -77.0364,
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "severity": "low",
                "hazards": ["high_waves"],
                "source": "lifeguard_report"
            },
            {
                "id": "mock_4",
                "description": "Coastal erosion worsening at Point Break. Several feet of beach lost this season.",
                "location": "Point Break",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "severity": "medium",
                "hazards": ["erosion"],
                "source": "environmental_agency"
            },
            {
                "id": "mock_5",
                "description": "Tropical storm approaching the gulf coast. Evacuation orders in effect for low-lying areas.",
                "location": "Gulf Coast City",
                "latitude": 29.7604,
                "longitude": -95.3698,
                "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
                "severity": "high",
                "hazards": ["coastal_storm", "flood"],
                "source": "national_weather_service"
            }
        ]
        
        self.current_hazards = mock_data
        self.hazard_history.extend(mock_data)
        
        # Keep history to a reasonable size
        if len(self.hazard_history) > 1000:
            self.hazard_history = self.hazard_history[-1000:]
    
    def _prepare_data_for_dashboard(self):
        """Prepare data for dashboard consumption"""
        result = []
        
        for hazard in self.current_hazards:
            # Extract the original data if available
            original_data = hazard.get("original_data", hazard)
            
            # Create a simplified representation for the dashboard
            dashboard_item = {
                "id": original_data.get("id", str(hash(str(hazard)))),
                "description": original_data.get("description", original_data.get("text", original_data.get("title", ""))),
                "location": original_data.get("location", ""),
                "latitude": original_data.get("latitude"),
                "longitude": original_data.get("longitude"),
                "timestamp": original_data.get("timestamp", datetime.now().isoformat()),
                "severity": hazard.get("severity", "unknown"),
                "hazards": hazard.get("hazards", []),
                "source": original_data.get("source", "unknown"),
                "confidence": hazard.get("confidence", 0.0)
            }
            
            result.append(dashboard_item)
        
        return result
    
    def start(self, host='127.0.0.1', port=8050, debug=False):
        """Start the dashboard server
        
        Args:
            host: Host address (default: '127.0.0.1')
            port: Port number (default: 8050)
            debug: Enable debug mode (default: False)
        """
        # Start data refresh thread
        self.running = True
        self.refresh_thread = threading.Thread(target=self._data_refresh_loop)
        self.refresh_thread.daemon = True
        self.refresh_thread.start()
        
        # Collect initial data
        self.collect_and_analyze_data()
        
        # Run the dashboard server
        logger.info(f"Starting Ocean Hazard Monitoring Dashboard on http://{host}:{port}")
        self.app.run_server(host=host, port=port, debug=debug)
    
    def stop(self):
        """Stop the dashboard server and data refresh thread"""
        self.running = False
        if self.refresh_thread and self.refresh_thread.is_alive():
            self.refresh_thread.join(timeout=5.0)
        logger.info("Ocean Hazard Monitoring Dashboard stopped")
    
    def _data_refresh_loop(self):
        """Background loop for refreshing data"""
        while self.running:
            try:
                self.collect_and_analyze_data()
                time.sleep(self.refresh_interval)
            except Exception as e:
                logger.error(f"Error in data refresh loop: {str(e)}")
                time.sleep(min(self.refresh_interval, 10))  # Sleep briefly before retrying

# Example usage
if __name__ == "__main__":
    # Create and start the dashboard with mock data
    dashboard = OceanHazardDashboard(refresh_interval=30)
    dashboard.start(debug=True)