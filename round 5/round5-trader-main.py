from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List, Dict
import math
import numpy as np
import jsonpickle

SQI = 'SQUID_INK'
KLP = 'KELP'
RAR = 'RAINFOREST_RESIN'

CST = 'CROISSANTS'
JAM = 'JAMS'
DJE = 'DJEMBES'
PB1 = 'PICNIC_BASKET1'
PB2 = 'PICNIC_BASKET2'

VOR = 'VOLCANIC_ROCK'
VOR_C9500 = 'VOLCANIC_ROCK_VOUCHER_9500'
VOR_C9750 = 'VOLCANIC_ROCK_VOUCHER_9750'
VOR_C10000 = 'VOLCANIC_ROCK_VOUCHER_10000'
VOR_C10250 = 'VOLCANIC_ROCK_VOUCHER_10250'
VOR_C10500 = 'VOLCANIC_ROCK_VOUCHER_10500'

MAC = 'MAGNIFICENT_MACARONS'

BOBBY = 'Olivia'
SUCKER = 'Pablo'


class Trader:
    def __init__(self):
        
        self.symbols_r1 = {SQI, KLP, RAR}
        self.symbols_r2 = {CST, JAM, DJE, PB1, PB2}
        self.symbols_r3 = {VOR, VOR_C9500, VOR_C9750, VOR_C10000, VOR_C10250, VOR_C10500}
        self.coupons = self.symbols_r3 - {VOR}
        self.symbols_r4 = {MAC}

        self.symbols = self.symbols_r1.union(self.symbols_r2).union(self.symbols_r3).union(self.symbols_r4)

        self.conversion_limit = 10
        
        self.position_limits = {
            MAC: 75,
            VOR: 400, VOR_C9500: 200, VOR_C9750: 200,
            VOR_C10000: 200, VOR_C10250: 200, VOR_C10500: 200,
            CST: 250, JAM: 350, DJE: 60,
            PB1: 60, PB2: 100,
            SQI: 50, KLP: 50, RAR: 50
        }

        self.baskets_window = 10
        self.baskets_index_thresholds = {
            PB1: [10, 150],
            PB2: [10, 150]
        }
        self.baskets_score_buffer = {
            PB1: 3,
            PB2: 3
        }

        self.baskets_buy_margin = {
            PB1: 1.5,
            PB2: 1
    }
    
    def run(self, state: TradingState):
        result = {}
        if (state.traderData == ""):
            traderData = {}
        else:
            traderData = jsonpickle.decode(state.traderData)

        bobby_directions = traderData['bobby'] if ('bobby' in traderData) else {}
        hist_price = traderData['hist_price'] if ('hist_price' in traderData) else {}
        sucker_moves = traderData['sucker'] if ('sucker' in traderData) else set()
        
        if not hist_price:
            for S in self.symbols:
                hist_price[S] = []
                
        
        ####### price information ######
        market_bids, market_asks, bid_prices, ask_prices, avg_prices, cur_pos = self._gather_market_data(state, self.symbols)
        
        ####### trading for RAR and KLP ######
        for S in {RAR, KLP}:
            result[S] = self._market_make(S, cur_pos[S], bid_prices[S], ask_prices[S])
        
        ###### trading for SQI and CST ######
        bobby_directions = self._bobby_info(state, bobby_directions)

        for S in {SQI, CST}:
            # may want to experiment with the pricing
            if (S in bobby_directions):
                result[S] = self._bobby_trade(S, cur_pos[S], bid_prices[S], ask_prices[S], bobby_directions[S])
        
        ###### trading for PB1 and PB2 related ######
        ## TO DO: try to fix the baskets algorithm + experiment with MM strategies given the spread

        sucker_order, sucker_moves = self._sucker_trade(state, bid_prices, ask_prices, cur_pos, sucker_moves)

        for S in {PB1, PB2}:
            if (S in sucker_order):
                result[S] = sucker_order[S]
        '''
        indices, target_pos_baskets = self._baskets_info(avg_prices, cur_pos)  # calculate the index thingy
        for S in {PB1, PB2}:
            if (S not in sucker_moves):
                result[S] = self._baskets_trade(S, cur_pos[S], target_pos_baskets[S], \
                                                bid_prices[S], ask_prices[S])
            if (len(hist_price[S]) == self.baskets_window):
                hist_price[S] = hist_price[S][1:]
            hist_price[S].append(indices[S])
        '''
        
        ###### trading for options related ######
        '''
        for coupon in self.coupons:
            result[coupon] = [Order(coupon, 0, self.position_limits[coupon] - cur_pos[coupon])]
            if (cur_pos[coupon] > 0):
                result[coupon].append(Order(coupon, market_asks[coupon], -self.position_limits[coupon] - cur_pos[coupon]))
        '''
        
        traderData = jsonpickle.encode({'bobby': bobby_directions,\
                                        'hist_price': hist_price,\
                                       'sucker': sucker_moves})
        
        conversions = -cur_pos[MAC]
        if (conversions < -self.conversion_limit):
            conversions = -self.conversion_limit
        if (conversions > self.conversion_limit):
            conversions = self.conversion_limit
        
        return result, conversions, traderData


    ###### HELPER FUNCTIONS ######
    
    def _gather_market_data(self, state, symbols):
        bid_prices = {}
        ask_prices = {}
        avg_prices = {}
        cur_pos = {}
        market_bids = {}
        market_asks = {}
        
        for S in symbols:
            order_depth: OrderDepth = state.order_depths[S]
            cur_pos[S] = state.position.get(S, 0)

            total_bid, bid_qty = sum(p * v for p, v in order_depth.buy_orders.items()), sum(order_depth.buy_orders.values())
            total_ask, ask_qty = sum(p * -v for p, v in order_depth.sell_orders.items()), sum(-v for v in order_depth.sell_orders.values())

            avg_bid = total_bid / bid_qty if bid_qty else 0
            avg_ask = total_ask / ask_qty if ask_qty else 0
            hi_bid = max(order_depth.buy_orders.keys()) if bid_qty else 0
            lo_ask = min(order_depth.sell_orders.keys()) if ask_qty else 0

            if (bid_qty == 0):
                avg_bid, hi_bid = lo_ask, lo_ask
            if (ask_qty == 0):
                avg_ask, lo_ask = hi_bid, hi_bid
            market_bids[S] = hi_bid
            market_asks[S] = lo_ask
            bid_prices[S] = avg_bid
            ask_prices[S] = avg_ask
            avg_prices[S] = (avg_bid + avg_ask) / 2 if avg_bid and avg_ask else 0

        return market_bids, market_asks, bid_prices, ask_prices, avg_prices, cur_pos
    
    ################ LOGIC FOR TRADING STRATEGIES ################
    def _market_make(self, S, position, bid_price, ask_price):
        buy_price = math.floor(bid_price) + 1
        sell_price = math.ceil(ask_price) - 1
        buy_limit = self.position_limits[S] - position
        sell_limit = self.position_limits[S] + position
        return [Order(S, buy_price, buy_limit), Order(S, sell_price, -sell_limit)]

    def _bobby_info(self, state, bobby_directions):
        ret = bobby_directions
        for S in self.symbols:
            for trade in state.market_trades.get(S, []):
                price = trade.price
                if trade.buyer == BOBBY and trade.seller != BOBBY:
                    if (S in ret):
                        ret[S]['lo'] = price
                        ret[S]['dir'] = 1
                    else:
                        ret[S] = {'lo': price, 'hi': math.nan, 'dir': 1}
                elif trade.seller == BOBBY and trade.buyer != BOBBY:
                    if (S in ret):
                        ret[S]['hi'] = price
                        ret[S]['dir'] = -1
                    else:
                        ret[S] = {'lo': math.nan, 'hi': price, 'dir': -1}
        return ret
    
    def _bobby_trade(self, S, position, bid_price, ask_price, bobby_direction):
        my_bid = math.floor(bid_price) + 1
        my_ask = math.ceil(ask_price) - 1
        if (bobby_direction['dir'] == 1):
            # max buy
            return [Order(S, my_bid, self.position_limits[S] - position)]
        if (bobby_direction['dir'] == -1):
            # max sell
            return [Order(S, my_ask, -(self.position_limits[S] + position))]
        
    ################ LOGIC FOR TRADING STRATEGIES (MORE ADVANCED) ################
    
    def _score(self, x, lo, hi):
        return 0 if x < lo else 1 if x > hi else (x - lo) / (hi - lo)

    def _baskets_info(self, avg_prices, cur_pos):
        p = avg_prices
        target_pos = {}

        index_1 = p[CST] * 6 + p[JAM] * 3 + p[DJE] - p[PB1]
        index_2 = p[CST] * 4 + p[JAM] * 2 - p[PB2]
        
        for S, index in [(PB1, index_1), (PB2, index_2)]:
            lo, hi = self.baskets_index_thresholds[S]
            limit = self.position_limits[S]
            buffer = self.baskets_score_buffer[S]

            long_score = self._score(index, lo, hi) * limit
            short_score = self._score(-index, lo, hi) * limit

            
            target_pos[S] = cur_pos[S]
            if long_score > 0 and (long_score == limit or abs(cur_pos[S] - long_score) > buffer):
                target_pos[S] = round(long_score)
                
            if short_score > 0 and (short_score == limit or abs(cur_pos[S] + short_score) > buffer):
                target_pos[S] = -round(short_score)
            
            if long_score == 0 and short_score == 0:
                target_pos[S] = 0

        
        return {PB1: index_1, PB2: index_2}, target_pos

    def _baskets_trade(self, S, cur_pos, target_pos, bid_price, ask_price):
        orders = []
        margin = self.baskets_buy_margin
        my_ask = math.floor(ask_price - margin[S])
        my_bid = math.ceil(bid_price + margin[S])
        if cur_pos > target_pos:
            orders.append(Order(S, my_ask, target_pos - cur_pos))
        if cur_pos < target_pos:
            orders.append(Order(S, my_bid, target_pos - cur_pos))

        return orders
        
    ######### DEPRECATED ###########
    def _sucker_trade(self, state, bid_prices, ask_prices, cur_pos, sucker_moves):
        orders = {}
        ret = sucker_moves
        margin = self.baskets_buy_margin
        for S in {PB1, PB2}:
            # neutralize position for suckers
            if S in ret:
                if (cur_pos[S] == 0):
                    ret.remove(S)
                orders[S] = [Order(S, math.ceil(bid_prices[S]+margin[S]), -cur_pos[S])]
            # if sucker moves, we move
            for trade in state.market_trades.get(S, []):
                price = trade.price
                if trade.buyer == SUCKER and trade.seller != SUCKER:
                    ret.add(S)
                    orders[S] = [Order(S, math.floor(ask_prices[S]-margin[S]), -(self.position_limits[S] + cur_pos[S]))]
            
        return orders, ret