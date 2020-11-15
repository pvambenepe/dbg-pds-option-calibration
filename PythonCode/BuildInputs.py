from SetUp import *
from PricingAndCalibration import Pricing

class BuildInputs(Pricing):

    def __init__(self, udl, matu):
        super(BuildInputs, self).__init__()

        self.udl = udl
        self.matu = matu
        self.df_params = pd.read_pickle(folder2 + '/Parameters_' + udl + '.pkl')
        self.df_volume = pd.read_pickle(folder1 + '/Execs_' + udl + '.pkl')
        self.df_udl = pd.read_pickle(folder1 + '/UDL_' + udl + '.pkl')
        # self.list_matu = sorted(list(self.df_params['ExpiDate'].unique()))
        self.df_volume = self.df_volume.loc[self.df_volume.MaturityDate == pd.Timestamp(matu.date())]
        self.df_params = self.df_params.loc[self.df_params.ExpiDate == matu]


    def find_middle(self, a, b): #in minutes of open market
        if (a==a) and (b==b):
            ti = self.timeline.index(b) - self.timeline.index(a)
            return self.timeline[self.timeline.index(a) + int(ti/2)]
        else:
            return np.nan


    def even_index(self):
        date_ranges = []
        start = self.df_volume.index.min()
        non_empty_days = sorted(list(self.df_udl.index.unique()))
        for date in list(dict.fromkeys([elt.date() for elt in non_empty_days if ((elt>=start) and (elt<=self.matu))])):
            t1 = datetime.datetime.combine(date, self.opening_hours)
            t2 = datetime.datetime.combine(date, self.closing_hours)
            date_ranges.append(pd.DataFrame({"OrganizedDateTime": pd.date_range(t1, t2, freq='1Min').values}))
        agg = pd.concat(date_ranges, axis=0)
        # agg.index = agg["OrganizedDateTime"].values

        # we center the index of df_params on the middle of the cluster
        self.timeline = agg["OrganizedDateTime"].tolist()
        self.df_params.index = [self.find_middle(a, b) for a, b in zip(self.df_params.StartTime, self.df_params.StartTime.shift(-1))]
        # self.df_params.index = self.df_params.index.map(lambda x: x.round('1min'))
        # self.df_params = self.df_params.iloc[1:, :]

        #we make sure that the index list of params is unique (not 2 calibration in the same minute)
        self.df_params = self.df_params.groupby(self.df_params.index).mean()

        #we reindex
        self.df_params = self.df_params.reindex(agg["OrganizedDateTime"].values)


        features = ['RefSpot', 'EWMA_ATF', 'EWMA_SMI', 'EWMA_CVX', 'EWMA_FwdRatio']
        for f in features:
            self.df_params[f] = self.df_params[f].interpolate(limit=60*8, limit_area='inside') #use 'time' option? + limit says that we won't extraoplate beyond 1 day


    def get_total_sensi(self):

        self.df_volume = pd.merge(self.df_volume, self.df_params, left_index=True, right_index=True, how='left')

        self.df_volume['vi'] = self.df_volume.apply(lambda x: self.get_vol_and_sensi(x.PriceU, x.RefSpot, x.StrikePrice, x.TTM, x.EWMA_ATF, x.EWMA_SMI, x.EWMA_CVX, x.EWMA_FwdRatio, True), axis=1)
        # vol, delta, sensiATF, sensiSMI, sensiCVX = self.get_vol_and_sensi()

        self.df_volume['Price'] = self.df_volume.apply(lambda x: self.vanilla_pricer(x.PriceU, x.StrikePrice, x.TTM, 0, x.vi[0], x.EWMA_FwdRatio, x.PutOrCall), axis=1)

        self.df_volume['TotalSensiATF'] = self.df_volume.apply(
            lambda x: (self.vanilla_pricer(x.PriceU, x.StrikePrice, x.TTM, 0, x.vi[0] + x.vi[2], x.EWMA_FwdRatio,
                                          x.PutOrCall) - x.Price) * x.NumberOfContracts, axis=1)
        self.df_volume['TotalSensiSMI'] = self.df_volume.apply(
            lambda x: (self.vanilla_pricer(x.PriceU, x.StrikePrice, x.TTM, 0, x.vi[0] + x.vi[3], x.EWMA_FwdRatio,
                                          x.PutOrCall) - x.Price) * x.NumberOfContracts, axis=1)
        self.df_volume['TotalSensiFwdRatio'] = self.df_volume.apply(
            lambda x: (self.vanilla_pricer(x.PriceU*1.01, x.StrikePrice, x.TTM, 0, x.vi[0] + x.vi[1], x.EWMA_FwdRatio,
                                          x.PutOrCall) - x.Price) * x.NumberOfContracts, axis=1)


        self.df_volume['NumberOfTrades'] = self.df_volume['NumberOfTrades'].fillna(0)
        self.df_volume = self.df_volume[['TotalSensiATF', 'TotalSensiSMI', 'TotalSensiFwdRatio', 'NumberOfTrades']]
        self.df_volume = self.df_volume.groupby(self.df_volume.index).sum()

        self.df_params = self.df_params[['EWMA_ATF', 'EWMA_SMI', 'EWMA_CVX', 'EWMA_FwdRatio']]
        self.df_params = self.df_params.groupby(self.df_params.index).mean()


    def merge(self):
        self.df = pd.merge(self.df_params, self.df_volume, left_index=True, right_index=True, how='left')
        self.df = pd.merge(self.df, self.df_udl[['PriceU', 'TradedVolume']], left_index=True, right_index=True, how='left')

        self.df['PriceU'] = self.df['PriceU'].interpolate('time') #should take nights into account

        for f in ['TradedVolume', 'TotalSensiATF', 'TotalSensiSMI', 'TotalSensiFwdRatio', 'NumberOfTrades']:
            self.df[f] = self.df[f].fillna(0)

        self.df = self.df.dropna()
        #solve duplicate index:
        self.df = self.df.groupby(self.df.index).mean()

        self.df['MaturityDate'] = self.matu
