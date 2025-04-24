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
        total_bid_volume = 0
        total_bid_prices = 0
        
        for bid_price, bid_volume in order_depth.buy_orders.items():
            total_bid_volume += bid_volume
            total_bid_prices += bid_price * bid_volume

        # what if total_bid_volume == 0?
        my_bid_price = math.floor(total_bid_prices / total_bid_volume) + 1
        
        total_ask_volume = 0
        total_ask_prices = 0
        
        for ask_price, ask_volume in order_depth.sell_orders.items():
            total_ask_volume += (-ask_volume)
            total_ask_prices += ask_price * (-ask_volume)

        my_ask_price = math.ceil(total_ask_prices / total_ask_volume) - 1

        if (total_bid_volume > 0 and total_ask_volume > 0 and my_bid_price < my_ask_price):
            # only then, make bids and asks
            result[KLP] = [Order(KLP, my_bid_price, LIMIT - KLP_pos), Order(KLP, my_ask_price, -LIMIT - KLP_pos)]

        print('all orders:', result)
        
        traderData = ""
        conversions = 0
        return result, conversions, traderData