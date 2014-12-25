# coding: utf-8

import cherrypy
import json
import argparse

from jinja2 import Template
import numpy as np
import pandas as pd


N_rows = 6000000  # 6M rows

hops_list = ["tpf0q01", "tpf0q02", "tpf0q03", "tpf0q04", "tpf0q05", "tpf0q06"]
hops_sigm = [      140,       280,        40,        40,       390,        10]
hops_mean = [      600,       700,      1100,       800,       900,       500]
N_per_series = N_rows/len(hops_list)
timerange = pd.date_range('20141203', periods=N_per_series, freq='10000U')

all_series = {}
for name, sigma, mean in zip(hops_list, hops_sigm, hops_mean):
        # Generate time series for hop
        linser = np.linspace(0.0001, 0.000001*N_per_series, num=N_per_series)
        sinser = np.sin(linser) * 200.0
        series = np.random.normal(mean, sigma, N_per_series)
        all_series[name] = series + sinser

quantiles = [0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
s = pd.Series(all_series["tpf0q01"], index=timerange)

description = s.describe()
single_series_desc = list(description.iteritems())

resampled_s = s.resample('10S')
single_series_plot = list(resampled_s.iteritems())


df = pd.DataFrame(all_series, index=timerange)
df_desc = df.describe()

dataset_desc = []
for name, series in df_desc.iterrows():
    row = [name]
    row += [val for _, val in series.iteritems()]
    dataset_desc.append(tuple(row))
dataset_columns = [col for col in df_desc.columns]

resampled_df = df.resample('min')

n_bins = 100

single_series_hist = []
hist = np.histogram(s, bins=n_bins)
prev = 0
for ix in range(0, n_bins):
    count = hist[0][ix]
    value = hist[1][ix]
    single_series_hist.append((prev, count))
    single_series_hist.append((value, count))
    prev = value

host = None

# Try to open config file and read it
places = [
    '/etc/latency-proto.conf',
    '/usr/share/latency-proto.conf',
]

for place in places:
    try:
        with open(place, 'r') as f:
            config = json.load(f)
            host = config['host']
        break
    except:
        # retry in different place
        pass

if not host:
    print "Host is not specified"
    exit()


class DataServer:
    """Data server mock, generates some BS data for you."""
    def __init__(self):
        with open("index.html", 'r') as template_file:
            self.__template = Template(template_file.read())
    
    @cherrypy.expose
    def data(self):
        result = self.__template.render(single_series_plot=single_series_plot,
                                        description=description,
                                        single_series_hist=single_series_hist,
                                        host=host
                                        )
        return result

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def data_api(self, chart='plot', **kwargs):
        if chart == 'plot':
            return single_series_plot
        elif chart == 'hist':
            return single_series_hist


cherrypy.config.update({'server.socket_port': 80, 'server.socket_host': '0.0.0.0'}) 
cherrypy.quickstart(DataServer())
