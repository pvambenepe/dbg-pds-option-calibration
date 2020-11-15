from SetUp import *

def get_raw_data():

    from_date = '2017-01-01'
    until_date = '2020-10-02'
    last_matu = '2022-12-31'
    dates = list(pd.date_range(from_date, until_date, freq='D').strftime('%Y-%m-%d'))
    dates_expi = list(pd.date_range(from_date, last_matu, freq='W'))
    dates_expi = [elt-datetime.timedelta(2) for elt in dates_expi]
    dates_expi = [elt for elt in dates_expi if elt.day in [15,16,17,18,19,20,21]]
    # dates_expi_trim = [elt for elt in dates_expi if elt.month in [3,6,9,12]]



    dates = list(pd.date_range(from_date, until_date, freq='D').strftime('%Y-%m-%d'))
    dates_expi = list(pd.date_range(from_date, last_matu, freq='W'))
    dates_expi = [elt-datetime.timedelta(2) for elt in dates_expi]
    dates_expi = [elt for elt in dates_expi if elt.day in [15,16,17,18,19,20,21]]
    dates_expi_trim = [elt for elt in dates_expi if elt.month in [3,6,9,12]]

    def next_expi_trim(dt):
        lst2 = [elt for elt in dates_expi_trim if elt > dt+datetime.timedelta(1)]
        return lst2[0]

    #
    time_fmt = "%H:%M"
    opening_hours = datetime.datetime.strptime(opening_hours_str, time_fmt)
    closing_hours = datetime.datetime.strptime(closing_hours_str, time_fmt)


    #keep basic stock features
    def basic_stock_features(input_df, new_time_index):
            stock = input_df.copy()

            stock['HasTrade'] = 1.0

            stock = stock.reindex(new_time_index)

            features = ['MinPrice', 'MaxPrice', 'EndPrice', 'StartPrice']
            for f in features:
                stock[f] = stock[f].fillna(method='ffill')

            features = ['HasTrade', 'TradedVolume', 'NumberOfTrades']
            for f in features:
                stock[f] = stock[f].fillna(0.0)

            selected_features = ['MinPrice', 'MaxPrice', 'StartPrice', 'EndPrice', 'HasTrade', 'TradedVolume',
                                 'NumberOfTrades']
            return stock[selected_features]


    print('Start')
    print(datetime.datetime.now())

    for stk in stocks_list:

        print(stk)

        def get_and_select(filename):
            df = pd.read_csv(filename)
            if stk == 'SX5E':
                return df[df['UnderlyingSymbol'] == stk]
            elif 'XETR' in filename:
                return df[df['Mnemonic'] == stk]
            else:
                return df[df['UnderlyingISIN'] == isin]


        def load_csv_dirs(data_dirs):
            files = []
            for data_dir in data_dirs:
                files.extend(glob.glob(os.path.join(data_dir, '*.csv')))

            return pd.concat(map(get_and_select, files))

        if stk != 'SX5E':
            data_dir = local_data_folder + '/'
            data_subdirs = map(lambda date: data_dir + date, dates)
            unprocessed_df = load_csv_dirs(data_subdirs)
        else:
            data_dir = local_data_folder_opt + '/'
            data_subdirs = map(lambda date: data_dir + date, dates)
            unprocessed_df = load_csv_dirs(data_subdirs)

            for elt in ['NumberOfContracts']:
                unprocessed_df[elt] = pd.to_numeric(unprocessed_df[elt])

            unprocessed_df = unprocessed_df.loc[unprocessed_df.SecurityType == 'FUT']
            unprocessed_df['MaturityDate'] = pd.to_datetime(unprocessed_df['MaturityDate'], format="%Y%m%d")
            unprocessed_df['NextMatu'] = pd.to_datetime(unprocessed_df['Date'], format="%Y-%m-%d").apply(next_expi_trim)
            unprocessed_df = unprocessed_df.loc[unprocessed_df.MaturityDate == unprocessed_df.NextMatu]
            unprocessed_df = unprocessed_df[['Time', 'Date', 'NumberOfContracts', 'MaxPrice', 'MinPrice', 'UnderlyingISIN']]
            unprocessed_df.columns = ['Time', 'Date', 'TradedVolume', 'MaxPrice', 'MinPrice', 'ISIN']


        isin = unprocessed_df['ISIN'].iloc[0]
        print(isin)

        data_dir = local_data_folder_opt + '/'
        data_subdirs = map(lambda date: data_dir + date, dates)
        unprocessed_df_opt = load_csv_dirs(data_subdirs)

        for elt in ['NumberOfContracts']:
            unprocessed_df_opt[elt] = pd.to_numeric(unprocessed_df_opt[elt])

        print('unprocessed_df_opt')
        print(unprocessed_df_opt.head(10))
        print(unprocessed_df_opt.shape)
        print(unprocessed_df.shape)
        print(datetime.datetime.now())

        unprocessed_df["CalcTime"] = pd.to_datetime("1900-01-01 " + unprocessed_df["Time"])

        unprocessed_df_opt["CalcTime"] = pd.to_datetime("1900-01-01 " + unprocessed_df_opt["Time"])

        unprocessed_df["CalcDateTime"] = pd.to_datetime(unprocessed_df["Date"] + " " + unprocessed_df["Time"])
        unprocessed_df_opt["CalcDateTime"] = pd.to_datetime(unprocessed_df_opt["Date"] + " " + unprocessed_df_opt["Time"])

        # Filter common stock
        # Filter between trading hours 08:00 and 17:30
        # Exclude auctions (those are with TradeVolume == 0)
        print('End of preprocessing')
        print(datetime.datetime.now())

        cleaned = unprocessed_df[(unprocessed_df.TradedVolume > 0) & \
                          (unprocessed_df.CalcTime >= opening_hours) & \
                          (unprocessed_df.CalcTime <= closing_hours)]

        cleaned_opt = unprocessed_df_opt[(unprocessed_df_opt.NumberOfContracts > 0) & \
                          (unprocessed_df_opt.CalcTime >= opening_hours) & \
                          (unprocessed_df_opt.CalcTime <= closing_hours) & \
                          (unprocessed_df_opt.SecurityType == 'OPT')]
        print('cleaned_opt')
        print(cleaned_opt.head(10))
        print(datetime.datetime.now())

        sorted_by_index = cleaned.set_index(['CalcDateTime']).sort_index()
        sorted_by_index_opt = cleaned_opt.set_index(['CalcDateTime']).sort_index()

        sorted_by_index['PriceU'] = (sorted_by_index['MaxPrice'] + sorted_by_index['MinPrice'])/2
        sorted_by_index_opt['PriceO'] = (sorted_by_index_opt['MaxPrice'] + sorted_by_index_opt['MinPrice']) / 2

        sorted_by_index['ErrorU'] = (sorted_by_index['MaxPrice'] - sorted_by_index['MinPrice'])/2
        sorted_by_index_opt['ErrorO'] = (sorted_by_index_opt['MaxPrice'] - sorted_by_index_opt['MinPrice']) / 2

        trimed = sorted_by_index[['PriceU', 'ErrorU', 'TradedVolume']]
        trimed_opt = sorted_by_index_opt[['PriceO', 'ErrorO', 'NumberOfContracts', 'NumberOfTrades', 'MaturityDate', 'StrikePrice', 'PutOrCall', 'MLEG']]
        trimed_opt['MaturityDate'] = pd.to_datetime(trimed_opt['MaturityDate'], format="%Y%m%d")
        trimed_opt['TTM'] = (trimed_opt.MaturityDate - trimed_opt.index).dt.days / 365

        print('trimed_opt')
        print(trimed_opt.head(10))
        print(datetime.datetime.now())

        prepared = pd.merge(trimed, trimed_opt, left_index=True, right_index=True, how='inner')
        prepared['ErrorU'] = prepared['ErrorU'] / prepared['PriceU'] * 10000
        prepared['ErrorO'] = prepared['ErrorO'] / prepared['PriceU'] * 10000

        print('prepared')
        print(prepared.head(10))
        print(datetime.datetime.now())

        prepared.to_pickle(folder1 + '/Execs_' + stk + '.pkl')
        trimed.to_pickle(folder1 + '/UDL_' + stk + '.pkl')



