import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib as mpl
import copy
from sklearn.linear_model import LinearRegression


def PrepareDF(DF):
    # Функція формування повного датафрейму

    ohlc = DF
    ohlc.columns = ["date", "open", "high", "low", "close", "volume"]   # Зміна назв колонок датафрейму
    ohlc = ohlc.set_index('date')                                       # Установка стовпчика date в якості індексу датафрейму
    df = indATR(ohlc, 14).reset_index()
    df['slope'] = indSlope(df['close'], 5)
    df['chanel_max'] = df['high'].rolling(10).max()
    df['chanel_min'] = df['low'].rolling(10).min()
    df['position_in_channel'] = (df['close'] - df['chanel_min']) / (df['chanel_max'] - df['chanel_min'])
    df = df.set_index('date')
    df = df.reset_index()
    return df


# True Range and Average True Range indicator
def indATR(source_DF, n):
    # ATR - Середній справжній діапазон.
    # Індікатор призначений для виявлення поточної волатильності інструменту.

    """
    TR = max[(H-L), |H-Cp|, |L-Cp|]
    ATR = 1/n * sum(TR)
    TR: a particular True Range
    n: the time period employed
    H: current High
    L: current Low
    Cp: previous close
    """
    df = source_DF.copy()                                               # копіювання та прсвоєння вхідного датафрейму
    df['H-L'] = abs(df['high']-df['low'])                               # розрахунок, згідно опису.
    df['H-PC'] = abs(df['high']-df['close'].shift(1))                   # shift зміщує даний показник на задану кількість позицій
    df['L-PC'] = abs(df['low']-df['close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1, skipna=False)    # axis=1 (колонки) skipna=False (добавляє значення NaN в операцію)
    df['ATR'] = df['TR'].rolling(n).mean()                              # rolling(n).mean() виявляє середнє з n значень по всьому датафрейму
    df_temp = df.drop(['H-L', 'H-PC', 'L-PC'], axis=1)                  # видалення непотрібних стовбців
    return df_temp


def indSlope(series, n):
    # Функція для визначення кута нахилу тренда.

    array_sl = [j * 0 for j in range(n-1)]
    for j in range(n, len(series)+1):
        y = series[j-n:j]
        x = np.array(range(n))
        x_sc = (x - x.min()) / (x.max() - x.min())
        y_sc = (y - y.min()) / (y.max() - y.min())
        x_sc = sm.add_constant(x_sc)
        model = sm.OLS(y_sc, x_sc)
        results = model.fit()
        array_sl.append(results.params[-1])
    slope_angle = (np.rad2deg(np.arctan(np.array(array_sl))))
    return np.array(slope_angle)


def isLCC(DF, i):
    df = DF.copy()
    LCC = 0
    if df['close'][i] <= df['close'][i+1] and df['close'][i] <= df['close'][i-1] and df['close'][i+1] > df['close'][i-1]:
        # Local min
        LCC = i - 1
    return LCC

def isHCC(DF, i):
    df = DF.copy()
    HCC = 0
    if df['close'][i] >= df['close'][i + 1] and df['close'][i] >= df['close'][i - 1] and df['close'][i + 1] < df['close'][i - 1]:
        #Local max
        HCC = i
    return HCC

def getMaxMinChannel(DF, n):
    maxx = 0
    minn = DF['low'].max()
    for i in range(1, n):
        if maxx < DF['high'][len(DF) - i]:
            maxx = DF['high'][len(DF) - i]
        if minn > DF['low'][len(DF) - i]:
            minn = DF['low'][len(DF) - i]
    return maxx, minn