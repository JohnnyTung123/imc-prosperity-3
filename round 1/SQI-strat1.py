from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import math
import jsonpickle

class Trader:
    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        
        SQI_history = []
        if (state.traderData != ""):
            SQI_history = (jsonpickle.decode(state.traderData))['SQI_history']

        result = {}
        orders: List[Order] = []

        LIMIT = 50
        SQI = 'SQUID_INK'
            
        # strategy for SQI
        order_depth_SQI: OrderDepth = state.order_depths[SQI]
        SQI_pos = 0
        if SQI in state.position:
            SQI_pos = state.position[SQI]

        # see if is bull / is bear
        # if bull + see immediate sell signal, sell!
        # if bear + see immediate buy signal, buy!

        # MA200 > MA1000 = bull
        # MA200 < MA1000 = bear
        # each time tick only market buy/sell 1 unit?

        # price > MA50 * 1.02 = spike up
        # price < MA50 * 0.98 = spike down
        # immediately switch
        
        # compute the mid price
        SQI_bid_volume = 0
        SQI_bid_prices = 0
        for bid_price, bid_volume in order_depth_SQI.buy_orders.items():
            SQI_bid_volume += bid_volume
            SQI_bid_prices += bid_price * bid_volume

        SQI_avg_bid = SQI_bid_prices / SQI_bid_volume

        SQI_ask_volume = 0
        SQI_ask_prices = 0
        for ask_price, ask_volume in order_depth_SQI.sell_orders.items():
            SQI_ask_volume += (-ask_volume)
            SQI_ask_prices += ask_price * (-ask_volume)

        SQI_avg_ask = SQI_ask_prices / SQI_ask_volume

        SQI_mid_price = (SQI_avg_bid + SQI_avg_ask) / 2

        SQI_history.append(SQI_mid_price)



        is_bull = False
        is_bear = False
        spike_up = False
        spike_down = False
        MA50 = -1
        MA200 = -1
        MA1000 = -1
        
        T = len(SQI_history)
        if (T >= 50):
            MA50 = sum(SQI_history[-200:]) / 50
        if (T >= 200):
            MA200 = sum(SQI_history[-200:]) / 200
        if (T >= 1000):
            MA1000 = sum(SQI_history[-1000:]) / 1000

        if (T >= 1000):
            is_bull = (MA200 > MA1000)
            is_bear = (MA200 < MA1000)
        if (T >= 50):
            spike_up = (SQI_mid_price >= 1.02 * MA50)
            spike_down = (SQI_mid_price <= 0.98 * MA50)

        my_buy = 0
        my_sell = 0
        max_buy = LIMIT - SQI_pos
        max_sell = LIMIT + SQI_pos
        # just do market orders?
        buy_price = round(SQI_avg_ask)
        sell_price = round(SQI_avg_bid)
        if (spike_up):
            my_sell = max_sell
            sell_price -= 1
        elif (spike_down):
            my_buy = max_buy
            buy_price += 1
        elif (is_bull):
            my_buy = min(max_buy, 1)  # only buy 1
        elif (is_bear):
            my_sell = min(max_sell, 1) # only sell 1

        SQI_orders = []
        if (my_buy > 0):
            SQI_orders.append(Order(SQI, buy_price, my_buy))
        if (my_sell > 0):
            SQI_orders.append(Order(SQI, sell_price, -my_sell))
        
        if (SQI_orders):
            result[SQI] = SQI_orders
        
        print('all orders:', result)
        
        traderData = jsonpickle.encode({'SQI_history': SQI_history})
        conversions = 0
        return result, conversions, traderData