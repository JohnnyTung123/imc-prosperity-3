from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import jsonpickle
import math

class Trader:
    def run(self, state: TradingState):
        
        CST = 'CROISSANTS'
        JAM = 'JAMS'
        DJE = 'DJEMBES'
        SQI = 'SQUID_INK'
        KLP = 'KELP'
        RAR = 'RAINFOREST_RESIN'
        PB1 = 'PICNIC_BASKET1'
        PB2 = 'PICNIC_BASKET2'
        # symbols = {CST, JAM, DJE, SQI, KLP, RAR, PB1, PB2}
        symbols = {SQI, KLP, RAR}
        position_limits = {CST: 250, JAM: 350, DJE: 60, PB1: 60, PB2: 100, SQI: 50, KLP: 50, RAR: 50}

        
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        result = {}
        orders: List[Order] = []
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


        # RAR
        S = RAR
        RAR_true_price = 10000
        RAR_orders = []
        order_depth_S: OrderDepth = state.order_depths[S]
        remaining_bids_S = position_limits[S] - cur_pos[S]
        remaining_asks_S = position_limits[S] + cur_pos[S]
        base_ask_S = math.ceil(ask_prices[S]) - 1
        base_bid_S = math.floor(bid_prices[S]) + 1
        
        RAR_orders.append(Order(RAR, base_bid_S, remaining_bids_S))
        RAR_orders.append(Order(RAR, base_ask_S, -remaining_asks_S))
        
        result[RAR] = RAR_orders
        
        traderData = ""
        conversions = 0
        
        return result, conversions, traderData