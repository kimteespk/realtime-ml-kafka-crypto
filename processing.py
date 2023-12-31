from pandas import to_datetime
from numpy import timedelta64

from river import stats
from river.compose import Pipeline, FuncTransformer
from river.linear_model import LinearRegression
from river.preprocessing import StandardScaler

from river.forest import AMFRegressor, ARFRegressor

from river.utils import Rolling
from river.metrics import MAE, MSE, RMSE

from river import feature_extraction as fx



############# DATA PREPROCESSING ####################
def convert_timestamp(dct, unit= 'ms'):
    dct['openTime'] = to_datetime(dct['openTime'], unit= unit) + timedelta64(7, 'h')
    dct['closeTime'] = to_datetime(dct['closeTime'], unit= unit) + timedelta64(7, 'h')
    return dct


def time_extractor(dct):
    dct['date'] = str(dct['closeTime'].date())
    dct['hour'] = dct['closeTime'].hour
    dct['min'] = dct['closeTime'].minute
    
    return dct

def convert_datatype(dct):
    base_dct = dct
    # dct = {key: float(dct[key]) for key in dct.keys() if 'Time' not in key and 'x'}
    dct = {key: float(dct[key]) if 'Time' not in key else dct[key] for key in dct.keys()}

    return dct


def preprocessing_pipeline(dct):
    dct = convert_timestamp(dct)
    dct = convert_datatype(dct)
    dct = time_extractor(dct)

    
    return dct

def create_agg():

    max_pct_price_chg = fx.Agg(
        on= 'priceChangePercent',
        by= 'hour',
        how = stats.Max()
    )

    min_pct_price_chg = fx.Agg(
        on= 'priceChangePercent',
        by= 'hour',
        how = stats.Min()
    )
    agg = (max_pct_price_chg + min_pct_price_chg)
    
    return agg


def _get_agg_feature_name(agg_item):
    return '_'.join([agg_item.on , str(agg_item.how).split(':')[0].lower(),'by', agg_item.by[0]])

    
    
def transform_agg(data, agg):
    if data[agg[0].by[0]] == None:
        for i in range(len(agg)):
            dct = {_get_agg_feature_name(agg[i]): None}
            data.update(dct)
        return data
    # print(data)
    agg.learn_one(data)
    dct_result = agg.transform_one(data)
    data.update(dct_result)
    
    return data

    
    
    

    
# EXCLUDE KEY
class MultiKeyShift:
    def __init__(self, keys, window_size, key_exclude= 'lastPrice'):
        self.key_exclude = key_exclude
        keys.remove(key_exclude)
        self.keys = keys
        self.shifts = {key: stats.Shift(window_size) for key in keys}


    def update(self, dct):
        self.dct_y = {self.key_exclude: dct[self.key_exclude]}
        dct_x = {key: self.shifts[key].update(dct[key]) for key in self.keys}
        return {**dct_x, **self.dct_y}
    
    def get(self):
        dct_x = {key: self.shifts[key].get() for key in self.keys}
        return {**dct_x, **self.dct_y}



############ MODEL ############
def create_pipeline():
    
    pl = Pipeline(
        # ('ordinal_date', FuncTransformer(get_ordinal_date)),
        ('scale', StandardScaler()),
        ('AMF REG ', AMFRegressor(n_estimators= 10, step= 5,seed=42))
        # ('lr', LinearRegression())
    )
    print(pl)

    return pl


def create_metric(metric_str= 'MSE', rolling_size= 12):
    dct_met = {
        'MAE': MAE,
        'MSE': MSE,
        'RMSE': RMSE
    }
    met = dct_met[metric_str.upper()]
    return Rolling(met(), rolling_size)
    # return Rolling(MAE(), 12)

def learn_pred(x, y, pl, metric):
    
    # version 0.21.0
    if x['openPrice'] == None:
        return x, y, None, pl, metric
    try:
        y_pred_old = pl.predict_one(x)
        pl.learn_one(x, y)
        metric.update(y, y_pred_old)
    except:
        return x, y, None, pl, metric
    
    # version 0.20.1
    # if x['openPrice'] == None:
    #     return x, y, None, pl, metric
    # try:
    #     y_pred_old = pl.predict_one(x)
    #     pl = pl.learn_one(x, y)
    #     metric = metric.update(y, y_pred_old)
    # except:
    #     return x, y, None, pl, metric

    # y_pred_old = pl.predict_one(x)
    # # pl = pl.learn_one(x, y)
    # pl = pl.learn_one(x, y)
    # print(pl)
    # metric = metric.update(y, y_pred_old)


    return x, y, y_pred_old, pl, metric

    
if __name__ == '__main__':
    print(__name__)
    
    
    
    
############# ONLINE PROCESSING ###################
# class MultiKeyShift:
#     def __init__(self, keys, window_size):
#         self.keys = keys
#         self.shifts = {key: stats.Shift(window_size) for key in keys}

#     def update(self, dct):
#         return {key: self.shifts[key].update(dct[key]) for key in self.keys}
    
#     def get(self):
#         return {key: self.shifts[key].get() for key in self.keys}
    
    

# def shift_back_data(dct, period: int= 180, stat= None):

#     stat = stat or stats.Shift(period)
#     lst_price = dct.pop('lastPrice')
#     dct_x = dct
    
#     stat = stat.update(dct_x)
#     dct_x = stat.get()
#     current_data = {**dct_x, 'lastPrice': lst_price}

#     return current_data, stat

