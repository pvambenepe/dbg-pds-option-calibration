# dbg-pds-option-calibration
Shows how to calibrate a simple parametric volatility surface using intraday data made public by Deutsche Boerse


# Context

Using machine learning technics is always conditional to having large scale, clean and preferably stationary data.
Few open source AI projects tackle options market precisely for lack of data and the difficulty of putting together all stages of data transformation from raw intraday prices to refined parameters time series.

Data used here have been made public by Deutsche Boerse as part of their PDS initative (https://github.com/Deutsche-Boerse/dbg-pds).

For the retreiving of these data, I have used bits of code from a git that you can find here : https://github.com/Originate/dbg-pds-tensorflow-demo

My code, written in Python, shows how to calibrate a volatility surface using only trade data sampled with 1 minute intervals.

This code works for liquid underlings like the Eurostoxx50 index but also for less liquid single stock options.


# Chosen technics

I decided to clusterize consecutive trades by groups containing at least 5 calls and 5 puts.

The idea here is to be able to start each calibration with a calibration of the forward to spot ratio. This will prevent any wide miscalibration resulting from a sudden change of this ratio following either a dividend payment or a change in the dividend forecast.

Hence, the first operation will consist in permforming a WLS (weighted OLS) mono-regression to determine which forward to spot ratio fits best the n trades in the cluster.
The weights are used to balance the positive and negative delta (call and puts) in the cluster.

Once this is done, the we want to see how to alter volatility parameters in order to best fit the trade prices of the new cluster starting with the parameters of the previous one. This is done by using Elastic Net regression in order to give more rigidity to parameters with less variability like smile and convexity.


# Simplicifation choices

Each underlying and maturity are treated separatly.

Every trade is priced only once along with options sensitivity on spot and volatility parameters. This pricing uses paramters obtained with the preceding cluster. First order extrapolation along Spot, ATF, SMI and CVX sensitivities is used thereafter for the calibration of the cluster.

The pricers used are a european Black and Scholes pricer with continuous dividend yield and a binomial tree for american options also with a continuous dividend yield for american options abovve a certain threshold of dividenyield. 
Even when using a binomial tree, the pricing of american options is unprecise due to the lack of data regarding the exact dividend ex-date. In order to prevent too big an impact from that, we filter out calls with a delta under 50% (and puts with delta over -70% in order to keep only vol relevant options).

The volatility model is a simple polynamial fit a degree 2.
Sigma(K, T) = ATF(T) - SMI(T) * moneyness +  CVX(T) * moneyness²
with moneyness = ln(K/F)
K = Strike
F = Forward


# Output

The output of this code is are pandas dataframes giving time series of the following calibrated parameters : ATF, SMI, CVX, divyield along with traded volumes.


# Exploitation

My goal is to use this output to detect asymmetrical information in stock options market.

Asymmetrical information can stem from criminal behaviours like insider trading but also from an hedge given by advanced research from actors deploying extensive means to get an hedge like the use of mobile phone data, private polls or other types of intelligence gathering along with machine learning treatment of those data.
The development of those technics risks putting at risk the business model of less specialized actors including market makers thus jeopardizing the structure of the market.

Asymmetrical information can be detected because they will ultimately lead to a sudden shift of a parameter like the spot price, the volatility or the dividend yield.

The goal here is to spot signals in the trading pattern that will alert such actor that something is fishy.
The code of the Machine Learning code used to achieve that will be madle public in a separate git at a later date.

