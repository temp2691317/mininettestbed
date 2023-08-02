import pandas as pd
import matplotlib.pyplot as plt
import scienceplots
plt.style.use('science')
import json
import os
import matplotlib as mpl
pd.set_option('display.max_rows', None)
import numpy as np
from matplotlib.pyplot import figure

ROOT_PATH = "/Volumes/LaCie/mininettestbed/nooffload/results_responsiveness_bw_rtt/fifo"
PROTOCOLS = ['cubic', 'orca', 'aurora']
BW = 50
DELAY = 50
QMULT = 1
RUNS = list(range(1,51))
LOSSES=[0]
BDP_IN_BYTES = int(BW * (2 ** 20) * 2 * DELAY * (10 ** -3) / 8)
BDP_IN_PKTS = BDP_IN_BYTES / 1500
start_time = 0
end_time = 300


# List containing each data point (each run). Values for each datapoint: protocol, run_number, average_goodput, optimal_goodput
data = []

for protocol in PROTOCOLS:
    optimals = []
    for run in RUNS:
        PATH = ROOT_PATH + '/Dumbell_%smbit_%sms_%spkts_0loss_1flows_22tcpbuf_%s/run%s' % (BW, DELAY, int(QMULT * BDP_IN_PKTS), protocol, run)
        # Compute the average optimal throughput
        with open(PATH + '/emulation_info.json', 'r') as fin:
            emulation_info = json.load(fin)

        bw_capacities = list(filter(lambda elem: elem[5] == 'tbf', emulation_info['flows']))
        bw_capacities = [x[-1][1] for x in bw_capacities]
        optimal_mean = sum(bw_capacities)/len(bw_capacities)

        if protocol != 'aurora':
            print(protocol)
            print(run)
            if os.path.exists(PATH + '/sysstat/etcp_c1.log'):
                systat1 = pd.read_csv(PATH + '/sysstat/etcp_c1.log', sep=';').rename(
                    columns={"# hostname": "hostname"})

                retr1 = systat1[['timestamp', 'retrans/s']]
                start_timestamp = retr1['timestamp'].iloc[0]



                retr1['timestamp'] = retr1['timestamp'] - start_timestamp + 1

                retr1 = retr1.rename(columns={'timestamp': 'time'})
                valid = True

            else:
                valid = False
        else:
            if os.path.exists(PATH + '/csvs/c1.csv'):
                systat1 = pd.read_csv(PATH + '/csvs/c1.csv').rename(
                    columns={"retr": "retrans/s"})
                retr1 = systat1[['time', 'retrans/s']]
                valid = True
            else:
                valid = False

        if valid:
            retr1['time'] = retr1['time'].apply(lambda x: int(float(x)))

            retr1 = retr1.drop_duplicates('time')

            retr1_total = retr1[(retr1['time'] > start_time) & (retr1['time'] < end_time)]
            retr1_total = retr1_total.set_index('time')
            data.append([protocol, run, retr1_total.mean()['retrans/s']*1500*8/(1024*1024)])

COLUMNS = ['protocol', 'run_number', 'average_retr_rate']
data_df = pd.DataFrame(data, columns=COLUMNS)
BINS = 50
figure(figsize=(3, 1.5), dpi=720)

fig, axes = plt.subplots(nrows=1, ncols=1,figsize=(3,1.5))
ax = axes

for protocol in PROTOCOLS:
    avg_goodputs = data_df[data_df['protocol'] == protocol]['average_retr_rate']
    values, base = np.histogram(avg_goodputs, bins=BINS)
    # evaluate the cumulative
    cumulative = np.cumsum(values)
    # plot the cumulative function
    ax.plot(base[:-1], cumulative/50*100, label=protocol)

ax.set(xlabel="Average Retr. Rate (Mbps)", ylabel="Percentage of Trials (\%)")
fig.legend(ncol=2, loc='upper center',bbox_to_anchor=(0.5, 1.17),columnspacing=1,handletextpad=1)
fig.savefig("retr_cdf.png", dpi=720)