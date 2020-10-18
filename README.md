# dbg-pds-option-calibration
Shows how to calibrate a simple parametric volatility surface using intraday data made public by Deutsche Boerse


# Context

Using machine learning technics is always conditional to having large scale, clean and preferably stationary data.
Few open source AI projects tackle options market precisely for the lack of data and the difficulty of putting together all stages of data transformation from raw intraday prices to refined parameters time series.

Data are here made public by Deutsche Boerse as part of their PDS initative (https://github.com/Deutsche-Boerse/dbg-pds).
(Important : these data are under a Non-Commercial license)

For the retreiving of these data, I have used a demo git that you can find here : https://github.com/Originate/dbg-pds-tensorflow-demo

My code written in Python shows how to calibrate a volatility surface using trade only data sampled with 1 minute intervals.

This code works for liquid underlings like the Eurostoxx50 index but also for much less liquid single stock options.


# Chosen technics

I decided to clusterize consecutive trades (or trades by on the same instrument executed in the same minute) by groups containing at least 5 calls and 5 puts.

The idea here is to be able to start each calibration with a calibration of the forward to spot ratio. This will prevent any wide miscalibration resulting from a sudden change of this ration following either a dividend payment or a change in the dividend forecast.

Hence, the first operation will consist in permforming a WLS mono-regression to determine which forward to spot ratio fits best the n trades in the cluster.
The weights are used to balance the positive and negative delta (call and puts) in the cluster.

Once this is done, the we want to see how to alter volatility parameters in order to best fit the trade prices of the new cluster starting with the parameters of the previous one. This is done by using Elastic Net regression in order to give more rigidity to parameters with less variability like smile and convexity.


# Simplicifation choices

Each underlying and maturity are treated separatly.

Every trade is priced once only once along with options sensitivity on spot and volatility parameters. This price iuses paramters obtaines with the preceding cluster. First order extrapolation is used thereafter for the calibration of the cluster.

The pricer is a european black and Scholes very naive pricer. In order to prevent too big an impact from the fact that single stock options are mainly american ones, we filter out calls with a delta under 50% (and puts with delta over -70% in order to keep only vol relevant options).

The volatility model is a simple polynamial fit a degree 2.
Sigma(K, T) = ATF(T) - SMI(T) * moneyness +  CVX(T) * moneyness²
with moneyness = ln(K/F)
K = Strike
F = Forward

