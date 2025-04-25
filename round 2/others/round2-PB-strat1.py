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
        PB1_buffer = 2
        PB2_buffer = 3

        
        
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


        def scoring(x, lo, hi):
           if (x < lo):
               return 0
           elif (x > hi):
               return 1
           else:
               return ((x - lo) / (hi - lo))

        # compute directions for each product
        PB1_long_index = avg_prices[CST] * 6 + avg_prices[JAM] * 3 + avg_prices[DJE] - avg_prices[PB1]
        PB2_long_index = avg_prices[CST] * 4 + avg_prices[JAM] * 2 - avg_prices[PB2]
        PB1_long_score = scoring(PB1_long_index, PB1_index_thresholds[0], PB1_index_thresholds[1]) * PB1_limit
        PB1_short_score = scoring(-PB1_long_index, PB1_index_thresholds[0], PB1_index_thresholds[1]) * PB1_limit
        PB2_long_score = scoring(PB2_long_index, PB2_index_thresholds[0], PB2_index_thresholds[1]) * PB2_limit
        PB2_short_score = scoring(-PB2_long_index, PB1_index_thresholds[0], PB1_index_thresholds[1]) * PB2_limit
        
        target_position = {}
        target_position[PB1] = cur_pos[PB1]
        target_position[PB2] = cur_pos[PB2]
        
        
        if (PB1_long_score > 0 and (PB1_long_score == PB1_limit or abs(target_position[PB1] - PB1_long_score) > PB1_buffer)):
            target_position[PB1] = round(PB1_long_score)
        if (PB1_short_score > 0 and (PB1_short_score == PB1_limit or abs(target_position[PB1] + PB1_short_score) > PB1_buffer)):
            target_position[PB1] = -round(PB1_short_score)
        if (PB1_long_score == 0 and PB1_short_score == 0):
            target_position[PB1] = 0
            
        if (PB2_long_score > 0 and (PB2_long_score == PB2_limit or abs(target_position[PB2] - PB2_long_score) > PB2_buffer)):
            target_position[PB2] = round(PB2_long_score)
        if (PB2_short_score > 0 and (PB2_short_score == PB2_limit or abs(target_position[PB2] + PB2_short_score) > PB2_buffer)):
            target_position[PB2] = -round(PB2_short_score)
        if (PB2_long_score == 0 and PB2_short_score == 0):
            target_position[PB2] = 0

        target_position[CST] = 6 * target_position[PB1] 
        target_position[JAM] = 3 * target_position[PB1]
        target_position[DJE] = target_position[PB1]
        
        for S in symbols_r2:
            if (S not in target_position):
                target_position[S] = cur_pos[S]

        
        exceed = False
        for S in symbols_r2:
            if (abs(target_position[S]) > position_limits[S]):
                exceed = True
                break
        exceed = False
        if (exceed):  # don't do any trade
            target_position = cur_pos
    
        # make buy or sell orders accordingly
        for S in symbols_r2:
            orders = []
            if S in {PB1, PB2}:
                sell_price = round(0.75*ask_prices[S] + 0.25*bid_prices[S])
                buy_price = round(0.75*bid_prices[S] + 0.25*ask_prices[S])
            else:
                sell_price = math.ceil(avg_prices[S])
                buy_price = math.floor(avg_prices[S])
            if (cur_pos[S] > target_position[S]):
                # just mid sell
                orders.append(Order(S, sell_price, target_position[S] - cur_pos[S]))
            if (cur_pos[S] < target_position[S]):
                # just mid buy
                orders.append(Order(S, buy_price, target_position[S] - cur_pos[S]))
            result[S] = orders

        print('cur_pos =', cur_pos)
        print('target_position =', target_position)
        print('PB1_long =', PB1_long_score)
        print('PB2_long =', PB2_long_score)
        
        traderData = ""
        conversions = 0
        return result, conversions, traderData