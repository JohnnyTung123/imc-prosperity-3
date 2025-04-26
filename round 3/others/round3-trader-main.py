from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import jsonpickle
import math
import numpy as np

############### PARAMETERS ##############
current_day = 3   # ******** TO DO: CHANGE TO DAY 3
window_size = 100
lo_signal_threshold = 0.1
hi_signal_threshold = 0.11

PB1_index_thresholds = [0, 100]
PB2_index_thresholds = [0, 100]
PB1_limit = 60
PB2_limit = 100
PB1_buffer = 3
PB2_buffer = 3


############### CONSTANTS ###############
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

coupons = [VOR_C9500, VOR_C9750, VOR_C10000, VOR_C10250, VOR_C10500]
strikes = {VOR_C9500: 9500, \
            VOR_C9750: 9750, \
            VOR_C10000: 10000, \
            VOR_C10250: 10250, \
            VOR_C10500: 10500}

symbols_r1 = {SQI, KLP, RAR}
symbols_r2 = {CST, JAM, DJE, PB1, PB2}
symbols_r3 = {VOR, VOR_C9500, VOR_C9750, VOR_C10000, VOR_C10250, VOR_C10500}
symbols = symbols_r1.union(symbols_r2).union(symbols_r3)

position_limits = {VOR: 400, VOR_C9500: 200, VOR_C9750: 200, VOR_C10000: 200, VOR_C10250: 200, VOR_C10500: 200, \
                   CST: 250, JAM: 350, DJE: 60, PB1: 60, PB2: 100, \
                   SQI: 50, KLP: 50, RAR: 50}

######## HELPER FUNCTIONS ###############
# z score to buy / sell signals
def f(z):
    if (abs(z) < lo_signal_threshold):
        return 0
    elif (abs(z) > hi_signal_threshold):
        return 1 if z > 0 else -1
    else:
        mag = (abs(z) - lo_signal_threshold) / (hi_signal_threshold - lo_signal_threshold)
        return mag if z > 0 else -mag

def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def bsm_call_price(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    # Manually computed CDF values using norm_cdf
    N_d1 = norm_cdf(d1)
    N_d2 = norm_cdf(d2)
    
    return S * N_d1 - K * np.exp(-r * T) * N_d2

def bsm_delta(S, K, T, r, sigma):
    if (sigma < 1e-6):
        return 0  # no hedging then!
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    N_d1 = norm_cdf(d1)

    return N_d1

def implied_volatility(S, K, T, r, C):
    left = 0.0
    right = 1e3
    num_iters = 50
    for _ in range(num_iters):
        mid = (left + right) / 2
        if (bsm_call_price(S, K, T, r, mid) > C):
            right = mid
        else:
            left = mid
    return left



############ MAIN CLASS #############
class Trader:
    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
       # print("Observations: " + str(state.observations))
        
        ############# HISTORY ##############
        history = {}
        if (state.traderData == ""):
            traderData = {}
            for product in symbols_r3:
                history[product] = []
        else:
            traderData = jsonpickle.decode(state.traderData)
            for product in symbols_r3:
                history[product] = traderData[product]

        
        ########### DATA #################
        
        current_timestamp = state.timestamp
        def time_to_T(day, timestamp):
            return (8000000 - 1000000*day - timestamp) / 1000000
        T = time_to_T(current_day, current_timestamp)

        
        result = {}
        orders: List[Order] = []

        ########## USEFUL VALUES ###########
        bid_prices = {}
        ask_prices = {}
        highest_bids = {}
        lowest_asks = {}
        cur_pos = {}
        avg_prices = {}
        max_buy = {}
        max_sell = {}
        
        for S in symbols:
            # get current position
            cur_pos[S] = 0
            if (S in state.position):
                cur_pos[S] = state.position[S]
            max_buy[S] = position_limits[S] - cur_pos[S]
            max_sell[S] = position_limits[S] + cur_pos[S]
            
            order_depth_S: OrderDepth = state.order_depths[S]
            
            total_bid_volume = 0
            total_bid_prices = 0

            total_ask_volume = 0
            total_ask_prices = 0
            
            for bid_price, bid_volume in order_depth_S.buy_orders.items():
                total_bid_volume += bid_volume
                total_bid_prices += bid_price * bid_volume
            avg_bid_price = total_bid_prices / total_bid_volume if total_bid_volume > 0 else math.nan
            
            for ask_price, ask_volume in order_depth_S.sell_orders.items():
                total_ask_volume += (-ask_volume)
                total_ask_prices += ask_price * (-ask_volume)
            avg_ask_price = total_ask_prices / total_ask_volume if total_ask_volume > 0 else math.nan

            highest_bids[S] = max(order_depth_S.buy_orders) if total_bid_volume > 0 else math.nan
            lowest_asks[S] = min(order_depth_S.sell_orders) if total_ask_volume > 0 else math.nan

            # basically only happens for options
            if (total_bid_volume == 0):
                avg_bid_price = avg_ask_price - 1
                highest_bids[S] = lowest_asks[S] - 1
            if (total_ask_volume == 0):
                avg_ask_price = avg_bid_price + 1
                lowest_asks[S] = highest_bids[S] + 1

            bid_prices[S] = avg_bid_price
            ask_prices[S] = avg_ask_price
            avg_prices[S] = (avg_bid_price + avg_ask_price) / 2

        
        target_position = {}


        
        ###### LOGIC FOR ROUND 3 PRODUCTS ######
        for product in symbols_r3:
            target_position[product] = 0

        # compare current IV with past IV, check z score
        IV = {}
        delta = {}
        z_score = {}
        for product in coupons:
            IV[product] = implied_volatility(S=avg_prices[VOR], K=strikes[product], T=T, r=0, C=avg_prices[product])
            delta[product] = bsm_delta(S=avg_prices[VOR], K=strikes[product], T=T, r=0, sigma=IV[product])
            hist_length = len(history[product])
            if (hist_length < window_size):
                z = 0
            else:
                hist_mean = np.mean(history[product])
                hist_stdev = np.std(history[product])
                z = (IV[product] - hist_mean) / hist_stdev
            target_position[product] = round(-f(z) * position_limits[product])
            z_score[product] = z

        # delta hedge using the volcanic rocks
        for product in coupons:
            target_position[VOR] -= cur_pos[product] * delta[product]
        target_position[VOR] = round(target_position[VOR])
        if (target_position[VOR] > position_limits[VOR]):
            target_position[VOR] = position_limits[VOR]
        elif (target_position[VOR] < -position_limits[VOR]):
            target_position[VOR] = -position_limits[VOR]
        
        for product in symbols_r3:
            target_buy_price = round(avg_prices[product])
            target_sell_price = round(avg_prices[product])
            if (product == VOR): # different spread, so.....
                target_buy_price = math.floor(bid_prices[product]) + 1
                target_sell_price = math.ceil(ask_prices[product]) - 1
            if (target_position[product] > cur_pos[product]):
                result[product] = [Order(product, target_buy_price, target_position[product] - cur_pos[product])]
            if (target_position[product] < cur_pos[product]):
                result[product] = [Order(product, target_sell_price, target_position[product] - cur_pos[product])]


        
        ###### LOGIC FOR ROUND 2 PRODUCTS ######
        
        for S in symbols_r2:
            target_position[S] = 0

        
        def scoring(x, lo, hi):
           if (x < lo):
               return 0
           elif (x > hi):
               return 1
           else:
               return (x - lo) / (hi - lo)

        # compute directions for each product
        PB1_long_index = avg_prices[CST] * 6 + avg_prices[JAM] * 3 + avg_prices[DJE] - avg_prices[PB1]
        PB2_long_index = avg_prices[CST] * 4 + avg_prices[JAM] * 2 - avg_prices[PB2]
        PB1_long_score = scoring(PB1_long_index, PB1_index_thresholds[0], PB1_index_thresholds[1]) * PB1_limit
        PB1_short_score = scoring(-PB1_long_index, PB1_index_thresholds[0], PB1_index_thresholds[1]) * PB1_limit
        PB2_long_score = scoring(PB2_long_index, PB2_index_thresholds[0], PB2_index_thresholds[1]) * PB2_limit
        PB2_short_score = scoring(-PB2_long_index, PB1_index_thresholds[0], PB1_index_thresholds[1]) * PB2_limit
        
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

        
        # this is to magnify the position actually. so no need to do it really...
        # target_position[CST] = 6 * target_position[PB1] + 4 * target_position[PB2]
        # target_position[JAM] = 3 * target_position[PB1] + 2 * target_position[PB2]
        # target_position[DJE] = target_position[PB1]


        
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

        

        ###### LOGIC FOR ROUND 1 PRODUCTS ######
        for S in {RAR, KLP}:
            S_bid_price = math.floor(bid_prices[S]) + 1
            S_ask_price = math.ceil(ask_prices[S]) - 1
            result[S] = [Order(S, S_bid_price, max_buy[S]), Order(S, S_ask_price, -max_sell[S])]


        
        
        ###### SAVE HISTORICAL IV ######
        for product in coupons:
            if (len(history[product]) == window_size):
                history[product] = history[product][1:]
            history[product].append(IV[product])
        
        traderData = jsonpickle.encode(history)
        
        conversions = 0
        return result, conversions, traderData