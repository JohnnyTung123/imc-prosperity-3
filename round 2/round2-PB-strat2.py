from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import jsonpickle
import math

class Trader:
    def run(self, state: TradingState):
        SQI = 'SQUID_INK'
        KLP = 'KELP'
        RAR = 'RAINFOREST_RESIN'
        
        CST = 'CROISSANTS'
        JAM = 'JAMS'
        DJE = 'DJEMBES'
        PB1 = 'PICNIC_BASKET1'
        PB2 = 'PICNIC_BASKET2'
        
        symbols_r1 = {SQI, KLP, RAR}
        symbols_r2 = {CST, JAM, DJE, PB1, PB2}
        symbols = symbols_r1.union(symbols_r2)
        
        position_limits = {CST: 250, JAM: 350, DJE: 60, PB1: 60, PB2: 100, SQI: 50, KLP: 50, RAR: 50}

        # CST and JAM will be over-exposed, so not sure if it's a great idea...
        # in the end, should probably use some kind of z-score
        PB1_index_thresholds = [0, 100]
        PB2_index_thresholds = [0, 100]
        PB1_limit = position_limits[PB1]
        PB2_limit = position_limits[PB2]


        
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        result = {}
        orders: List[Order] = []

        # maximum orders to not exceed the limit
        # first compute average bid, average ask
        bid_prices = {}
        ask_prices = {}
        highest_bids = {}
        lowest_asks = {}
        cur_pos = {}
        avg_prices = {}

        
        
        for S in symbols:
            # get current position
            cur_pos[S] = 0
            if (S in state.position):
                cur_pos[S] = state.position[S]
            order_depth_S: OrderDepth = state.order_depths[S]

            highest_bids[S] = max(order_depth_S.buy_orders)
            lowest_asks[S] = min(order_depth_S.sell_orders)
            
            total_bid_volume = 0
            total_bid_prices = 0

            total_ask_volume = 0
            total_ask_prices = 0
            
            for bid_price, bid_volume in order_depth_S.buy_orders.items():
                total_bid_volume += bid_volume
                total_bid_prices += bid_price * bid_volume
            avg_bid_price = total_bid_prices / total_bid_volume
            
            for ask_price, ask_volume in order_depth_S.sell_orders.items():
                total_ask_volume += (-ask_volume)
                total_ask_prices += ask_price * (-ask_volume)
            avg_ask_price = total_ask_prices / total_ask_volume

            bid_prices[S] = avg_bid_price
            ask_prices[S] = avg_ask_price
            avg_prices[S] = (avg_bid_price + avg_ask_price) / 2

        
        for S in {PB1, PB2}:
            S_bid_price = math.floor(bid_prices[S]) + 1
            S_ask_price = math.ceil(ask_prices[S]) - 1
            S_buy_limit = position_limits[S] - cur_pos[S]
            S_sell_limit = position_limits[S] + cur_pos[S]
            result[S] = [Order(S, S_bid_price, S_buy_limit), Order(S, S_ask_price, -S_sell_limit)]

        traderData = ""
        conversions = 0
        return result, conversions, traderData