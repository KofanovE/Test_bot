import copy
import glob

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib as mpl
from datetime import datetime

from scipy.stats import trim_mean
from Indicators import *


def main():

    pd.set_option('display.max_columns', None)  #форматування відображення DataFrame
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_colwidth', None)




    # url = f'https://www.alphavantage.co/query?function=CRYPTO_INTRADAY&symbol=ETH&market=USD&interval=5min&apikey=demo&datatype=csv'
    # df = pd.read_csv(url)


    data_files = glob.glob(r".\data_eth\*.csv", recursive=True) # механізм зчитування данних з декількох файлів з заданої директорії
    cont = []
    for i in range(len(data_files)):
        df = pd.read_csv(data_files[i], header=None, names=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                                       '6', '7', '8', '9', '10', '11'])
        cont.append(df)
    df = pd.concat(cont)

    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    # df = df[::-1]
    prepared_df = PrepareDF(df)     # Формування датафрейму однохвилинних свічок [timestamp, open, high, low, close, volume]
    lend = len(prepared_df)  # Змінна кількості строк у датафреймі


    df_science = pd.DataFrame({'profit_deal' : [],                   # створення дослідницького датафрейму
                               'time_open' : [],
                               'price_open' : [],
                               'position_open' : [],
                               'slope_open' : [],
                               'price_min' : [],
                               'price_max' : [],
                               'min_mean' : [],
                               'max_mean' : [],
                               'time_close' : [],
                               'price_close' : [],
                               'position_close' : [],
                               'slope_close' : [],
                               'profit' : []})

    num = 0                                                          # Змінна номеру строки в дослідницькому датафреймі
    min_arr = []
    max_arr = []

    sl_percent = 0.01
    slope = 20
    chanel_dif = 0.1




    # Добавлення колонок вершин high i low, якщо спрацювали відповідні індикатори

    prepared_df['hcc'] = [None] * lend                              # Додавання колонок вершин і впадин
    prepared_df['lcc'] = [None] * lend
    for i in range(4, lend-1):                                      # Для всіх строк, починаючи з 4-ї добавляються значення в колонки вершин..
        if isHCC(prepared_df, i) > 0:                               # .. якщо спрацювали відповідні індикатори
            prepared_df.at[i, 'hcc'] = prepared_df['close'][i]
        if isLCC(prepared_df, i) > 0:
            prepared_df.at[i, 'lcc'] = prepared_df['close'][i]






    # Тестова стратегія
    #________________________________________________________________________________________________
    deal = 0
    position = 0
    eth_proffit_array = [[20, 1], [40, 1], [60, 2], [80, 2], [100, 2], [150, 1], [200, 1], [200, 0]]      # Список кроків в ціні, та величина закриття позиції

    prepared_df['deal_o'] = [None] * lend                       # Добавлення колонок відкриття транзакції, закриття, і поточного прибутку
    prepared_df['deal_c'] = [None] * lend
    prepared_df['earn'] = [None] * lend


    for i in range(4, lend-1):                                  # Для кожної строки датафрейму, починаючи з 4-ї
        prepared_df.at[i, 'earn'] = deal                        # ініціалізація прибутку

        if position != 0:
            min_arr.append(prepared_df['low'][i])
            max_arr.append(prepared_df['high'][i])
            if df_science['price_min'][num] > prepared_df['low'][i]:
                df_science.at[num, 'price_min'] = prepared_df['low'][i]
            if df_science['price_max'][num] < prepared_df['high'][i]:
                df_science.at[num, 'price_max'] = prepared_df['high'][i]


        if position > 0:                                        # Якщо величина позиції більше 0:
            #long
            if prepared_df['low'][i] < stop_prise:            # Якщо актуальний прайс менше межі стоплосу, то стоп-лос
                #stop_loss
                deal -= (open_price-prepared_df['close'][i])*abs(position) # Визначення величини збитку: відкриття-закриття
                position = 0                                          # Закриття позиції
                prepared_df.at[i, 'deal_c'] = prepared_df['close'][i] # запис у колонку закритих позицій
            else:                                                   # Якщо актуальний прайс не менше межі стоплосу, то
                temp_arr = copy.copy(proffit_array)                 # Копіювання списку proffit_array
                for j in range(0, len(temp_arr) - 1):               # Для кожного шагу ціни в temp_arr
                    delta = temp_arr[j][0]                          # Поточний профітний крок ціни delta
                    contracts = temp_arr[j][1]                      # Поточний профітний крок позиції
                    if prepared_df['high'][i] > open_price + delta:                        # Якщо поточна ціна більше ціни відкриття + поточний профітний крок ціни delta
                        prepared_df.at[i, 'deal_c'] = prepared_df['close'][i]               # Запис ціни неповного закриття поточного профітного кроку
                        position = position - contracts                                     # Від позиції віднімається поточний профітний крок
                        deal += (prepared_df['close'][i] - open_price)*contracts            # До прибутку добавляється різниця в ціні * на величину закритої профітної позиції
                        del proffit_array[0]                                                # Видалення першого досягнутого профітного кроку

                        df_science.at[num, 'profit'] += contracts
                        df_science.at[num, 'profit_deal'] = True

        elif position < 0:                                                                  # Все теж саме, але, коли відкита позиція в шорт
            #short
            if prepared_df['high'][i] > stop_prise:
                #stop loss
                deal -= (prepared_df['close'][i] - open_price)*abs(position)
                position = 0
                prepared_df.at[i, 'deal_c'] = prepared_df['close'][i]
            else:
                temp_arr = copy.copy(proffit_array)
                for j in range(0, len(temp_arr)-1):
                    delta = temp_arr[j][0]
                    contracts = temp_arr[j][1]
                    if prepared_df['low'][i] < open_price - delta:
                        prepared_df.at[i, 'deal_c'] = prepared_df['close'][i]
                        position = position + contracts
                        deal += (open_price - prepared_df['close'][i]) * contracts
                        del proffit_array[0]

                        df_science.at[num, 'profit'] += contracts
                        df_science.at[num, 'profit_deal'] = True

            if position == 0:

                df_science.at[num, 'time_close'] = prepared_df['date'][i]
                df_science.at[num, 'price_close'] = prepared_df['close'][i]
                df_science.at[num, 'position_close'] = prepared_df['position_in_channel'][i]
                df_science.at[num, 'slope_close'] = prepared_df['slope'][i]
                df_science.at[num, 'min_mean'] = np.mean(min_arr)
                df_science.at[num, 'max_mean'] = np.mean(max_arr)
                num += 1



        else:                                                                       # Якщо відкритої позиції не знайдено
            if prepared_df['lcc'][i-1] != None:                                     # Якщо на даній свічі в стовпці "впадина" відкрита позиція
                #Long
                if prepared_df['position_in_channel'][i-1] < 0.5 - chanel_dif:      # Якщо позиція в каналі менше 0.5 (можна змінювати)...
                    if prepared_df['slope'][i-1] > slope:                           # ...та якщо кут нахилу менше -20 (тут є питання ->)
                        prepared_df.at[i, 'deal_o'] = prepared_df['close'][i]       # В колонку відкриття записується дана свічка
                        proffit_array = copy.copy(eth_proffit_array)                # В proffit_array записується список профітних кроків
                        position = 10                                               # Відкривається позиція 10 в лонг
                        open_price = prepared_df['close'][i]                        # Запис змінної відкриття
                        stop_prise = prepared_df['close'][i] * (1 - sl_percent)     # Запис змінної стоплос


                        df_science.at[num, 'profit_deal'] = False
                        df_science.at[num, 'time_open'] = prepared_df['date'][i]
                        df_science.at[num, 'price_open'] = prepared_df['close'][i]
                        df_science.at[num, 'position_open'] = prepared_df['position_in_channel'][i-1]
                        df_science.at[num, 'slope_open'] = prepared_df['slope'][i-1]
                        df_science.at[num, 'price_min'] = prepared_df['close'][i]
                        df_science.at[num, 'price_max'] = prepared_df['close'][i]
                        df_science.at[num, 'profit'] = 0



            if prepared_df['hcc'][i - 1] != None:                                       # Все теж саме, але,якщо в стовпці "вершина" відкрита позиція
                # Short
                if prepared_df['position_in_channel'][i-1] > 0.5 + chanel_dif:
                    if prepared_df['slope'][i - 1] < -slope:
                        prepared_df.at[i, 'deal_o'] = prepared_df['close'][i]
                        proffit_array = copy.copy(eth_proffit_array)
                        position = -10
                        open_price = prepared_df['close'][i]
                        stop_prise = prepared_df['close'][i] * (1 + sl_percent)


                        df_science.at[num, 'profit_deal'] = False
                        df_science.at[num, 'time_open'] = prepared_df['date'][i]
                        df_science.at[num, 'price_open'] = prepared_df['close'][i]
                        df_science.at[num, 'position_open'] = prepared_df['position_in_channel'][i-1]
                        df_science.at[num, 'slope_open'] = prepared_df['slope'][i-1]
                        df_science.at[num, 'price_min'] = prepared_df['close'][i]
                        df_science.at[num, 'price_max'] = prepared_df['close'][i]
                        df_science.at[num, 'profit'] = 0

    # print(prepared_df)
    df_science = df_science.fillna(0)
    df_science['time_open'] = [datetime.fromtimestamp(d/1000) if d != 0 else 0 for d in df_science["time_open"]]
    df_science['time_close'] = [datetime.fromtimestamp(d/1000) if d != 0 else 0 for d in df_science["time_close"]]
    df_science['sl_percent'] = [None] * len(df_science)
    df_science.at[0, 'sl_percent'] = sl_percent
    df_science['slope'] = [None] * len(df_science)
    df_science.at[0, 'slope'] = slope
    df_science['slope'] = [None] * len(df_science)
    df_science.at[0, 'slope'] = slope
    df_science['chan_diff'] = [None] * len(df_science)
    df_science.at[0, 'chan_diff'] = chanel_dif
    df_science['amount_deals'] = [None] * len(df_science)
    df_science.at[0, 'amount_deals'] = len(df_science)
    df_science['amt_prof_deals'] = [None] * len(df_science)
    df_science.at[0, 'amt_prof_deals'] = len(df_science[df_science['profit_deal'] == True])
    df_science['earn'] = [None] * len(df_science)
    df_science.at[0, 'earn'] = deal

    df_science.to_csv('statistical_result.csv', encoding='utf-8')
    print(df_science)



    # prepared_df[0:100][['slope']].plot()
    # prepared_df[0:100][['close']].plot()
    # prepared_df[0:100][['close', 'chanel_max', 'chanel_min']].plot()
    # plt.show()


    # Visualization
    aa = prepared_df
    aa = aa.reset_index()

    labels = ['close', 'deal_o', 'deal_c']
    labels_line = ['--', '*-', '*-', 'g-', 'r-']

    j = 0
    x = pd.DataFrame()
    y = pd.DataFrame()
    for i in labels:
        x[j] = aa['index']
        y[j] = aa[i]
        j += 1

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)

    fig.suptitle("Deals")
    fig.set_size_inches(20, 10)

    for j in range(0, len(labels)):
        ax1.plot(x[j], y[j], labels_line[j])

    ax1.set_ylabel("Price")
    ax1.grid(True)

    ax2.plot(x[0], aa['earn'], 'g-')
    ax3.plot(x[0], aa['position_in_channel'], '.-')

    ax2.grid(True)
    ax3.grid(True)
    plt.show()



if __name__ == "__main__":
    main()