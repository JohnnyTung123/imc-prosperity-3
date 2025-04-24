from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import math

class Trader:
    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        result = {}
        orders: List[Order] = []

        LIMIT = 50

        # strategy for KLP
        
        KLP = 'KELP'
        order_depth: OrderDepth = state.order_depths[KLP]

        # maximum orders to not exceed the limit
        KLP_pos = 0
        if KLP in state.position:
            KLP_pos = state.position[KLP]

        # compute bid price as just above the weighted average of bid price
        my_bid_price = 0
        
        for bid_price, bid_volume in order_depth.buy_orders.items():
            my_bid_price = max(my_bid_price, bid_price)
        
        my_ask_price = 9999
        for ask_price, ask_volume in order_depth.sell_orders.items():
            my_ask_price = min(my_ask_price, ask_price)

        if (my_bid_price < my_ask_price):
            result[KLP] = [Order(KLP, my_bid_price, LIMIT - KLP_pos), Order(KLP, my_ask_price, -LIMIT - KLP_pos)]

        print('all orders:', result)
        
        traderData = ""
        conversions = 0
        return result, conversions, traderData