from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import math
import jsonpickle

class Trader:
    def run(self, state: TradingState):
       # print("traderData: " + state.traderData)
       # print("Observations: " + str(state.observations))

        result = {}
        orders: List[Order] = []

        LIMIT = 50

        RAR = 'RAINFOREST_RESIN'
        KLP = 'KELP'
        SQI = 'SQUID_INK'


        
        # strategy for RAR
        
        pos_RAR = 0
        if RAR in state.position:
            pos_RAR = state.position[RAR]

        my_bid_RAR = 9998
        my_ask_RAR = 10002

        result[RAR] = [Order(RAR, 9998, LIMIT - pos_RAR), Order(RAR, 10002, -LIMIT - pos_RAR)]



        
        # strategy for KLP
        
        order_depth_KLP: OrderDepth = state.order_depths[KLP]

        # maximum orders to not exceed the limit
        pos_KLP = 0
        if KLP in state.position:
            pos_KLP = state.position[KLP]

        # compute bid price as just above the weighted average of bid price
        total_bid_volume = 0
        total_bid_prices = 0
        
        for bid_price, bid_volume in order_depth_KLP.buy_orders.items():
            total_bid_volume += bid_volume
            total_bid_prices += bid_price * bid_volume

        # what if total_bid_volume == 0?
        avg_bid_price = total_bid_prices / total_bid_volume
        
        total_ask_volume = 0
        total_ask_prices = 0
        
        for ask_price, ask_volume in order_depth_KLP.sell_orders.items():
            total_ask_volume += (-ask_volume)
            total_ask_prices += ask_price * (-ask_volume)

        avg_ask_price = total_ask_prices / total_ask_volume

        my_bid_KLP = round(0.75 * avg_bid_price + 0.25 * avg_ask_price)
        my_ask_KLP = round(0.25 * avg_bid_price + 0.75 * avg_ask_price)

        if (total_bid_volume > 0 and total_ask_volume > 0 and my_bid_KLP < my_ask_KLP):
            # only then, make bids and asks
            result[KLP] = [Order(KLP, my_bid_KLP, LIMIT - pos_KLP), Order(KLP, my_ask_KLP, -LIMIT - pos_KLP)]






        
        SQI_history = []
        if (state.traderData != ""):
            SQI_history = jsonpickle.decode(state.traderData)['SQI_history']
            
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
            MA50 = sum(SQI_history[-50:]) / 50
        if (T >= 200):
            MA200 = sum(SQI_history[-200:]) / 200
        if (T >= 1000):
            MA1000 = sum(SQI_history[-1000:]) / 1000

        if (False and T >= 1000):
            is_bull = (MA200 > MA1000)
            is_bear = (MA200 < MA1000)
        if (T >= 50):
            spike_up = (SQI_mid_price >= 1.02 * MA50)
            spike_down = (SQI_mid_price <= 0.98 * MA50)

        SQI_buy = 0
        SQI_sell = 0
        max_SQI_buy = LIMIT - SQI_pos
        max_SQI_sell = LIMIT + SQI_pos
        # just do market orders?
        SQI_buy_price = round(SQI_avg_ask)
        SQI_sell_price = round(SQI_avg_bid)
        if (spike_up):
            SQI_sell = max_SQI_sell
            SQI_sell_price -= 1
        elif (spike_down):
            SQI_buy = max_SQI_buy
            SQI_buy_price += 1
        elif (is_bull):
            SQI_buy = min(max_SQI_buy, 1)  # only buy 1
        elif (is_bear):
            SQI_sell = min(max_SQI_sell, 1) # only sell 1

        SQI_orders = []
        if (SQI_buy > 0):
            SQI_orders.append(Order(SQI, SQI_buy_price, SQI_buy))
        if (SQI_sell > 0):
            SQI_orders.append(Order(SQI, SQI_sell_price, -SQI_sell))
        result[SQI] = SQI_orders





        
        print('all orders:', result)
        
        traderData = jsonpickle.encode({'SQI_history': SQI_history})
        
        conversions = 0
        return result, conversions, traderData