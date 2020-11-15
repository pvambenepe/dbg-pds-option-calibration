from SetUp import *


class Graph():
    def __init__(self, udl = 'DAI'):
        self.udl = udl
        self.dfe = pd.read_pickle(folder2 + '/Parameters_' + udl + '.pkl')
        self.dfi = pd.read_pickle(folder2 + '/Inputs_' + udl + '.pkl')
        # self.dfp = pd.read_pickle(folder3 + '/X_' + udl + '.pkl')
        # st = 5
        # lt = 8 * 20
        # self.dfxy = pd.read_pickle(folder3 + '/XY_' + udl + '-st ' + str(st) + '-lt ' + str(lt) + '.pkl')


    def graph_params(self, year = 2020, month = 9):
        expi = pd.Timestamp(str(year) + "-{:02d}".format(month) + "-15 15:30:00")
        self.dfet = self.dfe.loc[self.dfe.ExpiDate.isin([expi + pd.Timedelta(i, unit='d') for i in range(7)])]

        self.dfet['ATF'] = self.dfet['ATF'] / 10
        self.dfet['EWMA_ATF'] = self.dfet['EWMA_ATF'] / 10
        self.dfet['divyield'] = (1 - self.dfet['FwdRatio']) * 100
        self.dfet['EWMA_divyield'] = (1 - self.dfet['EWMA_FwdRatio']) * 100
        self.dfet.index = self.dfet.StartTime

        plt.close()
        self.dfet[['ATF', 'SMI', 'CVX', 'divyield', 'Error']].plot()
        plt.show()



    def graph_inputs(self, year = 2020, field = 'EWMA_ATF'):
        self.l = list(dict.fromkeys(self.dfi.MaturityDate.tolist()))

        plt.close()
        for expi in [elt for elt in self.l if elt.year == year]:
            self.dfit = self.dfi.loc[self.dfi.MaturityDate == expi]
            self.dfit[field].plot()
        plt.show()


    def graph_X(self, year=2020, field='EWMA_ATF'):
        self.listcol = [elt for elt in self.dfp.columns if (elt[0] == field) and (elt[1].year() == year)]
        self.dfpt = self.dfp[self.listcol]
        newlistcol = [elt[1] for elt in self.listcol]
        self.dfpt.columns = newlistcol
        plt.close()
        self.dfpt.plot()
        plt.show()


    def graph_XY(self, year=2020, field='EWMA_ATF'):
        self.listcol = [elt for elt in dfxy.columns if (elt[0] == field) and (elt[1].year() == year)]
        self.dfxyf = self.dfxy[self.listcol]
        newlistcol = [elt[1] for elt in self.listcol]
        self.dfxyf.columns = newlistcol
        plt.close()
        self.dfxyf.plot()
        plt.show()


