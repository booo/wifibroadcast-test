import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from glob import glob
import os
import re

worktime = 4 #[sek]
rxAdapterCount = 2


def getTestIdFromFilename(filename):
    return  int(re.findall(r'\d+', filename)[0])

#read test descriptions
df_tests = pd.read_csv("/home/julle/projects/SearchWing/Tests/20201119_WifiTestSetup/wifibroadcast-test/testids.csv")
df_tests['testid'] = pd.to_numeric(df_tests['testid'])
for i, row in df_tests.iterrows():
    df_tests.at[i,'testdescr'] = "mcs"+ str(row['mcs'])+ " " + "fec_r"+str(row['FEC_r'])+ " " +str(row['bandwidth'])


#path to test results
path="/home/julle/projects/SearchWing/Tests/20201119_WifiTestSetup/wfb-test-results/dummyTest"
testPositions = glob(path+"/*/")
testPositionsDirNames = [os.path.basename(os.path.normpath(path)) for path in testPositions]


#containers
##csv
df_results = {k: None for k in range(rxAdapterCount)}
maxValuesOneAdapter = {k: [] for k in range(rxAdapterCount)}
##data
testIds = []
sizesBits = []
testPositionsList = []


#read in raw result data
for idx,oneTestPosPath in enumerate(testPositions):
    #  csvs
    csvs = sorted(glob(os.path.join(oneTestPosPath,"*.csv")))
    for oneCsv in csvs:
        df_debug = pd.read_csv(oneCsv)  
        filename = os.path.basename(oneCsv)
        testId = getTestIdFromFilename(filename)

        for oneAdapterIdx in range(rxAdapterCount):
            df_copy = df_debug.copy()
            df_copy = df_copy[df_copy.adapterIdx==oneAdapterIdx]

            test_start_idx = df_copy[df_copy.received_block_cnt == 0].index[-1]
            df_copy = df_copy.loc[test_start_idx:,:]
            test_end_idx = df_copy[df_copy.received_block_cnt == np.max(df_copy.received_block_cnt.values)].index[0]
            df_copy = df_copy.loc[:test_end_idx,:]

            df_copyT = pd.DataFrame(df_copy.max()).transpose()
            df_copyT = df_copyT.drop('stamp', 1)
            df_copyT['mean_signal_dbm'] = np.mean(df_copy['current_signal_dbm'])
            df_copyT['testid'] = testId
            df_copyT['testPosition'] = testPositionsDirNames[idx]

            maxValuesOneAdapter[oneAdapterIdx].append(df_copyT)

    # data files
    nettoDataFiles = glob(os.path.join(oneTestPosPath,"*.data"))
    for oneNettoDataFile in nettoDataFiles:
        filename = os.path.basename(oneNettoDataFile)
        testIds.append(getTestIdFromFilename(filename))
        bitpersec = ((os.path.getsize(oneNettoDataFile)*8)/worktime)/1E6 # convert to Mbit/s
        sizesBits.append(bitpersec) 
        testPositionsList.append(testPositionsDirNames[idx])


#create results df
##csv
for oneAdapterIdx in range(rxAdapterCount):
    df_maxValuesOneAdapter = pd.concat( maxValuesOneAdapter[oneAdapterIdx])
    df_results[oneAdapterIdx] = pd.merge(df_tests.copy(), df_maxValuesOneAdapter,  how='left', on='testid')
##data files
df_nettoDataSize = pd.DataFrame(data={'testid':testIds, 'testPosition': testPositionsList, 'DataRateNetto' : sizesBits})
df_resultsNettoDataSize = pd.merge(df_tests.copy(), df_nettoDataSize,  how='left', on='testid')


#plot
plt_width=15
plt_height=5
##datafiles
allTestPositons={testPositionsDirName : df_resultsNettoDataSize[df_resultsNettoDataSize.testPosition == testPositionsDirName].DataRateNetto.values for testPositionsDirName in testPositionsDirNames}
df = pd.DataFrame(allTestPositons, index=df_tests['testdescr'])
yticks = [1 * i for i in range(20)]
ax = df.plot.bar(rot=90,grid=True, figsize=(plt_width,plt_height), yticks=yticks, title="DataRateNetto Mbit/s")

##csv
def plot_specific(df, colName):
    allTestPositons={testPositionsDirName : df[df.testPosition == testPositionsDirName][colName].values for testPositionsDirName in testPositionsDirNames}
    df_vis = pd.DataFrame(allTestPositons, index=df_tests['testdescr'])
    ax = df_vis.plot.bar(rot=90, grid=True, figsize=(plt_width,plt_height), title=colName)
    plt.subplots_adjust(hspace=0.5) 


plot_specific(df_results[0],"mean_signal_dbm")
plt.show()
