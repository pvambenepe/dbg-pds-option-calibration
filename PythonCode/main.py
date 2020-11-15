from SetUp import *

##
# from GetRawDataimport GetRawData
# get_raw_data()


##
from PricingAndCalibration import Pricing, Fitting

P = Pricing()

for udl in stocks_list:
    print(udl)
    res = pd.DataFrame()

    for MaturityDate in P.dates_expi:  #[pd.Timestamp('2020-09-18 15:30:00')]:  #  P.dates_expi:
        print(MaturityDate)
        fit = Fitting(folder1, udl, MaturityDate)
        if fit.bigEnough:
            fit.clusterize()

            while (fit.cluster.shape[0] > 0) and (fit.df.loc[fit.last_index, 'timeOfTrade'] < MaturityDate - datetime.timedelta(5)):
                fit.reref()
                fit.price_cluster(udl)
                possible = fit.get_new_fwd_ratio()
                if possible:
                    fit.get_new_vols_params()
                    # fit.visualize()
                    fit.writedown()
                else:
                    fit.start_index = fit.end_index

                # if fit.df.loc[fit.start_index, 'timeOfTrade'] >= pd.Timestamp('2020-06-24 00:30:00'):
                #     print(fit.df.loc[fit.start_index, 'timeOfTrade'])
                fit.clusterize()

            fit.compute_EWMA()
            if res.shape[0] == 0:
                res = fit.df_params.copy()
            else:
                res = res.append(fit.df_params, ignore_index=True)
            print(res.tail(10))

    # Filter out if Error is too big
    before = res.shape[0]
    compare_range = max(30, int(before/100/2))
    res.to_pickle(folder2 + '/Parameters_before_filter_' + udl + '.pkl')
    res = res.sort_values(by='StartTime', ascending=True)
    global_mean = res.Error.mean()
    res['maxE'] = res.Error.rolling(compare_range*2).mean().shift(periods=-compare_range, fill_value=0).apply(lambda x: max(global_mean, x)) * (2 + 3 * res.TTM.apply(lambda x: min(2, x)))
    res = res.loc[res.Error < res.maxE]
    print('Pct rows out ' + str(1 - res.shape[0] / before))
    #take out TTM column
    del res['TTM']

    res.to_pickle(folder2 + '/Parameters_' + udl + '.pkl')



##

from BuildInputs import BuildInputs
print('BuildInputs')
for udl in stocks_list:
    print(udl)
    df = pd.DataFrame()
    for pos, matu in enumerate(P.dates_expi):
        # if matu == pd.Timestamp('2020-06-19 00:00:00'):
        print(matu)
        build = BuildInputs(udl, matu)
        if build.df_params.shape[0] > 10:
            build.even_index()
            build.get_total_sensi()
            build.merge()
            df = df.append(build.df)

    df.to_pickle(folder2 + '/Inputs_' + udl + '.pkl')



##
# from Graph import Graph
# g = Graph('SX5E')
# g.graph_params(2020,9)
# g.graph_inputs(2018=9,'EWMA_CVX')



##
from BuildXY import Data
print('BuildXY')

for udl in stocks_list:
    print(udl)
    data = Data(udl)
    data.differentiate_matu()
    data.df_pivot.to_pickle(folder3 + '/X_' + udl + '.pkl')


ref = 'DAI'
st = 5
lt = 8*20
for udl in stocks_list:
    print(udl)
    data = Data(udl)
    data.df_pivot = pd.read_pickle(folder3 + '/X_' + udl + '.pkl')

    data.differentiate_time(st, lt)

    if udl not in [ref]:
        XRef = pd.read_pickle(folder3 + '/XY_' + ref + '-st ' + str(st) + '-lt ' + str(lt) + '.pkl')
        data.differentiate_refindex(XRef)
        data.filter(1, True)
        data.create_Y('EWMA_FwdRatio', 5) #in hours
        data.normalize()
        data.Xrn.to_pickle(folder3 + '/XY_' + udl + '-st ' + str(st) + '-lt ' + str(lt) + '.pkl')
    else:
        data.X.to_pickle(folder3 + '/XY_' + udl + '-st ' + str(st) + '-lt ' + str(lt) + '.pkl')


##
# from ML import ML