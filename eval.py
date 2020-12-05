import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from glob import glob
import os
import re

worktime = 30 #[sek]
rxAdapterCount = 2

##TODO add nettodata from niceblocks = recBlocks-brokenBlocks      * 8 * mtu
##TODO add good pakets received from = recPak - crcfail
##TODO add ratio goodpkts/allpkts
##TODO add double bar for rec pkts (goodpkts unter allpkts)
##TODO plot noisefloor


def getTestIdFromFilename(filename):
    return  int(re.findall(r'\d+', filename)[0])

#path to test results
path="/home/julle/projects/SearchWing/Tests/20201119_WifiTestSetup/wfb-test-results/20201128_Feld"
testPositions = sorted(glob(path+"/*/"))
testPositionsDirNames = [os.path.basename(os.path.normpath(path)) for path in testPositions]


#read test descriptions
testIdsPath = os.path.join(path,"testids.csv")
df_tests = pd.read_csv(testIdsPath)
df_tests['testid'] = pd.to_numeric(df_tests['testid'])
for i, row in df_tests.iterrows():
    df_tests.at[i,'testdescr'] = "ch"+ str(row['channel'])+ " " + "mcs"+ str(row['mcs'])+ " " + "f_r"+str(row['FEC_r'])+ " " +str(row['bandwidth']) + " " + "s" + str(row['stbc']) + " " + str(row['mtu'])




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

            test_start_idx = df_copy[df_copy.received_block_cnt == np.min(df_copy.received_block_cnt)].index[-1]
            df_copy = df_copy.loc[test_start_idx:,:]
            test_end_idx = df_copy[df_copy.received_block_cnt == np.max(df_copy.received_block_cnt.values)].index[0]
            df_copy = df_copy.loc[:test_end_idx,:]

            df_copyT = pd.DataFrame(df_copy.max()).transpose()
            df_copyT = df_copyT.drop('stamp', 1)
            df_copyT['mean_signal_dbm'] = np.mean(df_copy['current_signal_dbm'])
            df_copyT['testid'] = testId
            df_copyT['testPosition'] = testPositionsDirNames[idx]
            #df_copyT['nettoData'] = (df_copy['received_block_cnt'][-1]-df_copy['damaged_block_cnt'][-1])*df_tests[df_tests["testid"] == testId]

            #damaged_block_cnt


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
plt_name = "wfb DataRateNetto Mbit_s"
allTestPositons={testPositionsDirName : df_resultsNettoDataSize[df_resultsNettoDataSize.testPosition == testPositionsDirName].DataRateNetto.values for testPositionsDirName in testPositionsDirNames}
df = pd.DataFrame(allTestPositons, index=df_tests['testdescr'])
yticks = [0.5 * i for i in range(8)]
ax = df.plot.bar(rot=90,grid=True, figsize=(plt_width,plt_height), yticks=yticks, title=plt_name)
plt.tight_layout()
plt.savefig( os.path.join(path,plt_name+'.png'))

##csv
def plot_specific(df, colName, text):
    plt_name = text + " " +colName
    allTestPositons={testPositionsDirName : df[df.testPosition == testPositionsDirName][colName].values for testPositionsDirName in testPositionsDirNames}
    
    df_vis = pd.DataFrame(allTestPositons, index=df_tests['testdescr'])
    df_vis.plot.bar(rot=90, grid=True, figsize=(plt_width,plt_height), title=plt_name)
    plt.tight_layout()
    plt.savefig( os.path.join(path,plt_name+'.png'))
    

for k in range(rxAdapterCount):
    plot_specific(df_results[k],"mean_signal_dbm", "Ant"+str(k))
    plot_specific(df_results[k],"received_packet_cnt", "Ant"+str(k))
    plot_specific(df_results[k],"wrong_crc_cnt", "Ant"+str(k))
    plot_specific(df_results[k],"lost_packets_cnt", "Ant"+str(k))

plot_specific(df_results[0],"fecs_used_cnt", "wfb")
plot_specific(df_results[0],"received_block_cnt", "wfb")
plot_specific(df_results[0],"damaged_block_cnt", "wfb")
plot_specific(df_results[0],"tx_restart_cnt", "wfb")

#plt.show()
