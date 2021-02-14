import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import fix_yahoo_finance as yf
import matplotlib.animation as animation
import CapitalGainCalculator as CapitalGainCalculator
from decimal import Decimal
import math 

#the first plot is the actual close price with long/short positions
fig=plt.figure()
ax=fig.add_subplot(111)
securities = {}
symbols = ['RELIANCE.NS']
funds = 50000

def main():
    security = CapitalGainCalculator.Security(symbols[0], '')
    
    init(security)
    #(df).to_csv('1.csv')
    #ani = animation.FuncAnimation(fig, animate, init_func=init, interval=5000)
    plt.show()

def init(security):
    print(security)
    stdate='2021-01-06'
    eddate='2021-02-12'
    
    ticker=(security.sym) 
    #df=yf.download(tickers=ticker, start=stdate, end=eddate)
    df=yf.download(tickers=ticker, period='45d', interval='5m')

    lowVolumePricePickupMarker = lowVolumePricePickup(df, -1).to_frame()
    lowPriceVolumePickupMarker = lowPriceVolumePickup(df, -1).to_frame()

    lowVolumePricePickupMarker = lowVolumePricePickupMarker.where((lowVolumePricePickupMarker.applymap(type) != bool), lowVolumePricePickupMarker.replace({True: 'Sell', False: ''}))
    lowPriceVolumePickupMarker = lowPriceVolumePickupMarker.where((lowPriceVolumePickupMarker.applymap(type) != bool), lowPriceVolumePickupMarker.replace({True: 'Buy', False: ''}))
    
    conDive = volumeConverganceDiverganceCalculator(df)
    advice = lowPriceVolumePickupMarker.merge(lowVolumePricePickupMarker, how='inner', left_index=True, right_index=True)
    df = df.merge(advice, how='outer', left_index=True, right_index=True)
    df = df.merge(conDive, how='outer', left_index=True, right_index=True)

    df.to_csv('1.csv')
    bought = 0
    
    quantity = math.floor(funds /  df["Close"].max())
    for index, row in df.iterrows():
        availableFunds = funds - (math.ceil(row['Close'])*quantity)
        if(row['0_x']=='Buy' and availableFunds > 0):
            security.add_tran(CapitalGainCalculator.Security.Transaction(index, row['0_x'], quantity, math.ceil(row['Close']), '20'))
            bought = bought + quantity
            funds = funds - (math.ceil(row['Close'])*quantity)
        elif(row['0_y']=='Sell' and bought > 0):
            security.add_tran(CapitalGainCalculator.Security.Transaction(index, row['0_y'], bought, math.ceil(row['Close']), '20'))
            bought = 0
            funds = funds + (math.ceil(row['Close'])*quantity)
    if(bought>0):
        row = df.tail(1)
        print(row)
        security.add_tran(CapitalGainCalculator.Security.Transaction(index, 'Sell', bought, math.ceil(row['Close']), '20'))
    print(CapitalGainCalculator.calculate(security))
    
    new = df
    new['Close'].plot(label=ticker)
    ax.plot(new.loc[new['0_x']=='Buy'].index,new['Close'][new['0_x']=='Buy'],label='LONG',lw=0,marker='^',c='green')
    ax.plot(new.loc[new['0_y']=='Sell'].index,new['Close'][new['0_y']=='Sell'],label='SHORT',lw=0,marker='v',c='red')
    # ax.plot(new.loc[new['0_x_y']=='Buy'].index,new['Close'][new['0_x_y']=='Buy'],label='LONG',lw=0,marker='^',c='brown')
    #ax.plot(new.loc[new['0_y_y']=='Sell'].index,new['Close'][new['0_y_y']=='Sell'],label='SHORT',lw=0,marker='v',c='orange')

    plt.legend(loc='best')
    plt.grid(True)
    plt.title('Positions')
    

def Average(lst): 
    return sum(lst) / len(lst) 

def lowVolumePricePickup(df, row):
     #df['match'] = df['Volume'] < df['Volume'].shift() and df['Close'] > df['Close'].shift()
     diff = df.diff(row)
     return ((diff['Volume'] < 0) &  (diff['Close']>0))
     

def lowPriceVolumePickup(df, row):
     #df['match'] = df['Volume'] < df['Volume'].shift() and df['Close'] > df['Close'].shift()
     diff = df.diff(row)
     return ((diff['Volume'] > 0) &  (diff['Close'] < 0))



def volumeConverganceDiverganceCalculator(df):
    avgVol = Average(df['Volume'])
    avgPrice = Average(df['Adj Close'])
    print("Average Volumn - ", avgVol, " Average Price ", avgPrice)
    volAvgVsActual = {}
    for index, row in df.iterrows():
        volDev = ((row.values[len(row.values)-1]-avgVol)*100)/avgVol
        priceDev = ((row.values[len(row.values)-2]-avgPrice)*100)/avgPrice
        buyOrSell = (volDev + priceDev )
        volAvgVsActual[index] = [avgVol,volDev,avgPrice,priceDev,buyOrSell]
    convDf =  (pd.DataFrame.from_dict(volAvgVsActual, orient='index', columns=['avgVol', 'volumeDeviation', 'avgPrice', 'priceDeviation', 'conDiv']))
    
        
    
    return convDf

if __name__ == '__main__':
    main()