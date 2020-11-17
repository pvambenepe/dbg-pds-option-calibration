# dbg-pds-option-calibration
Shows how to calibrate a simple parametric volatility surface using intraday data made public by Deutsche Boerse


# Context

In order to use machine learning techniques, you first need to gather large scale, clean and stationary data.
Few open source AI projects tackle options market precisely for lack of data and the difficulty of putting together all stages of data transformation from raw intraday prices to refined parameters time series.

Data used here have been made public by Deutsche Boerse as part of their PDS initative : https://github.com/Deutsche-Boerse/dbg-pds

To retreive these raw data, I have used bits of code from another git that you can find here : https://github.com/Originate/dbg-pds-tensorflow-demo

My code, written in Python, shows how to calibrate a volatility surface using only trade data sampled with 1 minute intervals.

This code works for liquid underlings like the Eurostoxx50 index but also for less liquid single stock options.


# Chosen technics

I decided to clusterize consecutive trades by groups containing at least 5 traded calls and 5 traded puts.

The idea here is to be able to first perform a calibration of the forward-to-spot ratio prior to the calibration of volatility parameters. This will prevent any miscalibration resulting from a sudden change of this ratio following either a dividend payment or a change in the dividend forecast.

For that, we will perform a WLS (weighted OLS) to determine which forward-to-spot ratio fits best the n trades in the cluster.
The weights are used to balance the positive and negative delta (call and puts) in the cluster.

With one row per trade in the cluster so :

X = 
sensi_delta_opt1

sensi_delta_opt2

sensi_delta_opt3

...

Y = 

Traded_price_opt1 - Model_price_opt1_with_param(t-1)

Traded_price_opt2 - Model_price_opt2_with_param(t-1)

Traded_price_opt3 - Model_price_opt3_with_param(t-1)

...

the result of the regression gives the shift to be applied to the forward-to-spot ratio (cf code get_new_fwd_ratio in the Fitting class)


Once this is done, we want to see how to alter volatility parameters in order to best fit the traded prices of the cluster. We will be starting by pricing the trades with the parameters of the previous cluster along with the associated sensitivities (sensi_vega, sensi_smile...). 
We will then be using an Elastic Net Regression rather than OLS in order to give more rigidity to parameters with less variability like smile and convexity 
Each row corresponds to a trade in the cluster so :

X = 
sensi_vega_opt1 * std_vega,  sensi_smile_opt1 * std smile,  sensi_convex_opt1 * std_convex

sensi_vega_opt2 * std_vega,  sensi_smile_opt2 * std smile,  sensi_convex_opt2 * std_convex

sensi_vega_opt3 * std_vega,  sensi_smile_opt3 * std smile,  sensi_convex_opt3 * std_convex

...

Y = 
Traded_price_opt1 - Model_price_opt1_with_param(t-1)

Traded_price_opt2 - Model_price_opt2_with_param(t-1)

Traded_price_opt3 - Model_price_opt3_with_param(t-1)

...

We look for a vector alpha which minimizes: ||Y-X * alpha||2 + epsilon1*||alpha||1 + epsilon2*||alpha||2   (see elastic net regression)
The result gives the move to apply to parameters :

ATF(t) = ATF(t-1) + alpha[0]*std_vega

SMI(t) = SMI(t-1) + alpha[1]*std_smile

CVX(t) = CVX(t-1) + alpha[2]*std_cvx

(cf code get_new_vols_params in the Fitting class)


# Simplifying choices

Each underlying and maturity are treated separatly.

Every trade is priced only once along with options sensitivity on spot and volatility parameters. This pricing uses paramters obtained with the preceding cluster. First order extrapolation along Spot, ATF, SMI and CVX sensitivities is used thereafter for the calibration of the cluster.

The pricers used are a european Black and Scholes pricer with continuous dividend yield and a binomial tree for american options also with a continuous dividend yield for american options above a certain threshold of dividenyield (we use the european closed formula pricer under this threshold for speed purposes). 
Even when using a binomial tree, the pricing of american options is unprecise due to the lack of data regarding the exact dividend ex-date. In order to prevent too big an impact from that, we filter out calls with a delta over X%.

The volatility model is a simple 2nd degree polynamial equation on moneyness.
Sigma(K, T) = ATF(T) - SMI(T) * moneyness +  CVX(T) * moneyness²
with moneyness = ln(K/F)
K = Strike
F = Forward


# Output

The output of this code is pandas dataframes giving time series of the following calibrated parameters : ATF, SMI, CVX, divyield along with traded volumes.
Graphs of these output are given in the Output folder.


# Usage

My goal is to use this output to detect events of asymmetrical information in stock options market.

Asymmetrical information can stem from criminal behaviours like insider trading but also from an edge given by advanced research to actors deploying extensive means like the use of mobile phone data, private polls or other types of intelligence gathering along with machine learning treatment of those data.
The development of those techniques risks undermining the business model of less specialized actors, including market makers, thus jeopardizing the structure of the market.

Asymmetrical information can be detected because they will ultimately lead to a dramatic shift of a parameter such as the spot price, the volatility or the dividend yield.

The goal here is to identify signals in the trading pattern that will alert liquidity providers that something is fishy.
The Machine Learning code used to achieve that will be made public in a separate git at a later date.

