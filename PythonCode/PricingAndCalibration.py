from SetUp import *


class Pricing():
    def __init__(self):
        self.indexlist = ['SX5E']
        time_fmt = "%H:%M"
        self.opening_hours = datetime.datetime.strptime(opening_hours_str, time_fmt).time()
        self.closing_hours = datetime.datetime.strptime(closing_hours_str, time_fmt).time()

        from_date = '2017-01-01'
        last_matu = '2022-12-31'
        dates_expi = list(pd.date_range(from_date, last_matu, freq='W'))
        dates_expi = [elt - datetime.timedelta(2) for elt in dates_expi]
        self.dates_expi = [datetime.datetime.combine(elt, self.closing_hours) for elt in dates_expi if
                           elt.day in [15, 16, 17, 18, 19, 20, 21]]
        # dates_expi_trim = [elt for elt in dates_expi if elt.month in [3, 6, 9, 12]]

        self.smile_sliding_coef = 1

    def euro_vanilla_pricer(self, S, K, T, r, repo, sigma, type):
        sigma = sigma / 100
        d1 = (np.log(S / K) + (r - repo + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = (np.log(S / K) + (r - repo - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        if type == 'Call':
            return (S * np.exp(-repo * T) * si.norm.cdf(d1, 0.0, 1.0) - K * np.exp(-r * T) * si.norm.cdf(d2, 0.0, 1.0))
        else:
            return (K * np.exp(-r * T) * si.norm.cdf(-d2, 0.0, 1.0) - S * np.exp(-repo * T) * si.norm.cdf(-d1, 0.0,
                                                                                                          1.0))

    def american_vanilla_pricer(self, S, K, r, repo, sigma, T, N=1000):
        sigma = sigma / 100
        # credit to http://gosmej1977.blogspot.com/2013/02/american-options.html
        # calculate delta T
        deltaT = float(T) / N

        # up and down factor will be constant for the tree so we calculate outside the loop
        u = np.exp(sigma * np.sqrt(deltaT))
        d = 1.0 / u

        # to work with vector we need to init the arrays using numpy
        fs = np.asarray([0.0 for i in range(N + 1)])

        # we need the stock tree for calculations of expiration values
        fs2 = np.asarray([(S * u ** j * d ** (N - j)) for j in range(N + 1)])

        # we vectorize the strikes as well so the expiration check will be faster
        fs3 = np.asarray([float(K) for i in range(N + 1)])

        # rates are fixed so the probability of up and down are fixed.
        # this is used to make sure the drift is the risk free rate
        a = np.exp((r - repo) * deltaT)
        p = (a - d) / (u - d)

        # Compute the leaves, f_{N, j}
        fs[:] = np.maximum(fs2 - fs3, 0.0)

        # calculate backward the option prices
        for i in range(N - 1, -1, -1):
            fs[:-1] = np.exp(-r * deltaT) * (p * fs[1:] + (1 - p) * fs[:-1])
            fs2[:] = fs2[:] * u

            # Simply check if the option is worth more alive or dead
            fs[:] = np.maximum(fs[:], fs2[:] - fs3[:])

        # print fs
        return fs[0]

    def vanilla_pricer(self, S, K, T, r, sigma, fwdRatio, type):
        indic = (1 - fwdRatio) / max(1 / 12, T) ** 0.5
        # not taking moneyness into account because all calls must have same method + only OTM calls anyway
        repo = - math.log(fwdRatio) / max(1 / 250, T)
        if (type == "Call") and (indic > 0.02) and (self.udl not in self.indexlist):
            return (self.american_vanilla_pricer(S, K, r, repo, sigma, T))
        else:
            return (self.euro_vanilla_pricer(S, K, T, r, repo, sigma, type))

    def get_vol_and_sensi(self, spot, RefSpot, strike, TTM, ATF, SMI, CVX, FwdRatio, sensi):
        # first pivot
        ATFnew = ATF - math.log(spot * FwdRatio / RefSpot) * SMI * self.smile_sliding_coef / (max(1.0 / 24, TTM)) ** 0.5
        # then get vol
        moneyness = math.log(strike / spot * FwdRatio)
        vol = ATFnew - moneyness * 10 * SMI / max(1.0 / 24, TTM) ** 0.5 + moneyness ** 2 * CVX / max(1.0 / 24, TTM)
        if sensi:
            delta = self.get_vol_and_sensi(spot * 1.01, RefSpot, strike, TTM, ATF, SMI, CVX, FwdRatio, False) - vol
            sensiATF = self.get_vol_and_sensi(spot, RefSpot, strike, TTM, ATF + 0.01, SMI, CVX, FwdRatio, False) - vol
            sensiSMI = self.get_vol_and_sensi(spot, RefSpot, strike, TTM, ATF, SMI + 0.01, CVX, FwdRatio, False) - vol
            sensiCVX = self.get_vol_and_sensi(spot, RefSpot, strike, TTM, ATF, SMI, CVX + 0.01, FwdRatio, False) - vol
            return (vol, delta, sensiATF, sensiSMI, sensiCVX)
        else:
            return vol


class Fitting(Pricing):

    def __init__(self, inputfolder, udl, MaturityDate):
        super(Fitting, self).__init__()
        self.udl = udl
        self.df = pd.read_pickle(inputfolder + '/Execs_' + udl + '.pkl')

        # filter Maturity
        self.MaturityDate = MaturityDate
        self.df = self.df.loc[self.df.MaturityDate == pd.Timestamp(MaturityDate.date())]
        self.df['MaturityDate'] = self.df['MaturityDate'].apply(
            lambda x: datetime.datetime.combine(x.date(), self.closing_hours))
        if self.df.shape[0] < 50:
            self.bigEnough = False
        else:
            # we need a unique index so the timestamp cannot do
            self.df['timeOfTrade'] = self.df.index.tolist()
            self.df = self.df.reset_index(drop=True)

            for coef in ['RefSpot', 'ATF', 'SMI', 'CVX', 'FwdRatio', 'ModelPrice', 'ModelPrice2', 'ModelPrice3',
                         'sensiDelta', 'sensiATF', 'sensiSMI', 'sensiCVX', 'OTM', 'iv']:
                self.df[coef] = np.nan

            self.min_nb_opt_per_cluster = 5

            self.ATF = 25
            self.SMI = 1.5
            self.CVX = 20
            self.TTM = 0
            self.FwdRatio = 1
            self.RefSpot = self.df.PriceU[0]

            self.stdParams = np.array([0.5, 0.1, 0.3])  # standard dev

            # filter out if error (meaning half spread between max and min over 1 minute) is too large in retrieved data
            # print(self.df.shape)
            # print('filter out if error is too large')
            self.df = self.df.loc[self.df.ErrorU < 15]  # 15bps for stocks
            self.df = self.df.loc[self.df.ErrorO < 5]  # 5bps for options
            # print(self.df.shape)

            self.start_index = self.df.index[0]

            # create dataframe with params
            self.df_params = pd.DataFrame(
                columns=['ExpiDate', 'StartIndex', 'StartTime', 'Interval', 'RefSpot', 'ATF', 'SMI', 'CVX', 'FwdRatio',
                         'TTM', 'Error'])
            self.bigEnough = True

    def clusterize(self):
        nb_calls = 0
        nb_puts = 0
        self.cluster = pd.DataFrame()

        iter = self.df.loc[self.start_index:].iterrows()
        for pos, row in iter:
            if row.PutOrCall == 'Call':
                nb_calls += 1
            else:
                nb_puts += 1

            if (nb_calls >= self.min_nb_opt_per_cluster) and (nb_puts >= self.min_nb_opt_per_cluster):
                # print(pos)
                self.last_index = pos
                try:
                    self.end_index, value = next(iter)
                except:
                    self.end_index = pos + 1
                self.cluster = self.df[self.start_index:self.end_index].copy()
                break

    def reref(self):
        newrefspot = self.cluster.PriceU.mean() * self.FwdRatio
        newTTM = self.cluster.TTM.mean()

        self.ATF = self.ATF - math.log(newrefspot / self.RefSpot) * self.SMI * self.smile_sliding_coef / (
            max(1.0 / 24, newTTM)) ** 0.5

        self.RefSpot = newrefspot
        self.TTM = newTTM
        self.cluster['RefSpot'] = self.RefSpot

    def price_cluster(self, udl):
        for pos, row in self.cluster.iterrows():
            vol, delta, sensiATF, sensiSMI, sensiCVX = self.get_vol_and_sensi(row.PriceU, self.RefSpot, row.StrikePrice,
                                                                              row.TTM, self.ATF, self.SMI, self.CVX,
                                                                              self.FwdRatio, True)
            ModelPrice = self.vanilla_pricer(row.PriceU, row.StrikePrice, row.TTM, 0, vol, self.FwdRatio, row.PutOrCall)
            sensidelta = self.vanilla_pricer(row.PriceU * 1.01, row.StrikePrice, row.TTM, 0, vol + delta, self.FwdRatio,
                                             row.PutOrCall) - ModelPrice
            sensivega = self.vanilla_pricer(row.PriceU, row.StrikePrice, row.TTM, 0, vol + 1, self.FwdRatio,
                                            row.PutOrCall) - ModelPrice

            self.cluster.loc[pos, 'ModelPrice'] = ModelPrice
            self.cluster.loc[pos, 'sensiDelta'] = sensidelta
            self.cluster.loc[pos, 'sensiATF'] = sensivega * sensiATF
            self.cluster.loc[pos, 'sensiSMI'] = sensivega * sensiSMI
            self.cluster.loc[pos, 'sensiCVX'] = sensivega * sensiCVX
            self.cluster.loc[pos, 'iv'] = vol

            if udl not in self.indexlist:
                delta_range = [0.5, 0.05, -0.6, -0.05]
                # adjust if we get close to a div
                indic = (1 - self.FwdRatio) / max(1 / 12, row.TTM) ** 0.5
                if indic > 0.02:
                    delta_range = [0.45, 0.05, -0.6, -0.05]
                if indic > 0.06:
                    delta_range = [0.4, 0.05, -0.6, -0.05]
                if indic > 0.1:
                    delta_range = [0.35, 0.05, -0.6, -0.05]
            else:
                delta_range = [0.5, 0.05, -0.5, -0.05]

            dtpct = sensidelta / row.PriceU * 100
            if ((row.PutOrCall == 'Call') and (dtpct < delta_range[0]) and (dtpct > delta_range[1])) or (
                    (row.PutOrCall == 'Put') and (dtpct > delta_range[2]) and (dtpct < delta_range[3])):
                self.cluster.loc[pos, 'OTM'] = True
            else:
                self.cluster.loc[pos, 'OTM'] = False

    def get_new_fwd_ratio(self):

        # filter out ITM options
        # print('filter out ITM options')
        # print(self.cluster.shape)
        self.cluster = self.cluster.loc[self.cluster.OTM == True]
        # self.cluster.loc[self.cluster.OTM == True].shape

        # normalize qty to give same weight to calls and puts
        dfcalls = self.cluster.loc[self.cluster.PutOrCall == 'Call']
        deltacalls = (dfcalls.NumberOfContracts ** 0.5 * dfcalls.sensiDelta).sum()
        checkSizeCalls = (
                    dfcalls.sensiDelta / dfcalls.PriceU * 100).sum()  # sum of all indivual delta (in %) should be at least 30%
        dfputs = self.cluster.loc[self.cluster.PutOrCall == 'Put']
        deltaputs = (dfputs.NumberOfContracts ** 0.5 * dfputs.sensiDelta).sum()
        checkSizePuts = (
                    dfputs.sensiDelta / dfputs.PriceU * 100).sum()  # sum of all indivual delta (in %) should be at least 30%

        # handle rare cases were all calls (resp puts) are ITM
        if (checkSizeCalls < .3) or (checkSizePuts > -.3):
            return False
        else:
            self.cluster['W'] = np.nan
            self.cluster.loc[self.cluster.PutOrCall == 'Call', 'W'] = \
                self.cluster.loc[self.cluster.PutOrCall == 'Call'].NumberOfContracts ** 0.5 / deltacalls
            self.cluster.loc[self.cluster.PutOrCall == 'Put', 'W'] = \
                self.cluster.loc[self.cluster.PutOrCall == 'Put'].NumberOfContracts ** 0.5 / -deltaputs

            # find best FwdRatio adjustment with WLS
            X = np.float64(np.array(self.cluster.sensiDelta))
            Y = np.float64(np.array(self.cluster.PriceO - self.cluster.ModelPrice))
            W = np.float64(np.array(self.cluster.W))

            wls_model = sm.WLS(Y, X, weights=W)
            # wls_model = sm.WLS(Y, X)
            self.results = wls_model.fit()
            newFwdRatio = self.FwdRatio * (1 + self.results.params[0] * 0.01)

            # readjust ModelPrices with this new FwdRatio
            self.cluster['ModelPrice2'] = self.cluster.ModelPrice + self.cluster.sensiDelta * (
                        newFwdRatio - self.FwdRatio) * 100
            self.FwdRatio = newFwdRatio
            self.cluster['FwdRatio'] = newFwdRatio

            return True

    def get_new_vols_params(self):
        # NB : if a cluster mixes pre and post dividend trades, it will be messy. I expect that the error cap
        # mechanism will sort out those cases
        # find best FwdRatio adjustment with WLS
        X = np.float64(np.array(self.cluster[['sensiATF', 'sensiSMI', 'sensiCVX']]) * self.stdParams)
        Y = np.float64(np.array(self.cluster.PriceO - self.cluster.ModelPrice2))
        # W = np.float64(self.cluster.NumberOfContracts)
        # wls_model = sm.WLS(Y, X, weights=W)
        modelOLS = sm.OLS(Y, X)
        results = modelOLS.fit_regularized(method='elastic_net', alpha=0.00000001, L1_wt=0.5)

        # self.var_coefs = results.params * self.stdParams

        self.ATF = self.ATF + results.params[0] * 0.01 * self.stdParams[0]
        self.SMI = self.SMI + results.params[1] * 0.01 * self.stdParams[1]
        self.CVX = self.CVX + results.params[2] * 0.01 * self.stdParams[2]

        self.cluster['ATF'] = self.ATF
        self.cluster['SMI'] = self.SMI
        self.cluster['CVX'] = self.CVX

        self.cluster['ModelPrice3'] = self.cluster.ModelPrice2 + np.array(
            results.params * self.cluster[['sensiATF', 'sensiSMI', 'sensiCVX']] * self.stdParams).sum(axis=1)

    def writedown(self):
        # copy back into df
        self.df.loc[self.cluster.index, :] = self.cluster

        # populate parameter dataframe
        start = self.df.loc[self.start_index, 'timeOfTrade']
        end = self.df.loc[self.last_index, 'timeOfTrade']

        hours = (end - start).seconds / 60 / 60
        if hours > 9:
            interval = (end - start).days + 1 + (24 - hours) / 8.5 * 0.7
        else:
            interval = (end - start).days + hours / 8.5 * 0.7

        # get mean error in bps
        self.error = (((self.cluster.ModelPrice3 - self.cluster.PriceO) ** 2).mean()) ** 0.5 / self.RefSpot * 1000

        self.df_params.loc[self.df_params.shape[0]] = [self.MaturityDate, self.start_index, start, interval,
                                                       self.RefSpot, self.ATF, self.SMI, self.CVX, self.FwdRatio,
                                                       self.TTM, self.error]
        # print(self.df_params.tail(2))

        self.start_index = self.end_index

    def compute_EWMA(self):
        Tau = 0.2  # in day of time for ewma

        self.df_params['Interval'] = (self.df_params['Interval'] + self.df_params['Interval'].shift(
            1)) / 2  # the params are valid for the middle of the period so the time between 2 observation is the avergae of 2 consecutive intervals
        self.df_params['alpha'] = self.df_params.Interval.apply(lambda x: 1 - math.exp(- x / Tau))

        for pos in self.df_params.index.tolist():
            for elt in ['ATF', 'SMI', 'CVX', 'FwdRatio']:
                if pos == 0:
                    self.df_params.loc[pos, 'EWMA_' + elt] = self.df_params.loc[pos, elt]
                else:
                    self.df_params.loc[pos, 'EWMA_' + elt] = self.df_params.loc[pos, 'alpha'] * self.df_params.loc[
                        pos, elt] \
                                                             + (1 - self.df_params.loc[pos, 'alpha']) * \
                                                             self.df_params.loc[pos - 1, 'EWMA_' + elt]
